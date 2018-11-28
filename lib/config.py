# coding:utf-8
import logging
from lib.credentials_adapaters import CredentialsFactory
from lib.authentication_handler import AuthHandlerFactory

LOG = logging.getLogger(__name__)


class PluginConfiguration(object):
    def __init__(self, bot_conf, plugin_prefix):
        self.plugin_prefix = plugin_prefix
        self._configure_prefixes(bot_conf)
        self._configure_credentials(bot_conf)
        self._configure_rbac_auth(bot_conf)
        self._configure_stackstorm(bot_conf)
        self.oob_auth_url = bot_conf.STACKSTORM.get('oob_auth_url', "https://localhost:8888/")
        self.timer_update = bot_conf.STACKSTORM.get('timer_update', 60)
        self.verify_cert = bot_conf.STACKSTORM.get('verify_cert', True)

        self.client_cert = bot_conf.STACKSTORM.get('client_cert', None)
        self.client_key = bot_conf.STACKSTORM.get("client_key", None)
        self.ca_cert = bot_conf.STACKSTORM.get("ca_cert", None)

    def _configure_rbac_auth(self, bot_conf):
        rbac_auth = bot_conf.STACKSTORM.get('rbac_auth', {"standalone": {}})
        if "clientside" in rbac_auth:
            self.auth_handler = ProxiedAuthHandler(rbac_auth["clientside"])
            return
        elif "serverside" in rbac_auth:
            self.auth_handler = OutOfBandsAuthHandler(rbac_auth["serverside"])
            return
        if rbac_auth == {}:
            self.auth_handler = StandaloneAuthHandler()
            return
        LOG.warning("Failed to configure RBAC authentication handler.  Check the configuration.")
        return False

    def _configure_prefixes(self, bot_conf):
        self.bot_prefix = bot_conf.BOT_PREFIX
        self.full_prefix = "{}{} ".format(bot_conf.BOT_PREFIX, self.plugin_prefix)

    def _configure_stackstorm(self, bot_conf):
        self.api_url = bot_conf.STACKSTORM.get('api_url', 'http://localhost:9101/v1')
        self.auth_url = bot_conf.STACKSTORM.get('auth_url', 'http://localhost:9100/v1')
        self.stream_url = bot_conf.STACKSTORM.get('stream_url', 'http://localhost:9102/v1')

    def _configure_credentials(self, bot_conf):
        self.api_auth = bot_conf.STACKSTORM.get('api_auth', {})
        self.bot_creds = None
        for cred_type in ["key", "user", "token"]:
            c = self.api_auth.get(cred_type)
            if c:
                if cred_type == "user":
                    self.bot_creds = CredentialsFactory.instantiate(cred_type)(
                        c.get('name'),
                        c.get('password')
                    )
                    break
                else:
                    self.bot_creds = CredentialsFactory.instantiate(cred_type)(c)
                    break
        if self.bot_creds is None:
            LOG.warning("Failed to find any valid st2 credentials for the bot, check the bots configuration.")

