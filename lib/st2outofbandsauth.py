# -*- coding: utf-8 -*-
import datetime
import uuid
import string
from random import SystemRandom
import hashlib
import logging
LOG = logging.getLogger(__name__)


class SessionStore(object):
    def __init__(self):
        """
        Sessions are stored by userid with a lookup index for
        uuid's to user_ids.
        """
        self.memory = {}
        self.id_to_user_map = {}

    def list(self):
        return [k+str(self.memory[k]) for k in self.memory.keys()]

    def get_by_userid(self, key):
        """
        Get information by user_id.
        """
        return self.memory.get(key, False)

    def put(self, session):
        """
        Put a new session in the store using the user_id as the key
        and create a reverse mapping between the user_id and the session_id.
        """
        self.memory[session.user_id] = session
        self.id_to_user_map[session.id()] = session.user_id

    def delete(self, user_id):
        """
        Delete a session by user_id.  Delete the reverse mapping
        if it exists.
        """
        self.memory[user_id] = session
        if session:
            if session.id in self.id_to_user_map:
                del self.id_to_user_map[session.id]
            del self.memory[user_id]

    def put_by_id(self, session_id, session):
        """
        Put a session in the store using the session id.
        """
        if session.user_id in self.memory:
            self.self.id_to_user_map[session_id] = session.user_id

    def pop_by_id(self, session_id):
        return self.memory.pop(self.id_to_user_map.pop(session_id, ""), False)

    def get_by_uuid(self, session_id):
        return self.memory.get(self.id_to_user_map.get(session_id, ""), False)


class Session(object):
    def __init__(self, user_id, user_secret):
        self.hashed_secret = self._hash_secret(user_secret)
        del user_secret
        self.user_id = user_id
        self._session_id_available = True
        self.session_id = uuid.uuid4()
        self.create_date = datetime.datetime.now()
        self.modified_date = self.create_date
        self.ttl_in_seconds = 3600

    def __repr__(self):
        return "{}".format([
            str(self.user_id),
            str(self._session_id_available),
            str(self.session_id),
            str(self.create_date),
            str(self.modified_date),
            str(self.ttl_in_seconds)
        ])

    def use_session_id(self):
        ret = self._session_id_available
        if self._session_id_available:
            self._session_id_available = False
        return ret

    def session_id_available(self):
        """
        Return the state of the one time use
        """
        return self._session_id_available

    def id(self):
        return self.session_id

    def ttl(self, ttl=None):
        if ttl is None:
            return self.ttl

        if isinstance(ttl, int()):
            self.ttl = ttl
            self.modified_date = datetime.datetime.now()
        else:
            LOG.warning("session ttl must by an integer type, got '{}'".format(ttl))

    def _hash_secret(self, user_secret):
        """
        Generate a unique token by hashing a random bot secret with the user secrets.
        param: user_secret[string] - The users secret provided in the chat backend.
        """
        rnd = SystemRandom(user_secret)
        bot_secret = "".join([rnd.choice(string.hexdigits) for _ in range(8)])
        h = hashlib.sha256()
        h.update(bytes(user_secret, "utf-8"))
        del user_secret
        h.update(bytes(bot_secret, "utf-8"))
        return h.hexdigest()


def ChallengeRequest(username, user_secret, bot_secret):
    """
    Generate a random bot_secret and use it to sign the username
    and user_secret values.
    Use the resulting value as a salt to create UUID.
    """
    raise NotImplementedError


def ChallengeResponseURL(uuid):
    """
    Takes a uuid and generates a one time use url to be consumed by
    the chat backend user.  An entry is created in the session hashtable
    with session information, chatbackend username, user_secret, bot_secret,
    uuid.
    """
    raise NotImplementedError


def PrivateMessageToChatUser(username, message):
    """
    param: username - The chat backend username to send the private message to.
    param: message - A string containing the message to be sent.
    """
    raise NotImplementedError


def OneTimeURLLogin(username, uuid):
    """
    This function is only called by the url uuid challenge end point.
    The url must contain a valid uuid.  The uuid is looked up in the
    sessions hash table.  The uuid token is removed and a redirect
    is sent to signal to the client that they should proceed to the
    authentication form.
    """
    raise NotImplementedError


class SessionManager(object):
    def __init__(self):
        self.store = SessionStore()

    def get_by_userid(self, user_id):
        """
        Fetch information related to session.
        """
        return self.store.get_by_userid(user_id)

    def get_by_uuid(self, uuid):
        """
        Fetch information related to a session by its UUID.
        If a session doesn't exist, False is returned.
        """
        return self.store.get_by_userid(self.store.get_by_uuid(uuid))

    def create(self, user_id, user_secret):
        """
        param: user_id - Chat user unique identifier.
        param: ser_secret - A pseudo-secret word provided
                      by the user and used as part of the UUID hashing process
        """
        session = self.store.get_by_userid(user_id)
        # Create a new session if one doesn't exist already.
        if session is False:
            session = Session(user_id, user_secret)
            # Store the session.
            self.store.put(session)
        return session

    def delete(self, user_id):
        """
        Remove a session from the manager
        """
        self.store.delete(user_id)

    def list_sessions(self):
        return self.store.list()

    def update(self, session):
        raise NotImplementedError

    def exists(self, user_id):
        return user_id in self.store.keys()


class AuthenticationController(object):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = SessionManager()

    def use_session_id(self, id):
        ret = False
        session = self.sessions.get_by_uuid(id)
        LOG.debug("UUID {} has a session: {}".format(id, session))
        if session:
            if session.session_id_available():
                ret = session.use_session_id()
        return ret

    def list_sessions(self):
        return self.sessions.list_sessions()

    def session_url(self, session_id):
        session = self.sessions.get_by_uuid(session_id)
        return "https://{}/{}?uuid={}".format("some_host", "some_path", session.id())

    def request_session(self, user, user_secret):
        """
        Handle an initial request to establish a session.  If a session already exists, return it.
        """
        user_id = self.bot.chatbackend.normalise_user_id(user)
        session = self.sessions.get_by_userid(user_id)
        if session:
            LOG.debug("Session already exists for {}.", user_id)
        else:
            self.sessions.create(user_id, user_secret)
            session = self.sessions.get_by_userid(user_id)
            return "Your challenge response is " \
                   "https://carlos.dev.dc3.dailymotion.com:8888/index.html?uuid=" \
                   "{}".format(session.id())
