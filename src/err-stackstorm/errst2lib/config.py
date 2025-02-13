# coding:utf-8
import logging

from errst2lib.authentication_handler import AuthHandlerFactory
from errst2lib.credentials_adapters import CredentialsFactory

LOG = logging.getLogger(__name__)


class BorgSingleton:
    """
    Borg Singleton pattern as described in Python Patterns, Idioms and Tests.
    """

    _shared_state = None

    def __init__(self):
        self.__dict__ = BorgSingleton._shared_state


class PluginConfiguration(BorgSingleton):
    """
    err-stackstorm shared configuration.
    """

    def __init__(self):
        super(BorgSingleton, self).__init__()

    def setup(self, bot_conf):
        if not hasattr(bot_conf, "STACKSTORM"):
            LOG.critical(
                "Missing STACKSTORM configuration in config.py.   err-stackstorm must be configured"
                " correctly to function.  See the err-stackstorm documentation for configuration "
                "instructions."
            )
            bot_conf.__setattr__("STACKSTORM", {})
        self._configure_prefixes(bot_conf)
        self._configure_credentials(bot_conf)
        self._configure_rbac_auth(bot_conf)
        self._configure_stackstorm(bot_conf)
        self.oob_auth_url = bot_conf.STACKSTORM.get("oob_auth_url", "https://localhost:8888/")
        self.timer_update = bot_conf.STACKSTORM.get("timer_update", 60)
        self.verify_cert = bot_conf.STACKSTORM.get("verify_cert", True)
        self.secrets_store = bot_conf.STACKSTORM.get("secrets_store", "cleartext")
        self.route_key = bot_conf.STACKSTORM.get("route_key", "errbot")
        self.session_ttl = bot_conf.STACKSTORM.get("session_ttl", 3600)
        self.user_token_ttl = bot_conf.STACKSTORM.get("user_token_ttl", 86400)

        self.client_cert = bot_conf.STACKSTORM.get("client_cert", None)
        self.client_key = bot_conf.STACKSTORM.get("client_key", None)
        self.ca_cert = bot_conf.STACKSTORM.get("ca_cert", None)

    def _configure_rbac_auth(self, bot_conf):
        self.auth_handler = None
        rbac_auth = bot_conf.STACKSTORM.get("rbac_auth", {"standalone": {}})
        for rbac_type in list(rbac_auth.keys()):
            self.auth_handler = AuthHandlerFactory.instantiate(rbac_type)(
                self, rbac_auth[rbac_type]
            )
        if self.auth_handler is None:
            LOG.warning(
                "Failed to configure RBAC authentication handler.  Check the configuration."
            )
        return True

    def _configure_prefixes(self, bot_conf):
        self.bot_prefix = bot_conf.BOT_PREFIX
        self.plugin_prefix = bot_conf.STACKSTORM.get("plugin_prefix", "st2")
        # If there is a plugin prefix set we want a space between it and the command, otherwise not
        if bot_conf.STACKSTORM.get("plugin_prefix", True):
            self.command_prefix = "{} ".format(self.plugin_prefix)
        else:
            self.command_prefix = "{}".format(self.plugin_prefix)
        self.full_prefix = "{}{} ".format(bot_conf.BOT_PREFIX, self.plugin_prefix)

    def _configure_stackstorm(self, bot_conf):
        self.api_url = bot_conf.STACKSTORM.get("api_url", "http://localhost:9101/v1")
        self.auth_url = bot_conf.STACKSTORM.get("auth_url", "http://localhost:9100/v1")
        self.stream_url = bot_conf.STACKSTORM.get("stream_url", "http://localhost:9102/v1")

    def _configure_credentials(self, bot_conf):
        self.api_auth = bot_conf.STACKSTORM.get("api_auth", {})
        self.bot_creds = None
        for cred_type in ["apikey", "user", "token"]:
            c = self.api_auth.get(cred_type)
            if c:
                if cred_type == "user":
                    self.bot_creds = CredentialsFactory.instantiate(cred_type)(
                        c.get("name"), c.get("password")
                    )
                    break
                else:
                    self.bot_creds = CredentialsFactory.instantiate(cred_type)(c)
                    break
        if self.bot_creds is None:
            LOG.warning(
                "Failed to find any valid st2 credentials for the bot,  check configuration file."
            )
