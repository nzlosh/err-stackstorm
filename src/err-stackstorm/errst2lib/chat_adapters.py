# coding:utf-8
import abc
import logging

from errbot.backends.base import (
    Person,
    Room,
)

LOG = logging.getLogger("errbot.plugin.st2.chat_adapters")


class AbstractChatAdapterFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def slack_adapter(self, bot_plugin):
        pass

    @abc.abstractmethod
    def mattermost_adapter(self, bot_plugin):
        pass

    @abc.abstractmethod
    def xmpp_adapter(self, bot_plugin):
        pass

    @abc.abstractmethod
    def generic_adpater(self, bot_plugin):
        pass


class ChatAdapterFactory(AbstractChatAdapterFactory):
    @staticmethod
    def instance(chat_backend):
        return {
            "slack": ChatAdapterFactory.slack_adapter,
            "slackv3": ChatAdapterFactory.slackv3_adapter,
            "mattermost": ChatAdapterFactory.mattermost_adapter,
            "xmpp": ChatAdapterFactory.xmpp_adapter,
            "irc": ChatAdapterFactory.irc_adapter,
            "discord": ChatAdapterFactory.discord_adapter,
        }.get(chat_backend, ChatAdapterFactory.generic_adapter)

    @staticmethod
    def discord_adapter(bot_plugin):
        return DiscordChatAdapter(bot_plugin)

    @staticmethod
    def slack_adapter(bot_plugin):
        return SlackChatAdapter(bot_plugin)

    @staticmethod
    def slackv3_adapter(bot_plugin):
        return SlackChatV3Adapter(bot_plugin)

    @staticmethod
    def irc_adapter(bot_plugin):
        return IRCChatAdapter(bot_plugin)

    @staticmethod
    def mattermost_adapter(bot_plugin):
        return MattermostChatAdapter(bot_plugin)

    @staticmethod
    def xmpp_adapter(bot_plugin):
        return XMPPChatAdapter(bot_plugin)

    @staticmethod
    def generic_adapter(bot_plugin):
        return GenericChatAdapter(bot_plugin)


class AbstractChatAdapter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_username(self, msg):
        pass

    @abc.abstractmethod
    def post_message(self, whisper, message, user, channel, extra):
        pass

    @abc.abstractmethod
    def format_help(self, help_strings):
        pass

    @abc.abstractmethod
    def normalise_user_id(self, user):
        pass

    @abc.abstractmethod
    def present_sessions(self, sessions):
        pass


class GenericChatAdapter(AbstractChatAdapter):
    def __init__(self, bot_plugin):
        self.bot_plugin = bot_plugin

    def get_username(self, msg):
        """
        Return the user name from an errbot message object.
        """
        return str(msg.frm)

    def format_help(self, help_strings):
        help_text = ""
        pack = ""
        for help_obj in help_strings:
            if pack != help_obj["pack"]:
                help_text += "[{}]\n".format(help_obj["pack"])
                pack = help_obj["pack"]
            help_text += "\t{}{}{} - {}\n".format(
                self.bot_plugin.cfg.bot_prefix,
                self.bot_plugin.cfg.command_prefix,
                help_obj["display"],
                help_obj["description"],
            )
        return help_text

    def post_message(self, whisper, message, user, channel, extra):
        """
        Post messages to the chat backend.
        """
        LOG.debug(
            "GenericChatAdapter posting message: whisper={},"
            " message={}, user={}, channel={}, extra={}".format(
                whisper, message, user, channel, extra
            )
        )
        user_id = None
        channel_id = None

        if user is not None:
            try:
                user_id = self.bot_plugin.build_identifier(user)
                LOG.debug("UserID: {}".format(user_id))
            except ValueError as err:
                LOG.warning("Invalid user identifier '{}'.  {}".format(channel, err))

        if channel is not None:
            try:
                LOG.debug("Channel {}".format(channel))
                channel_id = self.bot_plugin.build_identifier(channel)
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
            self.bot_plugin.send(target_id, message)

    def normalise_user_id(self, user):
        return "Generic normalise {}".format(
            [user.aclattr, user.client, user.fullname, user.nick, user.person]
        )

    def present_sessions(self, sessions):
        res = "Session:\n"
        for session in sessions:
            res += " - {}\n".format(str(session))
        return res


