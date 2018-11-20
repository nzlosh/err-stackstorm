# coding:utf-8
import uuid
import logging
from datetime import datetime as dt
from random import SystemRandom
from lib.store_adapters import StoreAdapterFactory
from lib.stackstorm_api import St2PluginAPI

LOG = logging.getLogger(__name__)


class SessionExpiredError(Exception):
    pass


class SessionInvalidError(Exception):
    pass


class SessionManager(object):
    def __init__(self):
        self.store = SessionStore()
        # TODO: FIXME: Support definition of store backend in configuration file.
        self.secure_store = StoreAdapterFactory.instantiate("developer")()
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
