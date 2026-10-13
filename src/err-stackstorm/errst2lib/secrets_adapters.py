# coding:utf-8
import abc
import logging

LOG = logging.getLogger(__name__)


class AbstractSecretsAdapterFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def instantiate(store_type):
        raise NotImplementedError


class SecretsAdapterFactory(AbstractSecretsAdapterFactory):
    @staticmethod
    def instantiate(store_type):
        LOG.debug("Establish connection with secret store service. '{}'".format(store_type))
        return {"vault": VaultSecretsAdapter}.get(store_type, ClearTextSecretsAdapter)


class AbstractSecretsAdapter(metaclass=abc.ABCMeta):
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


class VaultSecretsAdapter(AbstractSecretsAdapter):
    """
    Vault secrets store.  kv read/write/list and wrap/unwrap.
    """

    def __init__(self):
        import hvac
        self.client = hvac.Client()

    def __str__(self):
        return str(self.associations)

    def setup(self):
        # supported credentials are token or approle.
        backend = cfg.get("secrets", {}).get("backend")
        if backend:
            raise NotImplementedError

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

