# coding:utf-8
import logging
from lib.authentication_handler import St2ApiKey, St2UserToken, St2UserCredentials

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
        rbac_auth = bot_conf.STACKSTORM.get('rbac_auth', {})
        if "proxied" in rbac_auth:
            self.rbac_auth_type = "proxied"
            self.rbac_auth_opts = rbac_auth["proxied"]
        if "extended" in rbac_auth:
            self.rbac_auth_type = "extended"
            self.rbac_auth_opts = rbac_auth["extended"]
        if rbac_auth == {}:
            self.rbac_auth_type = "simple"
            self.rbac_auth_opts = {}

    def _configure_prefixes(self, bot_conf):
        self.bot_prefix = bot_conf.BOT_PREFIX
        self.full_prefix = "{}{} ".format(bot_conf.BOT_PREFIX, self.plugin_prefix)

    def _configure_stackstorm(self, bot_conf):
        self.api_url = bot_conf.STACKSTORM.get('api_url', 'http://localhost:9101/v1')
        self.auth_url = bot_conf.STACKSTORM.get('auth_url', 'http://localhost:9100/v1')
        self.stream_url = bot_conf.STACKSTORM.get('stream_url', 'http://localhost:9102/v1')

    def _configure_credentials(self, bot_conf):
        self.api_auth = bot_conf.STACKSTORM.get('api_auth', {})
        c = self.api_auth.get("token")
        if c:
            self.bot_creds = St2UserToken(c)
            return True
        c = self.api_auth.get("key")
        if c:
            self.bot_creds = St2ApiKey(c)
            return True
        c = self.api_auth.get("user")
        if c:
            self.bot_creds = St2UserCredentials(
                c.get('name'),
                c.get('password')
            )
            return True
        LOG.warning("Failed to find any valid st2 credentials for the bot.")
        return False
