# coding:utf-8
import abc
import time
import string
import logging
from pathlib import Path
from random import SystemRandom  # TODO: replace SystemRandom secrets which is added to Python 3.6

LOG = logging.getLogger(__name__)


class AbstractStoreAdapterFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def instantiate(store_type):
        raise NotImplementedError

    @abc.abstractmethod
    def keyring_adapter(self):
        raise NotImplementedError

    @abc.abstractmethod
    def vault_adpater(self):
        raise NotImplementedError


class StoreAdapterFactory(AbstractStoreAdapterFactory):
    @staticmethod
    def instantiate(store_type):
        LOG.debug("Create secret store for '{}'".format(store_type))
        return {
            "cleartext": ClearTextStoreAdapter,
            "keyring": KeyringStoreAdapter,
            "vault": VaultStoreAdapter
        }.get(store_type, KeyringStoreAdapter)

    @staticmethod
    def keyring_adapter():
        return KeyringStoreAdapter()

    @staticmethod
    def vault_adapter():
        return VaultStoreAdapter()

    @staticmethod
    def developer_adapter():
        return ClearTextStoreAdapter()


class AbstractStoreAdapter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def setup(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def set(self, name, secret, namespace):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, name, namespace):
        raise NotImplementedError

    @abc.abstractmethod
    def teardown(self, user):
        raise NotImplementedError


class ClearTextStoreAdapter(AbstractStoreAdapter):
    """
    This is only intended for use in development environments.
    Never use this in production, it offers no security.
    """
    def __init__(self):
        self.associations = {}

    def __str__(self):
        return str(self.associations)

    def setup(self):
        pass

    def set(self, name, secret, namespace=""):
        # TODO: disable this log after debugging complete.
        LOG.debug("__ClearTextStoreAdapter.set({}, {}).".format(name, secret))
        self.associations[name] = secret
        return True

    def get(self, name, namespace=""):
        LOG.debug("__ClearTextStoreAdapter.get({}).".format(name))
        return self.associations.get(name)

    def delete(self, name, namespace=""):
        LOG.debug("__ClearTextStoreAdapter.delete({}).".format(name))
        if name in self.associations:
            del self.associations[name]

    def teardown(self):
        pass


class KeyringStoreAdapter(AbstractStoreAdapter):
    import keyring

    def __init__(self):
        rnd = SystemRandom(str(int(time.time()) % 1000))
        self.password = "".join([rnd.choice(string.hexdigits) for _ in range(46)])

    def setup(self, filename='errbot_secrets.conf'):
        self.kr = KeyringStoreAdapter.keyring.get_keyring()
        self.kr.filename = filename
        # TODO: fix calls to remove stored file when bot stops running.
        # Path.unlink(self.kr.file_path)

    def set(self, name, secret, namespace="errst2"):
        self.kr.set_password(namespace, name, secret)

    def get(self, name, namespace="errst2"):
        self.kr.get_password(namespace, name)

    def delete(self, name, namespace="errst2"):
        raise NotImplementedError

    def teardown(self):
        # TODO: fix calls to remove stored file when bot stops running.
        # Path.unlink(self.kr.file_path)
        Path(".").exists()


class VaultStoreAdapter(AbstractStoreAdapter):
    import hvac

    def __init__(self):
        self.client = None

    def setup(self, filename):
        self.client = VaultStoreAdapter.hvac.Client()

    def set(self, name, secret, namespace="errst2"):
        raise NotImplementedError

    def delete(self, name, namespace="errst2"):
        raise NotImplementedError

    def get(self, name, namespace="errst2"):
        raise NotImplementedError

    def teardown():
        raise NotImplementedError


class SessionStore(object):
    def __init__(self):
        """
        Sessions are stored by userid with a lookup index for uuid's to user_ids.
        """
        self.memory = {}
        self.id_to_user_map = {}

    def list(self):
        return [k+str(self.memory[k]) for k in self.memory.keys()]

    def get_by_userid(self, user_id):
        """
        Get information by user_id.
        """
        LOG.debug("__SessionStore.get_by_userid(user_id={})".format(user_id))
        return self.memory.get(user_id, False)

    def put(self, session):
        """
        Put a new session in the store using the user_id as the key
        and create a reverse mapping between the user_id and the session_id.
        """
        LOG.debug("__SessionStore.put(session={})".format(session))
        self.memory[session.user_id] = session
        self.id_to_user_map[session.id()] = session.user_id

    def delete(self, user_id):
        """
        Delete a session by user_id.  Delete the reverse mapping
        if it exists.
        """
        LOG.debug("__SessionStore.delete(user_id={})".format(user_id))
        session = self.memory.get(user_id, False)
        if session:
            if session.id() in self.id_to_user_map:
                del self.id_to_user_map[session.id()]
            del self.memory[user_id]
        else:
            LOG.warning("Failed to delete user_id {} session - Not found.".format(user_id))

    def put_by_id(self, session_id, session):
        """
        Put a session in the store using the session id.
        """
        LOG.debug("__SessionStore.put_by_id(session_id={}, session={})".format(session_id, session))
        if session.user_id in self.memory:
            self.id_to_user_map[session_id] = session.user_id

    def get_by_uuid(self, session_id):
        LOG.debug("__SessionStore.get_by_uuid(session_id={})".format(session_id))
        user_id = self.id_to_user_map.get(session_id, False)
        session = self.memory.get(user_id, False)
        if session is False:
            LOG.debug("Error: Session id '{}' points to a missing session.".format(""))
        return session
