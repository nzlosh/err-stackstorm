# coding:utf-8
import json
import logging
import shlex
import threading
import traceback
from types import SimpleNamespace

import requests
from errbot import BotPlugin, Command, arg_botcmd, botcmd, re_botcmd, webhook

from errst2lib.authentication_controller import AuthenticationController, BotPluginIdentity
from errst2lib.authentication_handler import AuthHandlerFactory, ClientSideAuthHandler
from errst2lib.chat_adapters import ChatAdapterFactory
from errst2lib.config import PluginConfiguration
from errst2lib.credentials_adapters import St2ApiKey, St2UserCredentials, St2UserToken
from errst2lib.enquiry import Enquiry, EnquiryManager
from errst2lib.errors import (
    SessionConsumedError,
    SessionExistsError,
    SessionExpiredError,
    SessionInvalidError,
)
from errst2lib.stackstorm_api import StackStormAPI
from errst2lib.version import ERR_STACKSTORM_VERSION

LOG = logging.getLogger("errbot.plugin.st2")


class St2(BotPlugin):
    """
    StackStorm plugin for authentication and Action Alias execution.
    Try !st2help for action alias help.
    """

    def __init__(self, bot, name):
        super().__init__(bot, name)

        # Initialised shared configuraiton with the bot's stackstorm settings.
        try:
            self.cfg = PluginConfiguration()
            self.cfg.setup(self.bot_config)
        except Exception as err:
            LOG.critical(
                "Errors were encountered processing the STACKSTORM configuration."
                "Please correct the errors and restart the bot."
                "{}".format(err)
            )

        # The chat backend adapter mediates data format and api calls between
        # stackstorm, errbot and the chat backend.
        self.chatbackend = ChatAdapterFactory.instance(self._bot.mode)(self)

        self.accessctl = AuthenticationController(self)

        self.st2api = StackStormAPI(self.cfg, self.accessctl)

        self.responses = EnquiryManager()

        # Wrap err-stackstorm credentials to distinguish it from chat backend credentials.
        self.internal_identity = BotPluginIdentity()
        self.authenticate_bot_credentials()

        self.run_listener = True
        self.st2events_listener = None

    def authenticate_bot_credentials(self):
        """
        Create a session and associate valid StackStorm credentials with it for the bot to use.
        """

        # Create a session for internal use by err-stackstorm
        try:
            bot_session = self.accessctl.create_session(
                self.internal_identity, self.internal_identity.secret
            )
            self.accessctl.consume_session(bot_session.id())
        except SessionExistsError:
            LOG.warning("Internal logic error, bot session already exists.")
            bot_session = self.accessctl.get_session(self.internal_identity)
        LOG.debug("Bot session {}".format(bot_session))

        # Bot authentication is a corner case, it always requires the standalone model.
        standalone_auth = AuthHandlerFactory.instantiate("standalone")(self.cfg)
        bot_token = standalone_auth.authenticate(st2_creds=self.cfg.bot_creds)
        if bot_token:
            LOG.debug("StackStorm authentication succeeded.")
            self.accessctl.set_token_by_session(bot_session.id(), bot_token)
        else:
            LOG.critical("Failed to authenticate bot credentials with StackStorm API.")

    def reauthenticate_bot_credentials(self, bot_session):
        self.accessctl.delete_session(bot_session.id())
        self.authenticate_bot_credentials()

    def validate_bot_credentials(self):
        """
        Check the session and StackStorm credentials are still valid.
        """
        try:
            bot_session = self.accessctl.get_session(self.internal_identity)
            bot_session.is_expired()
        except SessionExpiredError as err:
            LOG.debug("{}".format(err))
            self.reauthenticate_bot_credentials(bot_session)
        except SessionInvalidError as err:
            LOG.debug("{}".format(err))
            self.authenticate_bot_credentials()

    def st2listener(self, start=False, stop=False):
        """
        Start a new thread to listen to StackStorm's stream events.
        """
        if start:
            self.run_listener = True
            self.st2events_listener.start()
            LOG.debug("st2stream listener thread starting.")
        if stop:
            self.run_listener = False
            LOG.debug("st2stream listener thread stopping.")

    def activate(self):
        """
        Activate Errbot's poller to periodically validate st2 credentials.
        """
        super().activate()
        LOG.info("Activate St2 plugin")

        self.dynamic_commands()

        self.start_poller(self.cfg.timer_update, self.validate_bot_credentials)
        self.st2events_listener = threading.Thread(
            target=self.st2api.st2stream_listener,
            name="st2stream_listener",
            args=[self.chatbackend.post_message, self.internal_identity],
        )
        self.st2listener(start=True)

    def deactivate(self):
        super().deactivate()
        self.stop_poller(self.validate_bot_credentials)
        self.destroy_dynamic_plugin("St2")
        self.st2listener(stop=True)
        LOG.info("st2stream listener wait for thread to exit.")
        self.st2events_listener.join()
        LOG.info("st2stream listener exited.")
        del self.st2events_listener

    def session_list(self, msg, args):
        """
        List any established sessions between the chat service and StackStorm API.
        """
        return self.chatbackend.present_sessions(self.accessctl.list_sessions())

    def session_delete(self, msg, args):
        """
        Delete an established session.
        """
        if len(args) > 0:
            self.accessctl.delete_session(args)

    def session_disconnect(self, msg, args):
        """
        Usage: session_disconnect
        Closes the session.  StackStorm credentials are purged when the session is closed.
        """
        # get user session
        # delete user session
        return "Not implemented yet."

    def enquiry_list(self, msg, args):
        """
        Usage: st2 <enquiry|inquiry> list
        """
        chat_user = msg.frm
        st2token, err_msg = self.get_token(chat_user)
        if st2token is False:
            rejection = (
                f"Error: '{err_msg}'.  Listing enquiries is not allowed for chat user "
                f"'{chat_user}'.  Please authenticate using {self.cfg.plugin_prefix}session_start "
                "or see your StackStorm administrator to grant access."
            )
            LOG.warning(rejection)
            return rejection

        res = self.st2api.enquiry_list(st2token).json()
        yield f"Enquries awaiting response: {len(res)}"
        for enquiry in res:
            yield enquiry["id"]

    def enquiry_set(self, msg, args):
        """
        Usage: st2 <enquiry|inquiry> set <enquiry_id>
        """
        self.responses.set(msg.frm.userid, args)
        return f"setting current enquiry to {args}"

    def enquiry_get(self, msg, args):
        """
        Usage: st2 <enquiry|inquiry> get <enquiry_id>
        """
        chat_user = msg.frm
        st2token, err_msg = self.get_token(chat_user)
        if st2token is False:
            rejection = (
                f"Error: '{err_msg}'.  Fetching enquiries is not allowed for chat user "
                f"'{chat_user}'.  Please authenticate using {self.cfg.plugin_prefix}session_start "
                "or see your StackStorm administrator to grant access."
            )
            LOG.warning(rejection)
            return rejection

        res = self.st2api.enquiry_get(args, st2token)
        if res:
            p = res["schema"]["properties"]
            return "Enquiry ID: {} (★ indicates required responses)\n{}".format(
                res["id"],
                "\n".join(
                    [
                        "Q{question}. {desc}{req} [{resp_type}]".format(
                            question=q[0] + 1,
                            desc=p[q[1]]["description"],
                            req="★" if p[q[1]]["required"] else "",
                            resp_type=p[q[1]]["type"],
                        )
                        for q in enumerate(p)
                    ]
                ),
            )
        else:
            return f"Error getting enquiry. {res}"

    def enquiry_reply(self, msg, args_str):
        """
        Usage: st2 <enquiry|inquiry> respond <enquiry_id> <question_idx> <answer>
        st2enquiry reply
        st2enquiry full reply '<json>'
        st2enquiry q1 reply <value>
        """
        args = shlex.split(args_str)

        user_id = msg.frm.userid
        enquiry_id = self.responses.get_current_enquiry(user_id)

        if len(args) == 0:
            yield "Respond to what?"
            return
        # TODO : Implement logic to use enquiry context to select next question.

        # ~ chat_user = msg.frm
        # ~ st2token, err_msg = self.get_token(chat_user)
        # ~ if st2token is False:
        # ~ rejection = (
        # ~ "Error: '{}'.  Responding to enquiries is not allowed for chat user '{}'."
        # ~ "  Please authenticate using {}session_start or see your StackStorm"
        # ~ " administrator to grant access.".format(err_msg, chat_user, self.cfg.plugin_prefix)
        # ~ )
        # ~ LOG.warning(rejection)
        # ~ yield rejection

        # ~ res = self.st2api.enquiry_get(args, st2token)
        # ~ self.responses.
        # ~ enquiry = Enquiry(res)

        # ~ yield f"{enquiry.response(1, 'a string')}"

    def session_authenticate(self, msg, args):
        """
        Usage: session_authenticate <secret>
        Establish a link between the chat backend and StackStorm by authenticating over an out of
        bands communication channel.
        """
        if isinstance(self.cfg.auth_handler, ClientSideAuthHandler) is False:
            return "Authentication is only available when Client side authentication is configured."

        if msg.is_direct is not True:
            return (
                "Requests for authentication in a public channel aren't supported for "
                "security reasons.  Request authentication in a private one-to-one message."
            )

        if len(args) < 1:
            return "Please provide a shared word to use during the authenication process."

        try:
            session = self.accessctl.create_session(msg.frm, args)
        except SessionExistsError:
            try:
                session = self.accessctl.get_session(msg.frm)
                if session.is_expired() is False:
                    return "A valid session already exists."
            except SessionExpiredError:
                self.accessctl.delete_session(session.id())
                session = self.accessctl.create_session(msg.frm, args)

        return "Your challenge response is {}".format(
            self.accessctl.session_url(session.id(), "index.html")
        )

    def get_token(self, chat_user):
        """
        Given a chat user, lookup the st2 token.

        Returns tuple of st2token and error message.
                Error message is only useful when st2token is false.
        """
        st2token = False
        err_msg = "Failed to fetch valid credentials."
        try:
            st2token = self.accessctl.pre_execution_authentication(chat_user)
        except (SessionExpiredError, SessionInvalidError) as err:
            err_msg = str(err)
        return (st2token, err_msg)

    def execute_actionalias(self, msg, match):
        """
        Run an arbitrary stackstorm command.
        Available commands can be listed using !st2help
        """

        def remove_bot_prefix(msg):
            """
            Drop plugin prefix and any trailing white space from user supplied st2 command.
            """
            return msg.removeprefix(self.cfg.plugin_prefix).strip()

        chat_user = msg.frm
        st2token, err_msg = self.get_token(chat_user)
        if st2token is False:
            rejection = (
                "Error: '{}'.  Action-Alias execution is not allowed for chat user '{}'."
                "  Please authenticate using {}session_start or see your StackStorm"
                " administrator to grant access.".format(err_msg, chat_user, self.cfg.plugin_prefix)
            )
            LOG.warning(rejection)
            return rejection

        msg.body = remove_bot_prefix(match.group())

        msg_debug = ""
        for attr, value in msg.__dict__.items():
            msg_debug += "\t\t{} [{}] {}\n".format(attr, type(value), value)
        LOG.debug(f"Message received from chat backend.\n{msg_debug}\n")

        matched_result = self.st2api.match(msg.body, st2token)

        if matched_result.return_code != 0:
            # The action-alias wasn't found or an error was encounter and is reported.
            return matched_result.message

        action_alias = matched_result.message["actionalias"]
        del matched_result

        if action_alias.get("enabled", True) is False:
            return "The command '{}' is disabled.".format(msg.body)

        actionalias_exec_result = self.st2api.execute_actionalias(
            msg, self.chatbackend.get_username(msg), st2token
        )

        LOG.debug(
            f"action alias execution result: "
            "type={type(actionalias_exec_result)} {actionalias_exec_result}"
        )

        if not isinstance(actionalias_exec_result, dict):
            # The StackStorm API hasn't responded with a json parsable body or with the
            # expected 201/400 return code.  The http response text is reported.
            return actionalias_exec_result

        result = actionalias_exec_result.get("faultstring")
        # If the response doesn't contain "faultstring", it's assumed the execution
        # submission was successful and command acknowledgement must be processed.
        if result is None:
            ack_action_alias = action_alias.get("ack", {"enabled": False})
            if ack_action_alias.get("enabled", True) is True:
                result = actionalias_exec_result.get("results", [{}])[0]
                if result.get("actionalias", {}).get("ack", {}).get("append_url", False):
                    web_url = f' {result.get("execution", {}).get("web_url", "")}'
                else:
                    web_url = ""
                result = f'{result.get("message", "")}{web_url}'

        return result

    def st2help(self, msg, pack=None, filter=None, limit=None, offset=None):
        """
        Provide help for StackStorm action aliases.
        """
        # If the bot session is invalid, attempt to renew it.
        try:
            bot_session = self.accessctl.get_session(self.internal_identity)
        except SessionInvalidError:
            self.authenticate_bot_credentials()
            bot_session = self.accessctl.get_session(self.internal_identity)

        st2_creds = self.accessctl.get_token_by_session(bot_session.id())
        help_result = self.st2api.actionalias_help(pack, filter, limit, offset, st2_creds)
        if isinstance(help_result, list) and len(help_result) == 0:
            return "No help found for the search."
        else:
            return self.chatbackend.format_help(help_result)

    @webhook("/chatops/message")
    def chatops_message(self, request):
        """
        Webhook entry point for stackstorm to post messages into
        errbot which will relay them into the chat backend.
        """
        # WARNING: Sensitive security information will be logged, uncomment only when necessary.
        # LOG.debug("Webhook request: {}".format(request))

        channel = request.get("channel")
        message = request.get("message")

        user = request.get("user")
        whisper = request.get("whisper")
        extra = request.get("extra", {})

        self.chatbackend.post_message(whisper, message, user, channel, extra)
        return "Delivered to chat backend."

    @webhook("/login/authenticate/<uuid>")
    def login_auth(self, request, uuid):
        # WARNING: Sensitive security information will be logged, uncomment only when necessary.
        # LOG.debug("Request: {}".format(request))
        r = SimpleNamespace(
            **{
                "authenticated": False,
                "return_code": 0,
                "message": "Successfully associated StackStorm credentials",
            }
        )

        try:
            self.accessctl.consume_session(uuid)
        except (SessionConsumedError, SessionExpiredError, SessionInvalidError) as err:
            r.return_code = 2
            r.message = "Session '{}' {}".format(uuid, str(err))
        except Exception as err:
            r.return_code = 90
            r.message = "Session unexpected error: {}".format(str(err))

        if r.return_code == 0:
            try:
                shared_word = request.get("shared_word", None)
                if self.accessctl.match_secret(uuid, shared_word) is False:
                    r.return_code = 5
                    r.message = "Invalid credentials"
            except Exception as err:
                r.return_code = 91
                r.message = "Credentials unexpected error: {}".format(str(err))

        if r.return_code == 0:
            # Get the user associated with the session id.
            user = self.accessctl.get_session_userid(uuid)
            LOG.debug("Matched chat user {} for credential association".format(user))
            if "username" in request:
                username = request.get("username", "")
                password = request.get("password", "")
                if self.accessctl.associate_credentials(
                    user, St2UserCredentials(username, password), self.cfg.bot_creds
                ):
                    r.authenticated = True
                else:
                    r.message = "Invalid credentials"
                    r.return_code = 6
            elif "user_token" in request:
                user_token = request.get("user_token", None)
                if self.accessctl.associate_credentials(
                    user, St2UserToken(user_token), self.cfg.bot_creds
                ):
                    r.authenticated = True
                else:
                    r.message = "Invalid token"
                    r.return_code = 6
            elif "api_key" in request:
                api_key = request.get("api_key", None)
                if self.accessctl.associate_credentials(
                    user, St2ApiKey(api_key), self.cfg.bot_creds
                ):
                    r.authenticated = True
                else:
                    r.message = "Invalid api key"
                    r.return_code = 6

            if (r.authenticated is False or shared_word is None) and r.return_code == 0:
                r.return_code = 3
                r.message = "Invalid authentication payload"

        if r.authenticated is False:
            try:
                self.accessctl.delete_session(uuid)
            except Exception as e:
                LOG.debug("Failed to delete {}. {}".format(uuid, e))
                if LOG.level <= logging.DEBUG:
                    traceback.print_exc()
            LOG.warning(r.message)

        return json.dumps(vars(r))

    def dynamic_commands(self):
        """
        Register commands.
        """

        def st2help(plugin, msg, pack=None, filter=None, limit=None, offset=None):
            return self.st2help(msg, pack, filter, limit, offset)

        def enquiry_list(plugin, msg, args):
            """
            Wrapped plugin method to be able to process generators.
            """
            for r in self.enquiry_list(msg, args):
                yield r

        def enquiry_reply(plugin, msg, args):
            """
            Wrapped plugin method to be able process generators.
            """
            for r in self.enquiry_reply(msg, args):
                yield r

        Help_Command = Command(
            st2help,
            name=f"{self.cfg.plugin_prefix}help",
            cmd_type=arg_botcmd,
            cmd_args=("--pack",),
            cmd_kwargs={"dest": "pack", "type": str},
            doc="Provide help for StackStorm action aliases.",
        )
        Help_Command.append_args(("--filter",), {"dest": "filter", "type": str})
        Help_Command.append_args(("--limit",), {"dest": "limit", "type": int})
        Help_Command.append_args(("--offset",), {"dest": "offset", "type": int})

        self.create_dynamic_plugin(
            name="St2",
            doc=f"err-stackstorm v{ERR_STACKSTORM_VERSION} - A StackStorm plugin for "
            "authentication and Action Alias execution.  Use "
            "{self.cfg.bot_prefix}{self.cfg.plugin_prefix}help for action alias help.",
            commands=(
                Command(
                    lambda plugin, msg, args: self.session_list(msg, args),
                    name=f"{self.cfg.plugin_prefix}session_list",
                    cmd_type=botcmd,
                    cmd_kwargs={"admin_only": True},
                    doc="List any established sessions between the "
                    "chat service and StackStorm API.",
                ),
                Command(
                    lambda plugin, msg, args: self.session_delete(msg, args),
                    name=f"{self.cfg.plugin_prefix}session_cancel",
                    cmd_type=botcmd,
                    cmd_kwargs={"admin_only": True},
                    doc="Allow an administrator to cancel a users session.",
                ),
                Command(
                    lambda plugin, msg, args: self.session_disconnect(msg, args),
                    name="{}session_end".format(self.cfg.plugin_prefix),
                    cmd_type=botcmd,
                    cmd_kwargs={"admin_only": False},
                    doc="End a user session.  StackStorm credentials are "
                    "purged when the session is closed.",
                ),
                Command(
                    lambda plugin, msg, args: self.session_authenticate(msg, args),
                    name="{}session_start".format(self.cfg.plugin_prefix),
                    cmd_type=botcmd,
                    cmd_kwargs={"admin_only": False},
                    doc="Usage: {}session_start <shared_secret>.\n"
                    "Authenticate with StackStorm API over an out of bands communication"
                    " channel.  User Token or API Key are stored in a user session managed by"
                    " err-stackstorm.".format(self.cfg.plugin_prefix),
                ),
                Command(
                    lambda plugin, msg, args: self.execute_actionalias(msg, args),
                    name="{}".format(self.cfg.plugin_prefix),
                    cmd_type=re_botcmd,
                    cmd_kwargs={"pattern": "^{}.*".format(self.cfg.command_prefix)},
                    doc="Run an arbitrary StackStorm command (action-alias).\n"
                    "Available commands can be listed using {}{}help".format(
                        self.cfg.bot_prefix, self.cfg.plugin_prefix
                    ),
                ),
                Command(
                    enquiry_list,
                    name=f"{self.cfg.plugin_prefix}enquiry_list",
                    cmd_type=botcmd,
                    cmd_kwargs={"admin_only": False},
                    doc=f"Usage: {self.cfg.plugin_prefix}enquiry_list\n"
                    "List enquiries awaiting respond.",
                ),
                # TODO: Add the enquiry code when it's completed.
                # ~ Command(
                # ~ lambda plugin, msg, args: self.enquiry_get(msg, args),
                # ~ name=f"{self.cfg.plugin_prefix}enquiry_get",
                # ~ cmd_type=botcmd,
                # ~ cmd_kwargs={"admin_only": False},
                # ~ doc=f"Usage: {self.cfg.plugin_prefix}enquiry_get\n" "View an enquiry.",
                # ~ ),
                # ~ Command(
                # ~ lambda plugin, msg, args: self.enquiry_set(msg, args),
                # ~ name=f"{self.cfg.plugin_prefix}enquiry_set",
                # ~ cmd_type=botcmd,
                # ~ cmd_kwargs={"admin_only": False},
                # ~ doc=f"Usage: {self.cfg.plugin_prefix}enquiry_set\n" "Set an active enquiry.",
                # ~ ),
                # ~ Command(
                # ~ enquiry_reply,
                # ~ name=f"{self.cfg.plugin_prefix}enquiry_reply",
                # ~ cmd_type=botcmd,
                # ~ cmd_kwargs={"admin_only": False},
                # ~ doc=f"Usage: {self.cfg.plugin_prefix}enquiry_reply\n" "Respond to an enquiry.",
                # ~ ),
                Help_Command,
            ),
        )
