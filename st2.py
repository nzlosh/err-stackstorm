# coding:utf-8

import logging
import threading

from errbot import BotPlugin, re_botcmd, botcmd, webhook
from st2pluginapi import St2PluginAPI

LOG = logging.getLogger(__name__)

# A plugin prefix for stackstorm action aliases is to avoid name collisions between
# them and native errbot plugins.  Defined here as a
PLUGIN_PREFIX = r"st2"


class St2Config(object):
    def __init__(self, bot_conf):
        self.plugin_prefix = PLUGIN_PREFIX
        self.bot_prefix = bot_conf.BOT_PREFIX
        self.full_prefix = "{}{} ".format(bot_conf.BOT_PREFIX, PLUGIN_PREFIX)
        self.api_auth = bot_conf.STACKSTORM.get('api_auth') or {}
        self.base_url = bot_conf.STACKSTORM.get('base_url') or 'http://localhost'
        self.api_url = bot_conf.STACKSTORM.get('api_url') or 'http://localhost:9100/api/v1'
        self.auth_url = bot_conf.STACKSTORM.get('auth_url') or 'http://localhost:9100'
        self.stream_url = bot_conf.STACKSTORM.get('stream_url') or 'http://localhost:9102/v1/stream'
        self.api_version = bot_conf.STACKSTORM.get('api_version') or 'v1'
        self.timer_update = bot_conf.STACKSTORM.get('timer_update') or 60


class St2(BotPlugin):
    """
    Stackstorm plugin for authentication and Action Alias execution.
    Try !st2help for action alias help.
    """
    def __init__(self, bot, name):
        super(St2, self).__init__(bot, name)

        self.st2config = St2Config(self.bot_config)
        self.st2api = St2PluginAPI(self.st2config)

        # Fetch available action-aliases
        self.st2api.generate_actionaliases()

        th1 = threading.Thread(target=self.st2api.st2stream_listener, args=[self.post_message])
        th1.setDaemon(True)
        th1.start()

    def activate(self):
        """
        Activate Errbot's poller to fetch Stackstorm action alias patterns and help.
        (deprecated with ActionAlias match API)
        """
        super(St2, self).activate()
        LOG.info("Poller activated")
        self.start_poller(self.st2config.timer_update, self.st2api.generate_actionaliases)

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

        LOG.info("""Message received from chat backend.
\t\tmsg.body [{}] {}
\t\tmsg.ctx [{}] {}
\t\tmsg.delayed [{}] {}
\t\tmsg.extras [{}] {}
\t\tmsg.flow [{}] {}
\t\tmsg.frm [{}] {}
\t\tmsg.is_direct [{}] {}
\t\tmsg.is_group [{}] {}
\t\tmsg.to [{}] {}""".format(type(msg.body), msg.body,
                             type(msg.ctx), msg.ctx,
                             type(msg.delayed), msg.delayed,
                             type(msg.extras), msg.extras,
                             type(msg.flow), msg.flow,
                             type(msg.frm), msg.frm,
                             type(msg.is_direct), msg.is_direct,
                             type(msg.is_group), msg.is_group,
                             type(msg.to), msg.to))

        matched_result = self.st2api.match(msg.body)

        if matched_result is not None:
            action_alias, representation = matched_result
            del matched_result
            if action_alias.enabled is True:
                res = self.st2api.execute_actionalias(action_alias, representation, msg)
                LOG.info('action alias execution result: type={} {}'.format(type(res), res))
                result = r"{}".format(res)
            else:
                result = "st2 command '{}' is disabled.".format(msg.body)
        else:
            result = "st2 command '{}' not found.  Check help with {}st2help"
            result = result.format(msg.body, self.st2config.bot_prefix)
        return result

    @botcmd
    def st2help(self, msg, args):
        """
        Provide help for stackstorm action aliases.
        """
        return self.st2api.show_help()

    @webhook('/chatops/message')
    def chatops_message(self, request):
        """
        Webhook entry point for stackstorm to post messages into
        errbot which will relay them into the chat backend.
        """
        LOG.debug("Webhook request:".format(request))

        channel = request.get('channel')
        message = request.get('message')

        user = request.get('user')
        whisper = request.get('whisper')
        extra = request.get('extra')

        self.post_message(whisper, message, user, channel, extra)
        return "Delivered to chat backend."

    def post_message(self, whisper, message, user, channel, extra):
        """
        Post messages to the chat backend.
        """
        LOG.info("whisper={}, message={}, user={}, channel={}, extra={}".format(whisper,
                                                                                message,
                                                                                user,
                                                                                channel,
                                                                                extra))
        if user is not None:
            user_id = self.build_identifier(user)

        if channel is not None:
            channel_id = self.build_identifier(channel)

        if whisper is True:
            self.send(user_id, message)
        else:
            self.send(channel_id, message)
