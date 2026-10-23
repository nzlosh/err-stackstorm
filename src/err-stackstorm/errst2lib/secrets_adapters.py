# coding:utf-8
import abc
import logging

try:
    import hvac

    HAVE_HVAC = True
except ModuleNotFoundError:
    HAVE_HVAC = False

LOG = logging.getLogger(__name__)


class AbstractSecretsAdapterFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def instantiate(store_type):
        raise NotImplementedError


class SecretsAdapterFactory(AbstractSecretsAdapterFactory):
    @staticmethod
    def instantiate(store_type):
        LOG.debug("Establish connection with secret store service. '{}'".format(store_type))
        return {"vault": VaultSecretsAdapter}.get(store_type, NoOpSecretsAdapter)


class AbstractSecretsAdapter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def setup(self, cfg):
        raise NotImplementedError

    @abc.abstractmethod
    def wrap_secret(self, secret, ttl):
        raise NotImplementedError

    @abc.abstractmethod
    def unwrap(self, token):
        raise NotImplementedError

    @abc.abstractmethod
    def read_kv(self, path, mount_point):
        raise NotImplementedError

    @abc.abstractmethod
    def write_kv(self, k, v, mount_point):
        raise NotImplementedError

    @abc.abstractmethod
    def renew_token(self):
        raise NotImplementedError

    @abc.abstractmethod
    def teardown(self):
        raise NotImplementedError


class NoOpSecretsAdapter(AbstractSecretsAdapter):
    """
    No Op Secret Adapater does nothing.
    """

    def setup(self):
        pass

    def renew_token(self):
        pass

    def wrap_secret(self, secret, ttl):
        pass

    def unwrap(self, token):
        pass

    def read_kv(self, path, mount_point):
        pass

    def write_kv(self, k, v, mount_point):
        pass

    def teardown(self):
        pass


class VaultSecretsAdapter(AbstractSecretsAdapter):
    """
    Vault secrets store.  kv read/write/list and wrap/unwrap.
    """

    def __init__(self, cfg):
        self.client = None
        self.unwrap_path = None
        self.cfg = cfg

    def setup(self):
        if not HAVE_HVAC:
            LOG.warning(
                "hvac module could not be found.  The Vault Secrets "
                "adapter can't function without it."
            )
            return
        self.client = hvac.Client(url=self.cfg["url"])
        self.unwrap_path = self.cfg["unwrap_path"]

        # supported credentials are token or approle.
        token = self.cfg.get("auth", {}).get("token")
        if "token" in self.cfg["auth"]:
            LOG.debug("Vault authentication using Token")
            self.client.token = self.cfg["auth"]["token"]
        elif "approle" in self.cfg["auth"]:
            LOG.debug("Vault authentication using AppRole")
            self.client.auth.approle.login(
                role_id=self.cfg["auth"]["approle"].get("role_id"),
                secret_id=self.cfg["auth"]["approle"].get("secret_id"),
            )
        else:
            raise RuntimeError(
                "Vault Secret backend only supports token or approle authentication."
            )
        LOG.info("Vault token is authenticated = %s", self.client.is_authenticated())

    def renew_token(self, threshold=3600):
        """
        threshold: the minimum number of seconds remaining to request a token.
        """
        # to do, add threshold check
        if True:
            self.teardown()
            self.setup()

    def get_wrap_path(self):
        return self.unwrap_path

    def wrap_secret(self, secret, ttl=30):
        """
        Given a secret and the path
        """
        return self.client.sys.wrap(payload=secret, ttl=ttl)

    def unwrap(self, token):
        """
        Given a chat userid, fetch an unwrap token from unwrap_path and perform the unwrap procedure
        to return the secret contents.
        """
        return self.client.sys.unwrap(token)

    def read_kv(self, path, mount_point="kv"):
        """
        Read a vault secret from kv path.
        """
        return self.client.secrets.kv.v1.read_secret(
            path=path,
            mount_point=mount_point,
        )["data"]

    def write_kv(self, k, v, mount_point="kv"):
        """
        Write a vault secret to the kv path.
        """
        self.client.secrets.kv.v1.create_or_update_secret(k, secret=v, mount_point="kv")

    def teardown(self):
        """
        Close connection with secrets backend.
        """
        if self.client:
            self.client.logout()
            self.client = None
