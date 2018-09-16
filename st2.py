# coding:utf-8

import logging
import threading

from errbot import BotPlugin, re_botcmd, botcmd, arg_botcmd, webhook
from lib.st2pluginapi import St2PluginAPI
from lib.st2adapters import ChatAdapterFactory
from lib.st2outofbandsauth import AuthenticationController

LOG = logging.getLogger(__name__)

# A plugin prefix for stackstorm action aliases to avoid name collisions between
# them and native errbot plugins.  Defined here so it's available to errbot's facade decorator.
PLUGIN_PREFIX = r"st2"


class St2Config(object):
    def __init__(self, bot_conf):
        self._configure_prefixes(bot_conf)
        self._configure_oobauth(bot_conf)
        self._configure_stackstorm(bot_conf)
        self.timer_update = bot_conf.STACKSTORM.get('timer_update', 60)
        self.verify_cert = bot_conf.STACKSTORM.get('verify_cert', True)

    def _configure_oobauth(self, bot_conf):
        rbac_auth = bot_conf.STACKSTORM.get('rbac_auth', {})
        if "proxied" in rbac_auth:
            self.rbac_auth_type = "proxied"
            self.rbac_auth_opts = rbac_auth["proxied"]
        if "extended" in rbac_auth:
            self.rbac_auth_type = "extended"
            self.rbac_auth_opts = rbac_auth["extended"]
        if rbac_auth == {}:
            self.rbac_auth_type = "simple"
            self.rbac_auth_opts = {}

    def _configure_prefixes(self, bot_conf):
        self.bot_prefix = bot_conf.BOT_PREFIX
        self.plugin_prefix = PLUGIN_PREFIX
        self.full_prefix = "{}{} ".format(bot_conf.BOT_PREFIX, self.plugin_prefix)

    def _configure_stackstorm(self, bot_conf):
        self.api_auth = bot_conf.STACKSTORM.get('api_auth', {})
        self.api_url = bot_conf.STACKSTORM.get('api_url', 'http://localhost:9101/v1')
        self.auth_url = bot_conf.STACKSTORM.get('auth_url', 'http://localhost:9100/v1')
        self.stream_url = bot_conf.STACKSTORM.get('stream_url', 'http://localhost:9102/v1')


class St2(BotPlugin):
    """
    StackStorm plugin for authentication and Action Alias execution.
    Try !st2help for action alias help.
    """
    def __init__(self, bot, name):
        super(St2, self).__init__(bot, name)

        self.st2config = St2Config(self.bot_config)
        self.st2api = St2PluginAPI(self.st2config)
        # The chat backend adapter mediates data format and api calls between
        # stackstorm, errbot and the chat backend.
        self.chatbackend = {
            "slack": ChatAdapterFactory.slack_adapter
        }.get(self._bot.mode, ChatAdapterFactory.generic_adapter)(self)

        self.oobauth = AuthenticationController(self)

        # Run the stream listener loop in a separate thread.
        if not self.st2api.validate_credentials():
            LOG.critical("Invalid credentials when communicating with StackStorm API.")

        th1 = threading.Thread(
            target=self.st2api.st2stream_listener,
            args=[self.chatbackend.post_message]
        )
        th1.setDaemon(True)
        th1.start()

    def activate(self):
        """
        Activate Errbot's poller to validate credentials periodically.  For user/password auth.
        """
        super(St2, self).activate()
        LOG.info("Poller activated")
        self.start_poller(self.st2config.timer_update, self.st2api.validate_credentials)

    @botcmd
    def st2sessionlist(self, msg, args):
        """
        List any established sessions between the chat service and StackStorm API.
        """
        return "Sessions: " + "\n".join(self.oobauth.list_sessions())

    @botcmd
    def st2sessiondelete(self, msg, args):
        """
        Delete an established session.
        """
        if len(args) > 0:
            self.oobauth.delete_session(args)

    @botcmd
    def st2authenticate(self, msg, args):
        """
        Usage: st2authenticate <secret>
        Establish a link between the chat backend and StackStorm by authenticating over an out of
        bands communication channel.
        """
        ret = ""

        if msg.is_direct:
            if len(args) > 0:
                ret = self.oobauth.request_session(msg.frm, args)
            else:
                ret = "Please provide a secret word to use during the authenication process."
        else:
            ret = "Requests for authentication in a public channel is nt possible." \
                  "  Request authentication in a private one-to-one message."
        return ret

    @re_botcmd(pattern='^{} .*'.format(PLUGIN_PREFIX))
    def st2_execute_actionalias(self, msg, match):
        """
        Run an arbitrary stackstorm command.
        Available commands can be listed using !st2help
        """
        def remove_bot_prefix(msg):
            """
            Drop plugin prefix and any trailing white space from user supplied st2 command.
            """
            return msg.replace(self.st2config.plugin_prefix, "", 1).strip()

        msg.body = remove_bot_prefix(match.group())

        msg_debug = ""
        for attr, value in msg.__dict__.items():
            msg_debug += "\t\t{} [{}] {}\n".format(attr, type(value), value)
        LOG.debug("Message received from chat backend.\n{}\n".format(msg_debug))

        matched_result = self.st2api.match(msg.body)

        if matched_result is not None:
            action_alias, representation = matched_result
            del matched_result
            if action_alias.enabled is True:
                res = self.st2api.execute_actionalias(
                    action_alias,
                    representation,
                    msg,
                    self.chatbackend
                )
                LOG.debug('action alias execution result: type={} {}'.format(type(res), res))
                result = r"{}".format(res)
            else:
                result = "st2 command '{}' is disabled.".format(msg.body)
        else:
            result = "st2 command '{}' not found.  View available commands with {}st2help."
            result = result.format(msg.body, self.st2config.bot_prefix)
        return result

    @arg_botcmd("--pack", dest="pack", type=str)
    @arg_botcmd("--filter", dest="filter", type=str)
    @arg_botcmd("--limit", dest="limit", type=int)
    @arg_botcmd("--offset", dest="offset", type=int)
    def st2help(self, msg, pack=None, filter=None, limit=None, offset=None):
        """
        Provide help for StackStorm action aliases.
        """
        help_result = self.st2api.actionalias_help(pack, filter, limit, offset)
        if isinstance(help_result, list) and len(help_result) == 0:
            return "No help found for the search."
        else:
            return self.chatbackend.format_help(help_result)

    @webhook('/chatops/message')
    def chatops_message(self, request):
        """
        Webhook entry point for stackstorm to post messages into
        errbot which will relay them into the chat backend.
        """
        LOG.debug("Webhook request: {}".format(request))

        channel = request.get('channel')
        message = request.get('message')

        user = request.get('user')
        whisper = request.get('whisper')
        extra = request.get('extra', {})

        self.chatbackend.post_message(whisper, message, user, channel, extra)
        return "Delivered to chat backend."

    @webhook('/login/authenticate/<uuid>')
    def login_auth(self, request, uuid):
        m = ""
        LOG.debug("Request: {}".format(request))
        if self.oobauth.use_session_id(uuid):
            m = "Session created successfully."
        else:
            m = "Session has already been used or has expired."
        return "{} : {} {}".format(m, uuid, request)
