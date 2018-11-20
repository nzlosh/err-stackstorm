# coding:utf-8
import json
import logging
import threading
from types import SimpleNamespace
from errbot import BotPlugin, re_botcmd, botcmd, arg_botcmd, webhook
from lib.config import PluginConfiguration
from lib.stackstorm_api import St2PluginAPI
from lib.chat_adapters import ChatAdapterFactory
from lib.authentication_controller import AuthenticationController, generate_password, BotPluginIdentity

LOG = logging.getLogger(__name__)

# TODO: FIXME: Set the PLUGIN_PREFIX based on configuration from errbot config.py.
# A plugin prefix for stackstorm action aliases to avoid name collisions between
# them and native errbot plugins.  Defined here so it's available to errbot's facade decorator.
PLUGIN_PREFIX = r"st2"


class St2(BotPlugin):
    """
    StackStorm plugin for authentication and Action Alias execution.
    Try !st2help for action alias help.
    """
    def __init__(self, bot, name):
        super(St2, self).__init__(bot, name)

        self.st2config = PluginConfiguration(self.bot_config, PLUGIN_PREFIX)
        self.st2api = St2PluginAPI(self.st2config)
        # The chat backend adapter mediates data format and api calls between
        # stackstorm, errbot and the chat backend.
        self.chatbackend = ChatAdapterFactory.instance(self._bot.mode)(self)
        self.access_control = AuthenticationController(self)

        # Wrap err-stackstorm credentials to distinguish it from chat backend credentials.
        self.internal_identity = BotPluginIdentity()
        self.bot_session = self.access_control.request_session(
            self.internal_identity,
            self.internal_identity.secret
        )
        self.log.debug("err-stackstorm requested session {}".format(self.bot_session))

        # Run the stream listener loop in a separate thread.
        if not self.st2api.validate_credentials():
            LOG.critical("Invalid credentials when communicating with StackStorm API.")

        st2events_listener = threading.Thread(
            target=self.st2api.st2stream_listener,
            args=[self.chatbackend.post_message]
        )
        st2events_listener.setDaemon(True)
        st2events_listener.start()

    def activate(self):
        """
        Activate Errbot's poller to validate credentials periodically.  For user/password auth.
        """
        super(St2, self).activate()
        LOG.info("Poller activated")
        self.start_poller(self.st2config.timer_update, self.st2api.validate_credentials)

    @botcmd(admin_only=True)
    def st2sessionlist(self, msg, args):
        """
        List any established sessions between the chat service and StackStorm API.
        """
        return "Sessions: " + "\n".join(self.access_control.list_sessions())

    @botcmd(admin_only=True)
    def st2sessiondelete(self, msg, args):
        """
        Delete an established session.
        """
        if len(args) > 0:
            self.access_control.delete_session(args)

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
                session = self.access_control.request_session(msg.frm, args)
                ret = "Your challenge response is {}".format(
                    self.access_control.session_url(session.id(), "/index.html")
                )
            else:
                ret = "Please provide a shared word to use during the authenication process."
        else:
            ret = "Requests for authentication in a public channel isn't possible." \
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
                LOG.debug("action alias execution result: type={} {}".format(type(res), res))
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
        LOG.debug("Request: {}".format(request))
        r = SimpleNamespace(**{
            "authenticated": False,
            "return_code": 0,
            "message": "Session has already been used or has expired."
        })

        if not self.access_control.use_session_id(uuid):
            r.return_code = 2
            r.message = "Invalid session id '{}'".format(uuid)

        if r.return_code == 0:
            shared_word = request.get("shared_word", None)
            if "username" in request:
                username = request.get("username", "")
                password = request.get("password", "")
                r.message = "Would have authenticated username/password"
                # validate user credentials against st2.
                r.authenticated = True
            elif "user_token" in request:
                user_token = request.get("user_token", None)
                r.message = "Would have authenticated user token."
                # validate user token against st2.
                r.authenticated = True
            elif "api_key" in request:
                api_key = request.get("api_key", None)
                r.message = "Would have authenticated api key."
                r.authenticated = True
                #validate api key against st2.
            else:
                r.return_code = 3
                r.message = "Invalid authentication payload."
                LOG.warning(r.message)

        return json.dumps(vars(r))
