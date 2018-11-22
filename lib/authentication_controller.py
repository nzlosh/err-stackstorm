# coding:utf-8
import string
import logging
from random import SystemRandom
from lib.session_manager import SessionManager

LOG = logging.getLogger(__name__)


def generate_password(length=8):
    rnd = SystemRandom()
    if length > 255:
        length = 255
    return "".join([rnd.choice(string.hexdigits) for _ in range(length)])


class BotPluginIdentity(object):
    """
    For internal use only by err-stackstorm.  The object is used to call methods that will create a
    session and authenticate err-stackstorm credentials with StackStorm.
    """
    def __init__(self, name="errbot%service", secret=generate_password(16)):
        self.name = name
        self.secret = secret


class AuthenticationController(object):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = SessionManager()

    def consume_session(self, session_id):
        ret = False
        session = self.sessions.get_by_uuid(session_id)
        if session is False:
            LOG.debug("Invalid session id '{}'.".format(session_id))
        else:
            ret = session.use_session_id()
            if ret is False:
                LOG.debug("Session id '{}' has already been consumed.".format(session_id))
            if session.expired():
                ret = False
                LOG.debug("Session has expired '{}'.".format(session_id))
        return ret

    def list_sessions(self):
        return self.sessions.list_sessions()

    def session_url(self, session_id, url_path="/"):
        """
        Return a URL formatted with the UUID query sting attached.
        """
        return "{}{}?uuid={}".format(
            self.bot.st2config.rbac_auth_opts.get("url"), url_path, session_id
        )

    def delete_session(self, session_id):
        session = self.sessions.get_by_uuid(session_id)
        if session is False:
            LOG.debug("Session '{}' doesn't exist to be deleted".format(session_id))
        else:
            self.sessions.delete(session.user_id)

    def get_session_token(self, user):
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
            LOG.debug("Get token for '{}' with session id {}".format(user, session.session_id))
            secret = self.sessions.get_secret(session.session_id)
        return secret

    def set_session_token(self, session, token):
        return self.sessions.put_secret(session.session_id, token)

    def request_session(self, user, user_secret):
        """
        Handle an initial request to establish a session.  If a session already exists, return it.
        """
        if isinstance(user, BotPluginIdentity):
            user_id = user.name
        else:
            user_id = self.bot.chatbackend.normalise_user_id(user)

        session = self.sessions.get_by_userid(user_id)

        if session is False:
            session = self.sessions.create(user_id, user_secret)
        else:
            if session.expired():
                self.sessions.delete(user_id)
                session = self.sessions.create(user_id, user_secret)

        return session
