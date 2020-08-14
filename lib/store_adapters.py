# coding:utf-8
import abc
import logging

LOG = logging.getLogger(__name__)


class AbstractStoreAdapterFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def instantiate(store_type):
        raise NotImplementedError


class StoreAdapterFactory(AbstractStoreAdapterFactory):
    @staticmethod
    def instantiate(store_type):
        LOG.debug("Create secret store for '{}'".format(store_type))
        return {"cleartext": ClearTextStoreAdapter}.get(store_type, ClearTextStoreAdapter)


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
    The clear text store adapter doesn't encrypt data in memory, but doesn't persist it to disk
    either.  If more secure methods are required to operate, open an issue requesting a new feature.
    """

    def __init__(self):
        self.associations = {}

    def __str__(self):
        return str(self.associations)

    def setup(self):
        pass

    def set(self, name, secret, namespace=""):
        self.associations[name] = secret
        return True

    def get(self, name, namespace=""):
        return self.associations.get(name)

    def delete(self, name, namespace=""):
        if name in self.associations:
            del self.associations[name]

    def teardown(self):
        pass


class SessionStore(object):
    def __init__(self):
        """
        Sessions are stored by userid with a lookup index for uuid's to user_ids.
        """
        self.memory = {}
        self.id_to_user_map = {}

    def list(self):
        """
        Return a list of string representation of session.
        """
        return [self.memory[k] for k in self.memory.keys()]

    def get_by_userid(self, user_id):
        """
        Get information by user_id.
        """
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
        else:
            LOG.warning("Failed to delete user_id {} session - Not found.".format(user_id))

    def put_by_id(self, session_id, session):
        """
        Put a session in the store using the session id.
        """
        if session.user_id in self.memory:
            self.id_to_user_map[session_id] = session.user_id

    def get_by_uuid(self, session_id):
        user_id = self.id_to_user_map.get(session_id, False)
        session = self.memory.get(user_id, False)
        if session is False:
            LOG.debug("Error: Session id '{}' points to a missing session.".format(""))
        return session
