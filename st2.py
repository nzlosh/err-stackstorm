# coding:utf-8

import logging
import threading

from errbot import BotPlugin, re_botcmd, botcmd, arg_botcmd, webhook
from st2pluginapi import St2PluginAPI

LOG = logging.getLogger(__name__)

# A plugin prefix for stackstorm action aliases is to avoid name collisions between
# them and native errbot plugins.  Defined here so it's available to errbot's facade decorator.
PLUGIN_PREFIX = r"st2"


class St2Config(object):
    def __init__(self, bot_conf):
        self.plugin_prefix = PLUGIN_PREFIX
        self.bot_prefix = bot_conf.BOT_PREFIX
        self.full_prefix = "{}{} ".format(bot_conf.BOT_PREFIX, PLUGIN_PREFIX)
        self.api_auth = bot_conf.STACKSTORM.get('api_auth', {})
        self.base_url = bot_conf.STACKSTORM.get('base_url', 'http://localhost')
        self.api_url = bot_conf.STACKSTORM.get('api_url', 'http://localhost:9100/api/v1')
        self.auth_url = bot_conf.STACKSTORM.get('auth_url', 'http://localhost:9100')
        self.stream_url = bot_conf.STACKSTORM.get('stream_url', 'http://localhost:9102/v1/stream')
        self.api_version = bot_conf.STACKSTORM.get('api_version', 'v1')
        self.timer_update = bot_conf.STACKSTORM.get('timer_update', 60)
        self.verify_cert = bot_conf.STACKSTORM.get('verify_cert', True)


class St2(BotPlugin):
    """
    Stackstorm plugin for authentication and Action Alias execution.
    Try !st2help for action alias help.
    """
    def __init__(self, bot, name):
        super(St2, self).__init__(bot, name)

        self.st2config = St2Config(self.bot_config)
        self.st2api = St2PluginAPI(self.st2config)

        # Run the stream listener loop in a separate thread.
        self.st2api.validate_credentials()
        th1 = threading.Thread(target=self.st2api.st2stream_listener, args=[self.post_message])
        th1.setDaemon(True)
        th1.start()

    def activate(self):
        """
        Activate Errbot's poller to validate credentials periodically.  For user/password auth.
        """
        super(St2, self).activate()
        LOG.info("Poller activated")
        self.start_poller(self.st2config.timer_update, self.st2api.validate_credentials)

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
                res = self.st2api.execute_actionalias(action_alias, representation, msg)
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
        return self.st2api.show_help(pack, filter, limit, offset)

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

        self.post_message(whisper, message, user, channel, extra)
        return "Delivered to chat backend."

    def post_message(self, whisper, message, user, channel, extra):
        """
        Post messages to the chat backend.
        """
        LOG.debug("Posting Message: whisper={}, message={}, user={}, channel={}, extra={}".format(
            whisper,
            message,
            user,
            channel,
            extra)
        )
        user_id = None
        channel_id = None

        if user is not None:
            try:
                user_id = self.build_identifier(user)
            except ValueError as err:
                LOG.warning("Invalid user identifier '{}'.  {}".format(channel, err))

        if channel is not None:
            try:
                channel_id = self.build_identifier(channel)
            except ValueError as err:
                LOG.warning("Invalid channel identifier '{}'.  {}".format(channel, err))

        # Only whisper to users, not channels.
        if whisper and user_id is not None:
            target_id = user_id
        else:
            if channel_id is None:
                # Fall back to user if no channel is set.
                target_id = user_id
            else:
                target_id = channel_id

        if target_id is None:
            LOG.error("Unable to post message as there is no user or channel destination.")
        else:
            if extra is {}:
                self.send(target_id, message)
            else:
                LOG.debug("Send card using backend {}".format(self.mode))
                backend = extra.get(self.mode, {})
                LOG.debug("fields {}".format(
                    tuple(
                        [(field.get("title"), field.get("value")) for field in backend.get("fields", [])]
                    )))
                if backend is not {}:
                    kwargs = {
                        "body": message,
                        "to": target_id,
                        "summary": backend.get("pretext"),
                        "title": backend.get("title"),
                        "link": backend.get("title_link"),
                        "image": backend.get("image_url"),
                        "thumbnail": backend.get("thumb_url"),
                        "color": backend.get("color"),
                        "fields":  tuple([(field.get("title"), field.get("value")) for field in backend.get("fields", [])])
                    }
                    LOG.debug("Type: {}, Args: {}".format(type(kwargs), kwargs))
                    self.send_card(**kwargs)
                else:
                    LOG.warning("{} not found.".format(self.mode))
                    self.send(target_id, message)
