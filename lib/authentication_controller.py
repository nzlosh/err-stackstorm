# coding:utf-8
import string
import logging
from random import SystemRandom
from lib.stackstorm_api import StackStormAPI
from lib.session_manager import SessionManager
from lib.errors import SessionInvalidError

LOG = logging.getLogger(__name__)


def generate_password(length=8):
    rnd = SystemRandom()
    if length > 255:
        length = 255
    return "".join([rnd.choice(string.hexdigits) for _ in range(length)])


class BotPluginIdentity(object):
    """
    For internal use only by err-stackstorm.  The object is used by methods that will create a
    session and authenticate err-stackstorm credentials with StackStorm.
    """
    def __init__(self, name="errbot%service", secret=generate_password(16)):
        self.name = name
        self.secret = secret


class AuthenticationController(object):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = SessionManager(bot.cfg)

    def consume_session(self, session_id):
        """
        Fetch the session and unseal it to make it as consumed.
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
        return "{}{}?uuid={}".format(
            self.bot.cfg.rbac_auth_opts.get("url"), url_path, session_id
        )

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
        if isinstance(user, BotPluginIdentity):
            user = user.name
        session = self.sessions.get_by_userid(user)
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
        session = self.sessions.get_by_userid(user_id)
        if session:
            ret = self.set_token_by_session(session.id(), token)
        else:
            LOG.debug("Failed to lookup session for user id '{}'".format(user_id))
        return ret

    def create_session(self, user, user_secret):
        """
        Handle an initial request to establish a session.  If a session already exists, return it.
        """
        if isinstance(user, BotPluginIdentity):
            user_id = user.name
        else:
            user_id = self.bot.chatbackend.normalise_user_id(user)

        return self.sessions.create(user_id, user_secret)

    def get_session(self, user):
        """
        Returns the session associated with the user.
        """
        if isinstance(user, BotPluginIdentity):
            user_id = user.name
        else:
            user_id = self.bot.chatbackend.normalise_user_id(user)

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
        """
        # get the configured authentication handler.
        token = self.bot.cfg.auth_handler.authenticate(creds, bot_creds)
        # pass credentials to authentication handler verify credentials
        if token:
            self.set_session_token(user, token)
        else:
            LOG.warning("Failed to validate StackStorm credentials for {}.".format(user))
