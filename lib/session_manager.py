# coding:utf-8
import logging
from lib.session import Session
from lib.store_adapters import SessionStore
from lib.store_adapters import StoreAdapterFactory
from lib.errors import SessionExistsError

LOG = logging.getLogger(__name__)


class SessionManager(object):
    def __init__(self):
        self.store = SessionStore()
        # TODO: FIXME: Support definition of store backend in configuration file.
        self.secure_store = StoreAdapterFactory.instantiate("developer")()
        self.secure_store.setup()

    def get_by_userid(self, user_id):
        """
        Fetch information from the store by user_id.
        param: user_id[string]  A string uniquely identifying the chat user.
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
        param: user_secret - A pseudo-secret word provided by
        the user and used as part of the UUID hashing process.
        """
        # Don't create a new session if one already exists.
        if self.exists(user_id):
            raise SessionExistsError
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
        """
        List all available sessions.
        """
        return self.store.list()

    def update(self, session):
        raise NotImplementedError

    def exists(self, user_id):
        return self.store.get_by_userid(user_id) is not False

    def put_secret(self, session_id, secret):
        return self.secure_store.set(session_id, secret)

    def get_secret(self, session_id):
        self.secure_store.get(session_id)