class DiscordChatAdapter(GenericChatAdapter):
    def __init__(self, bot_plugin):
        super().__init__(bot_plugin)

    def post_message(self, whisper, message, user, channel, extra):
        """
        Post messages to the chat backend.
        """
        LOG.debug(
            "GenericChatAdapter posting message: whisper={},"
            " message={}, user={}, channel={}, extra={}".format(
                whisper, message, user, channel, extra
            )
        )
        user_id = None
        channel_id = None

        if user is not None:
            try:
                user_id = self.bot_plugin.build_identifier(user)
            except ValueError as err:
                LOG.warning("Invalid user identifier '{}'.  {}".format(channel, err))

        if channel is not None:
            try:
                channel_id = self.bot_plugin.build_identifier(channel)
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
            self.bot_plugin.send(target_id, message)

    def normalise_user_id(self, user):
        return str(user.id)


class XMPPChatAdapter(GenericChatAdapter):
    def __init__(self, bot_plugin):
        self.bot_plugin = bot_plugin

    def normalise_user_id(self, user):
        return "{}@{}/{}".format(user.nick, user.domain, user.resource)


# Inheriting from Generic Chat Adapter until IRC backend specific methods are required.
class IRCChatAdapter(GenericChatAdapter):
    def __init__(self, bot_plugin):
        super().__init__(bot_plugin)

    def normalise_user_id(self, user):
        return "IRC normalise {}".format(
            [user.aclattr, user.client, user.fullname, user.host, user.nick, user.person, user.user]
        )


class MattermostChatAdapter(GenericChatAdapter):
    def __init__(self, bot_plugin):
        super().__init__(bot_plugin)

    def get_username(self, msg):
        LOG.debug("MattermostChatAdapter {} {}".format(type(msg.frm), msg.frm))
        username = None
        try:
            username = "~" + msg.frm.room
        except AttributeError:
            pass
        try:
            username = "@" + msg.frm.username
        except AttributeError:
            pass

        LOG.debug("MattermostChatAdapter username={}".format(username))
        return username

    def normalise_user_id(self, user):
        """
        Mattermost backend uses a unique id which is stored as the <client> attribute in Errbot's
        Identity object.
        """
        return user.client


