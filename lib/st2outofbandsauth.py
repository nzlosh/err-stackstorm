# coding:utf-8
import uuid
import string
import hashlib
import logging
from datetime import datetime as dt
from random import SystemRandom
from lib.st2storeadapters import StoreAdapterFactory
LOG = logging.getLogger("{}".format(__name__))


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

    def get_by_userid(self, user_id):
        """
        Get information by user_id.
        """
        LOG.debug("Fetch user_id '{}' in store.".format(user_id))
        return self.memory.get(user_id, False)

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
        session = self.memory.get(user_id, False)
        if session:
            if session.id() in self.id_to_user_map:
                del self.id_to_user_map[session.id()]
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
        user_id = self.id_to_user_map.get(session_id, False)
        LOG.debug("Session id '{}' is associated with user_id {}".format(session_id, user_id))
        session = self.memory.get(user_id, False)
        if session is False:
            LOG.debug("Error: Session id '{}' points to a missing session.".format(""))
        return session


class Session(object):
    def __init__(self, user_id, user_secret):
        self.bot_secret = None
        self.hashed_secret = self._hash_secret(user_secret)
        del user_secret
        self.user_id = user_id
        self._session_id_available = True
        self.session_id = uuid.uuid4()
        self.create_date = int(dt.now().timestamp())
        self.modified_date = self.create_date
        self.ttl_in_seconds = 3600

    def expired(self):
        """
        Returns true if both create and modified timestamps have exceeded the ttl.
        """
        now = int(dt.now().timestamp())
        create_expiry = self.create_date + self.ttl_in_seconds
        modified_expiry = self.modified_date + self.ttl_in_seconds
        return create_expiry < now and modified_expiry < now

    def __repr__(self):
        return "".join([
            "UserID: {}, ".format(str(self.user_id)),
            "Session Consumed: {}, ".format(str(self._session_id_available)),
            "SessionID: {}, ".format(str(self.session_id)),
            "Creation Data: {}, ".format(str(dt.fromtimestamp(self.create_date))),
            "Modified Date: {}, ".format(str(dt.fromtimestamp(self.modified_date))),
            "Expiry Date: {}".format(
                str(dt.fromtimestamp(self.modified_date + self.ttl_in_seconds))
            )
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
        return str(self.session_id)

    def ttl(self, ttl=None):
        if ttl is None:
            return self.ttl

        if isinstance(ttl, int()):
            self.ttl = ttl
            self.modified_date = dt.now()
        else:
            LOG.warning("session ttl must be an integer type, got '{}'".format(ttl))

    def _hash_secret(self, user_secret):
        """
        Generate a unique token by hashing a random bot secret with the user secrets.
        param: user_secret[string] - The users secret provided in the chat backend.
        """
        rnd = SystemRandom(user_secret)
        if self.bot_secret is None:
            self.bot_secret = "".join([rnd.choice(string.hexdigits) for _ in range(8)])
        h = hashlib.sha256()
        h.update(bytes(user_secret, "utf-8"))
        del user_secret
        h.update(bytes(self.bot_secret, "utf-8"))
        return h.hexdigest()


class SessionManager(object):
    def __init__(self):
        self.store = SessionStore()
        self.secure_store = StoreAdapterFactory.keyring_adapter()
        self.secure_store.setup()

    def get_by_userid(self, user_id):
        """
        Fetch information from the store by user_id.
        @user_id: A string uniquely identifying the chat user.
        """
        return self.store.get_by_userid(user_id)

    def get_by_uuid(self, _uuid):
        """
        Fetch information related to a session by its UUID.
        If a session doesn't exist, False is returned.
        """
        return self.store.get_by_uuid(_uuid)

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

    def use_session_id(self, session_id):
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

    def request_session(self, user, user_secret):
        """
        Handle an initial request to establish a session.  If a session already exists, return it.
        """
        auth_msg = ""
        user_id = self.bot.chatbackend.normalise_user_id(user)
        session = self.sessions.get_by_userid(user_id)

        if session is False:
            session = self.sessions.create(user_id, user_secret)
            auth_msg = "Your challenge response is {}".format(
                self.session_url(session.id(), "/index.html")
            )
        else:
            if session.expired():
                self.sessions.delete(user_id)
                session = self.sessions.create(user_id, user_secret)
                auth_msg = "Your challenge response is {}".format(
                    self.session_url(session.id(), "/index.html")
                )
            else:
                auth_msg = "A valid session already exists for {}.".format(user_id)

        return auth_msg
