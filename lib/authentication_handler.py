# coding:utf-8
import abc
import requests
import logging
from requests.auth import HTTPBasicAuth
from lib.stackstorm_api import StackStormAPI

LOG = logging.getLogger(__name__)


# Strategy pattern to vary authentication behaviour amoung the authentication handler classes.
class AuthBase(object):
	def _http_request(self, verb="GET", base="", path="/", headers={}, auth=None):
	"""
	Generic HTTP call.
	"""
	get_kwargs = {
		'headers': headers,
		'timeout': 5,
		'verify': self.verify_cert
	}

	if auth:
		get_kwargs['auth'] = auth

	o = urlparse(base)
	new_path = "{}{}".format(o.path, path)

	url = urljoin(base, new_path)
	LOG.debug("HTTP Request: {} {} {}".format(verb, url, get_kwargs))
	return requests.request(verb, url, **get_kwargs)

class AuthUserStandalone(AuthBase):
    def __init__(self, cfg, creds):
        add_headers = credentials.requests()
        add_headers["X-Authenticate"] = add_headers["Authorization"]
        response = self._http_request('GET', cfg.api_url, '/api/v1/auth', headers=add_headers)
        if response.status_code in [200]:
            return True
        else:
			
        LOG.info('API response to token = {} {}'.format(response.status_code, response.reason))
        return False
        # set X-Authenticate: username/password
        # connect to api/v1/auth
        # if return 200 return (0, Token)
        # else return (x, ErrorMessage)
        raise NotImplementedError


class AuthUserProxied(object):
    def __init__(self, cfg, creds, bot_creds):
        raise NotImplementedError


class ValidateTokenStandalone(object):
    def __init__(self, cfg, creds):
        # connect to api/v1/token/validate
        # if return http 200 return (0, Token)
        # else return (x, ErrorMessage)
        raise NotImplementedError


class ValidateTokenProxied(object):
    def __init__(self, cfg, creds, bot_creds):
        raise NotImplementedError


class ValidateApiKeyStandalone(object):
    def __init__(self, cfg, creds):
        # connect to api/v1/token/validate
        # if return http 200 return (0, ApiKey)
        # else return (x, ErrorMessage)
        raise NotImplementedError


class ValidateApiKeyProxied(object):
    def __init__(self, cfg, creds, bot_creds):
        raise NotImplementedError


class AbstractAuthHandlerFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def instantiate(self, handler_type):
        raise NotImplementedError


class AuthHandlerFactory(AbstractAuthHandlerFactory):
    def __init__(self):
        pass

    @staticmethod
    def instantiate(handler_type):
        if handler_type == "serverside":
            return ServerSideAuthHandler
        elif handler_type == "clientside":
            return ClientSideAuthHandler
        else:
            return StandaloneAuthHandler


class AbstractAuthHandler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, kwconf={}):
        raise NotImplementedError

    @abc.abstractmethod
    def authenticate(self, creds, bot_creds):
        raise NotImplementedError


class StandaloneAuthHandler(AbstractAuthHandler):
    """
    Standalone authentication handler will only use the stackstorm authentication credentials
    provided in the errbot configuration for all stackstorm api calls.
    """
    def __init__(self, cfg=None):
        self.cfg = cfg

    def authenticate(self, creds, bot_creds=None):
        """
        param: bot_creds - not used, but present to have the same signature as other AuthHandlers.
        """
        if isinstance(creds, St2UserCredentials):
            return AuthUserStandalone(creds)
        if isinstance(creds, St2UserToken):
            return ValidateTokenStandalone(creds)
        if isinstance(creds, St2ApiKey):
            return ValidateApiKeyStandalone(creds)
        LOG.warning("Unsupported st2 authentication object {} - '{}'".format(type(creds), creds))
        return False


class ServerSideAuthHandler(AbstractAuthHandler):
    """
    Server side authentication handler is used when StackStorm maintains a list of chat user
    accounts and associates them with a StackStorm login accuont.

    err-stackstorm's authentication credentials must be configured as a service in StackStorm.
    This will permit err-stackstorm to request a user token on behalf of the chat user account.

    StackStorm will return a user token for a valid user and err-stackstorm will cache this token
    for subsequence action-alias executions by the corresponding chat user account.
    """
    def __init__(self, cfg=None):
        self.cfg = cfg

    def authenticate(self, creds, bot_creds):
        if isinstance(creds, St2UserCredentials):
            return AuthUserProxied(creds, bot_creds)
        if isinstance(creds, St2UserToken):
            return ValidateTokenProxied(creds, bot_creds)
        if isinstance(creds, St2ApiKey):
            return ValidateApiKeyProxied(creds, bot_creds)
        LOG.warning("Unsupported st2 authentication object {} - '{}'".format(type(creds), creds))
        return False


class ClientSideAuthHandler(AbstractAuthHandler):
    """
    Client side authentication handler will use the configured errbot credentials to query
    StackStorm credentials supplied via the authentication login page.  If the credentials are
    successfully validated, the returned token is cached by errbot.  Authenticated chat users will
    be looked up in the session manager to fetch their StackStorm token with each call to the
    StackStorm API.
    """
    def __init__(self, cfg=None):
        self.cfg = cfg

    def authenticate_user(self, creds, bot_creds, st2api):
        auth = AuthUserProxied(self.cfg, creds, bot_creds)

    def authenticate_token(self, creds, bot_creds):
        st2api = StackStormAPI(self.cfg)
        ValidateTokenProxied(creds, bot_creds)
        st2api.validate_credentials(creds)

    def authenticate_key(self, creds, bot_creds):
        auth = AuthUserProxied(self.cfg, creds, bot_creds)
        ValidateApiKeyProxied(creds, bot_creds)

    def authenticate(self, creds, bot_creds):
        token = False
        if isinstance(creds, St2UserCredentials):
            token = self.authenticate_user(cred, bot_creds)
        if isinstance(creds,  St2UserToken):
            token = self.authenticate_token(creds, bot_creds)
        if isinstance(creds, St2ApiKey):
            token self.authenticate_key(cred, bot_creds)
        if token is False:
            LOG.warning("Unsupported st2 authentication object {} - '{}'".format(type(creds), creds))
        return token
