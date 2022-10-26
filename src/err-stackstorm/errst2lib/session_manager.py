# coding:utf-8
import logging

from errst2lib.errors import SessionExistsError, SessionInvalidError
from errst2lib.session import Session
from errst2lib.store_adapters import SessionStore, StoreAdapterFactory

LOG = logging.getLogger("errbot.plugin.st2.session_mgr")


class SessionManager(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.store = SessionStore()
        self.secure_store = StoreAdapterFactory.instantiate(cfg.secrets_store)()
        self.secure_store.setup()

    def get_by_userid(self, user_id):
        """
        Fetch information from the store by user_id.
        param: user_id[string]  A string uniquely identifying the chat user.
        """
        session = self.store.get_by_userid(user_id)
        if session is False:
            raise SessionInvalidError
        return session

    def get_by_uuid(self, _uuid):
        """
        Fetch information related to a session by its UUID.
        If a session doesn't exist, False is returned.
        """
        session = self.store.get_by_uuid(_uuid)
        if session is False:
            raise SessionInvalidError
        return session

    def create(self, user_id, user_secret, session_ttl):
        """
        param: user_id - Chat user unique identifier.
        param: user_secret - A pseudo-secret word provided by
        the user and used as part of the UUID hashing process.
        """
        # Don't create a new session if one already exists.
        if self.exists(user_id):
            raise SessionExistsError
        session = Session(user_id, user_secret, session_ttl)
        # Store the session.
        self.store.put(session)
        return session

    def delete(self, user_id):
        """
        Remove a session from the manager
        """
        session = self.get_by_userid(user_id)
        if session:
            self.secure_store.delete(session.id())
        self.store.delete(user_id)

    def list_sessions(self):
        """
        List all available sessions.
        """
        return self.store.list()

    def update(self, session):
        raise NotImplementedError

    def exists(self, user_id):
        return self.store.get_by_userid(user_id) is not False

    def put_secret(self, session_id, secret):
        self.secure_store.set(session_id, secret)
        return True

    def get_secret(self, session_id):
        return self.secure_store.get(session_id)