class SlackChatAdapter(GenericChatAdapter):
    def __init__(self, bot_plugin):
        super().__init__(bot_plugin)

    def get_username(self, msg):
        """
        Return the user name from an errbot message object.
        Slack identity tuple (username, userid, channelname, channelid)
        """
        (
            username,
            user_id,
            channel_name,
            channel_id,
        ) = self.bot_plugin._bot.extract_identifiers_from_string(str(msg.frm))
        if username is None:
            name = "#{}".format(channel_name)
        else:
            name = "@{}".format(username)
        return name

    def post_message(self, whisper, message, user, channel, extra):
        """
        Post messages to the chat backend.

        https://api.slack.com/messaging/sending
        Sending messages in Slack can be
          - postMessage
          - postEphemeral
          - response_url (callback url to post reponses to a message interaction.)
          - (RTM doesn't support blocks or attachments)

        https://api.slack.com/messaging/composing
        Message Type:
          - plain-text (mrkdwn)
          - attachment
          - block

        """
        LOG.debug(
            "Slack posting message: whisper={}, message={},"
            " user={}, channel={}, extra={}".format(whisper, message, user, channel, extra)
        )
        user_id = None
        channel_id = None

        if user is not None:
            try:
                user_id = self.bot_plugin.build_identifier(user)
            except ValueError as err:
                LOG.warning("Invalid user identifier '{}'.  {}".format(channel, err))

        if channel is not None:
            try:
                channel_id = self.bot_plugin.build_identifier(channel)
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
            if extra and "slack" in extra:
                # https://api.slack.com/reference/messaging/attachments#legacy_fields
                legacy_fields = set(
                    [
                        "author_icon",
                        "author_link",
                        "author_name",
                        "color",
                        "fallback",
                        "fields",
                        "footer",
                        "footer_icon",
                        "image_url",
                        "mrkdwn_in",
                        "pretext",
                        "text",
                        "thumb_url",
                        "title",
                        "title_link",
                        "ts",
                    ]
                )
                if legacy_fields.issuperset(extra["slack"]):
                    self._post_legacy_attachment(whisper, message, target_id, extra["slack"])
                else:
                    self._post_block_message(whisper, message, target_id, extra["slack"])
            else:
                self.bot_plugin.send(target_id, message)

    def _post_legacy_attachment(self, whisper, message, target_id, extra):
        LOG.debug("Legacy attachment - Send card using backend {}".format(self.bot_plugin.mode))
        LOG.debug(
            "fields {}".format(
                tuple(
                    [(field.get("title"), field.get("value")) for field in extra.get("fields", [])]
                )
            )
        )
        if extra:
            kwargs = {
                "body": message,
                "to": target_id,
                "summary": extra.get("pretext"),
                "title": extra.get("title"),
                "link": extra.get("title_link"),
                "image": extra.get("image_url"),
                "thumbnail": extra.get("thumb_url"),
                "color": extra.get("color"),
                "fields": tuple(
                    [(field.get("title"), field.get("value")) for field in extra.get("fields", [])]
                ),
            }
            LOG.debug("Type: {}, Args: {}".format(type(kwargs), kwargs))
            self.bot_plugin.send_card(**kwargs)
        else:
            LOG.warning("extra.slack has no data, sending as plain message.")
            self.bot_plugin.send(target_id, message)

    def _post_block_message(self, whisper, message, target_id, extra):
        """
        Reference: https://api.slack.com/methods/chat.postMessage
        """
        extra["text"] = message
        if isinstance(target_id, Person):
            extra["user"] = target_id.userid
        elif isinstance(target_id, Room):
            extra["channel"] = target_id.id
        else:
            LOG.warning("target_id is type %s that isn't a Person or Room!", type(target_id))

        LOG.debug("Sending Slack Block %s", extra)
        self.bot_plugin._bot.slack_web.api_call("chat.postMessage", data=extra)

    def format_help(self, help_strings):
        help_text = ""
        pack = ""
        for help_obj in help_strings:
            if pack != help_obj["pack"]:
                help_text += "\n**{}**\n".format(help_obj["pack"])
                pack = help_obj["pack"]
            help_text += "\t{}{}{} - _{}_\n".format(
                self.bot_plugin.cfg.bot_prefix,
                self.bot_plugin.cfg.command_prefix,
                help_obj["display"],
                help_obj["description"],
            )
        return help_text

    def normalise_user_id(self, user):
        return str(user.userid)

    def present_sessions(self, sessions):
        res = "**Sessions**:\n"
        for session in sessions:
            LOG.debug("{}".format(session.attributes().get("UserID", "BAD!")))
            if session.attributes().get("UserID") == "errbot%service":
                res += "- {}\n".format(str(session))
            else:
                user = self.bot_plugin.build_identifier(
                    "@{}".format(session.attributes().get("UserID"))
                )
                res += "- {} {}\n".format(user.person, str(session))
        return res


class SlackChatV3Adapter(SlackChatAdapter):
    def __init__(self, bot_plugin):
        super().__init__(bot_plugin)

    def get_username(self, msg):
        """
        Return the user name from an errbot message object.
        Slack identity tuple (username, userid, channelname, channelid)
        """
        (
            username,
            user_id,
            channel_name,
            channel_id,
        ) = self.bot_plugin._bot.extract_identifiers_from_string(str(msg.frm))
        LOG.warning(
            f"""
            username = {username}
            user_id = {user_id}
            channel_name = {channel_name}
            channel_id = {channel_id}
        """
        )
        if channel_id:
            name = f"#{channel_id}"
        elif channel_name:
            name = f"#{channel_name}"
        elif user_id:
            name = f"<@{user_id}>"
        else:
            name = f"@{username}"
        return name
