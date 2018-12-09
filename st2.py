# coding:utf-8
import json
import logging
import threading
from types import SimpleNamespace
from errbot import BotPlugin, re_botcmd, botcmd, arg_botcmd, webhook
from lib.config import PluginConfiguration
from lib.chat_adapters import ChatAdapterFactory
from lib.errors import SessionConsumedError, SessionExpiredError, SessionInvalidError
from lib.stackstorm_api import StackStormAPI
from lib.authentication_controller import AuthenticationController, BotPluginIdentity
from lib.authentication_handler import St2ApiKey, St2UserToken, St2UserCredentials
from lib.authentication_handler import AuthHandlerFactory, ClientSideAuthHandler

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

        # Initialised shared configuraiton with the bot's stackstorm settings.
        self.cfg = PluginConfiguration()
        self.cfg.setup(self.bot_config, PLUGIN_PREFIX)

        # The chat backend adapter mediates data format and api calls between
        # stackstorm, errbot and the chat backend.
        self.chatbackend = ChatAdapterFactory.instance(self._bot.mode)(self)
        self.accessctl = AuthenticationController(self)
        self.st2api = StackStormAPI(self.cfg, self.accessctl)

        self.authenticate_bot_credentials()

    def authenticate_bot_credentials(self):
        """
        Create a session and associate valid StackStorm credentials with it for the bot to use.
        """
        # Wrap err-stackstorm credentials to distinguish it from chat backend credentials.
        self.internal_identity = BotPluginIdentity()

        # Create a session for internal use by err-stackstorm
        bot_session = self.accessctl.create_session(
            self.internal_identity,
            self.internal_identity.secret
        )
        LOG.debug("err-stackstorm requested session {}".format(bot_session))

        standalone_auth = AuthHandlerFactory.instantiate("standalone")(self.cfg)
        bot_token = standalone_auth.authenticate(st2_creds=self.cfg.bot_creds)
        LOG.debug("StackStorm authentication response {}".format(bot_token.requests()))
        if bot_token:
            self.accessctl.set_token_by_session(bot_session.id(), bot_token)
        else:
            LOG.critical("Failed to authenticate bot credentials with StackStorm API.")

    def reauthenticate_bot_credentials(self, bot_session):
        self.accessctl.delete_session(bot_session.id())
        self.accessctl.authenticate_bot_credentials()

    def validate_bot_credentials(self):
        """
        Check the session and StackStorm credentials are still valid.
        """
        try:
            bot_session = self.accessctl.get_session(self.internal_identity)
            bot_session.is_expired()
        except SessionExpiredError:
            LOG.debug("err-stackstorm session expired, attempting to renew")
            self.reauthenticate_bot_credentials(bot_session)

        # Fetch the stackstorm token and check it's validity.  If it's invalid, renew it.
        bot_token = self.accessctl.get_token_by_session(bot_session.id())
        if self.st2api.check_st2_token(bot_token) is False:
            self.reauthenticate_bot_credentials()

    def st2listener(self):
        """
        Start a new thread to listen to StackStorm's stream events.
        """
        # Run the stream listener loop in a separate thread.
        st2events_listener = threading.Thread(
            target=self.st2api.st2stream_listener,
            args=[self.chatbackend.post_message, self.internal_identity]
        )
        st2events_listener.setDaemon(True)
        st2events_listener.start()

    def activate(self):
        """
        Activate Errbot's poller to periodically validate st2 credentials.
        """
        super(St2, self).activate()
        LOG.info("Poller activated")
        self.start_poller(self.cfg.timer_update, self.validate_bot_credentials)
        self.st2listener()

    @botcmd(admin_only=True)
    def st2sessionlist(self, msg, args):
        """
        List any established sessions between the chat service and StackStorm API.
        """
        return "Sessions: " + "\n".join(self.accessctl.list_sessions())

    @botcmd(admin_only=True)
    def st2sessiondelete(self, msg, args):
        """
        Delete an established session.
        """
        if len(args) > 0:
            self.accessctl.delete_session(args)

    @botcmd
    def st2authenticate(self, msg, args):
        """
        Usage: st2authenticate <secret>
        Establish a link between the chat backend and StackStorm by authenticating over an out of
        bands communication channel.
        """
        ret = ""
        if isinstance(self.cfg.auth_handler, ClientSideAuthHandler):
            if msg.is_direct:
                if len(args) > 0:
                    session = self.accessctl.create_session(msg.frm, args)
                    ret = "Your challenge response is {}".format(
                        self.accessctl.session_url(session.id(), "/index.html")
                    )
                else:
                    ret = "Please provide a shared word to use during the authenication process."
            else:
                ret = "Requests for authentication in a public channel isn't possible." \
                      "  Request authentication in a private one-to-one message."
        else:
            ret = "Authentication is only available when Client side authentication is configured."
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
            return msg.replace(self.cfg.plugin_prefix, "", 1).strip()

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
            result = result.format(msg.body, self.cfg.bot_prefix)
        return result

    @arg_botcmd("--pack", dest="pack", type=str)
    @arg_botcmd("--filter", dest="filter", type=str)
    @arg_botcmd("--limit", dest="limit", type=int)
    @arg_botcmd("--offset", dest="offset", type=int)
    def st2help(self, msg, pack=None, filter=None, limit=None, offset=None):
        """
        Provide help for StackStorm action aliases.
        """
        bot_session = self.accessctl.get_session(self.internal_identity)
        st2_creds = self.accessctl.get_token_by_session(bot_session.id())
        help_result = self.st2api.actionalias_help(pack, filter, limit, offset, st2_creds)
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

        try:
            self.accessctl.consume_session(uuid)
        except (SessionConsumedError, SessionExpiredError, SessionInvalidError) as e:
            r.return_code = 2
            r.message = "Session '{}' {}.".format(uuid, e)
        except Exception as e:
            r.return_code = 90
            r.message = "An unexpected error has occurred."

        if r.return_code == 0:
            try:
                shared_word = request.get("shared_word", None)
                if self.accessctl.match_secret(uuid, shared_word) is False:
                    r.return_code = 5
                    r.message = "Invalid credentials"
            except Exception as e:
                r.return_code = 91
            r.message = "An unexpected error has occurred. {}".format(e)

        if r.return_code == 0:
            # Get the user associated with the session id.
            user = self.accessctl.get_session_user(uuid)
            if "username" in request:
                username = request.get("username", "")
                password = request.get("password", "")
                self.accessctl.associate_credentials(
                    user,
                    St2UserCredentials(username, password),
                    self.cfg.bot_creds
                )
                r.authenticated = True
            elif "user_token" in request:
                user_token = request.get("user_token", None)
                self.accessctl.associate_credentials(
                    user,
                    St2UserToken(user_token),
                    self.cfg.bot_creds
                )
                r.authenticated = True
            elif "api_key" in request:
                api_key = request.get("api_key", None)
                self.accessctl.associate_credentials(
                    user,
                    St2ApiKey(api_key),
                    self.cfg.bot_creds
                )
                r.authenticated = True

            if r.authenticate is False or shared_word is None:
                r.return_code = 3
                r.message = "Invalid authentication payload."
                LOG.warning(r.message)

        return json.dumps(vars(r))
