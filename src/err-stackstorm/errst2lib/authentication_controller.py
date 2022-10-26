# coding:utf-8
import logging

from errbot.backends.base import Identifier

from errst2lib.errors import SessionInvalidError
from errst2lib.session import generate_password
from errst2lib.session_manager import SessionManager

LOG = logging.getLogger("errbot.plugin.st2.auth_ctrl")


class BotPluginIdentity(object):
    """
    For internal use only by err-stackstorm.  The object is used by methods that will create a
    session and authenticate err-stackstorm credentials with StackStorm.
    """

    def __init__(self, name="errbot%service", secret=generate_password(16)):
        self.name = name
        self.secret = secret

    def __repr__(self):
        return str(self.secret)


class AuthenticationController(object):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = SessionManager(bot.cfg)

    def to_userid(self, user):
        """
        Convert BotIdentity, Identifier to plain text string suitable for use as the key with
        Sessions and cached tokens.
        param: user: may be one of BotIdentity, errbot.backend.base.Identifier or string.
        """
        if isinstance(user, BotPluginIdentity):
            user_id = user.name
        elif isinstance(user, Identifier):
            user_id = self.bot.chatbackend.normalise_user_id(user)
        else:
            user_id = user
        LOG.debug("Authentication User ID is '{}'".format(user_id))
        return user_id

    def pre_execution_authentication(self, chat_user):
        """
        Look up the chat_user to confirm they are authenticated.
        param: chat_user: the chat back end user.
        return: A valid St2 Token or False in the case of an error
        """
        user_id = self.to_userid(chat_user)
        return self.bot.cfg.auth_handler.pre_execution_authentication(self, user_id)

    def consume_session(self, session_id):
        """
        Fetch the session and unseal it to mark it as consumed.
        """
        session = self.sessions.get_by_uuid(session_id)
        if session is False:
            LOG.debug("Invalid session id '{}'.".format(session_id))
            raise SessionInvalidError
        session.unseal()
        return True

    def list_sessions(self):
        """
        Returns a list of sessions.
        """
        return self.sessions.list_sessions()

    def session_url(self, session_id, url_path="/"):
        """
        Return a URL formatted with the UUID query string attached.
        """
        return "{}{}?uuid={}".format(self.bot.cfg.auth_handler.url, url_path, session_id)

    def delete_session(self, session_id):
        """
        Delete a session from the store.
        """
        session = self.sessions.get_by_uuid(session_id)
        if session is False:
            LOG.debug("Session '{}' doesn't exist to be deleted".format(session_id))
            raise SessionInvalidError
        else:
            self.sessions.delete(session.user_id)

    def get_session_userid(self, session_id):
        session = self.sessions.get_by_uuid(session_id)
        session.is_expired()
        return session.user_id

    def get_token_by_userid(self, user):
        """
        Get the associated StackStorm token/key given chat backend username.
        Return StackStorm token/key associated with the user or False if session isn't valid or
        secret is missing.
        """
        secret = False
        session = self.sessions.get_by_userid(self.to_userid(user))
        if session:
            secret = self.get_token_by_session(session.id())
        return secret

    def get_token_by_session(self, session_id):
        """
        Get the associated StackStorm token/key given session id.
        """
        LOG.debug("Get token for session id {}".format(session_id))
        return self.sessions.get_secret(session_id)

    def set_token_by_session(self, session_id, token):
        """
        Stores a StackStorm user token or api key in the secrets store using the session id.
        """
        return self.sessions.put_secret(session_id, token)

    def set_token_by_userid(self, user_id, token):
        """
        Store StackStorm user token or api key in the secrets store.
        """
        session = self.sessions.get_by_userid(self.to_userid(user_id))
        if session:
            ret = self.set_token_by_session(session.id(), token)
        else:
            LOG.debug("Failed to lookup session for user id '{}'".format(user_id))
        return ret

    def create_session(self, user, user_secret):
        """
        Handle an initial request to establish a session.  If a session already exists, return it.
        """
        user_id = self.to_userid(user)
        return self.sessions.create(user_id, user_secret, self.bot.cfg.session_ttl)

    def get_session(self, user):
        """
        Returns the session associated with the user.
        """
        user_id = self.to_userid(user)
        session = self.sessions.get_by_userid(user_id)
        if session is False:
            raise SessionInvalidError
        return session

    def match_secret(self, session_id, user_secret):
        """
        Fetch session and compare user_secret.
        """
        session = self.sessions.get_by_uuid(session_id)
        if session is False:
            LOG.debug("Session '{}' doesn't exist.".format(session_id))
            raise SessionInvalidError

        if session.is_sealed():
            LOG.warning("Attempting to check secret while session is sealed.")
            return False

        return session.match_secret(user_secret)

    def associate_credentials(self, user, creds, bot_creds):
        """
        Verify credentials against stackstorm and if successful, store them using the user id.
        param: user: the normalised chat_user account.
        param: creds: the stackstorm user credentials to validate against StackStorm API.
        param: bot_creds: the bot credentials to use when authenticating user credentials.
        Return true if credentials were valid or False if they were not.
        """
        # get the configured authentication handler.
        token = self.bot.cfg.auth_handler.authenticate(user, creds, bot_creds)

        # WARNING: Sensitive security information will be logged, uncomment only when necessary.
        # LOG.debug("Token for {} was {}".format(user, token))

        # pass credentials to authentication handler verify credentials
        if token:
            self.set_token_by_userid(user, token)
        else:
            LOG.warning("Failed to validate StackStorm credentials for {}.".format(user))
        # Explicitly test not false to avoid returning tokens value.
        return token is not False
