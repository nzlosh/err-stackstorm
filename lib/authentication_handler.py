# coding:utf-8
import abc
import requests
import logging
from urllib.parse import urlparse, urljoin
from lib.credentials_adapaters import St2UserCredentials, St2UserToken, St2ApiKey

LOG = logging.getLogger(__name__)


class AbstractAuthHandlerFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def instantiate(self, handler_type):
        raise NotImplementedError


class AuthHandlerFactory(AbstractAuthHandlerFactory):
    def __init__(self):
        pass

    @staticmethod
    def instantiate(handler_type):
        handler_types = {
            "serverside": ServerSideAuthHandler,
            "clientside": ClientSideAuthHandler,
            "standalone": StandaloneAuthHandler
        }
        if handler_type not in handler_types:
            LOG.warning("Default to Standalone authentication, {} unspported.".format(handler_type))
        return handler_types.get(handler_type, StandaloneAuthHandler)


class AbstractAuthHandler(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, kwconf={}):
        raise NotImplementedError

    @abc.abstractmethod
    def authenticate(self, creds, bot_creds):
        raise NotImplementedError


class BaseAuthHandler(AbstractAuthHandler):
    def __init__(self, cfg, creds, bot_creds=None):
        self.cfg = cfg
        self.creds = creds
        self.bot_creds = bot_creds

    def _http_request(self, verb="GET", base="", path="/", headers={}, auth=None, timeout=5):
        """
        Generic HTTP call.
        """
        get_kwargs = {
            'headers': headers,
            'timeout': timeout,
            'verify': self.verify_cert
        }

        if auth:
            get_kwargs['auth'] = auth

        o = urlparse(base)
        new_path = "{}{}".format(o.path, path)

        url = urljoin(base, new_path)
        LOG.debug("HTTP Request: {} {} {}".format(verb, url, get_kwargs))
        return requests.request(verb, url, **get_kwargs)


class StandaloneAuthHandler(BaseAuthHandler):
    """
    Standalone authentication handler will only use the stackstorm authentication credentials
    provided in the errbot configuration for all stackstorm api calls.
    """
    def __init__(self, cfg=None):
        self.cfg = cfg

    def authenticate_user(self, creds):
        st2_endpoint = "/api/v1/auth"
        add_headers = creds.requests(st2_x_auth=True)
        response = self._http_request(
            'GET',
            self.cfg.api_url,
            path=st2_endpoint,
            headers=add_headers
        )
        if response.status_code in [200]:
            return response.token
        else:
            LOG.info('API response to token = {} {}'.format(response.status_code, response.reason))
        return False

    def authenticate_token(self, creds):
        st2_endpoint = "/api/v1/token/validate"
        add_headers = creds.requests()
        response = self._http_request("GET", path=st2_endpoint, headers=add_headers)
        if response.status_code == 200:
            return response.token
        else:
            return False

    def authenticate_key(self, creds):
        st2_endpoint = "/api/v1/key/check"
        add_headers = creds.request()
        response = self._http_request("GET", path=st2_endpoint, headers=add_headers)
        if response.status_code == 200:
            return response.token
        else:
            return False

    def authenticate(self, creds, bot_creds=None):
        """
        param: bot_creds - not used, but present to have the same signature as other AuthHandlers.
        """
        token = False
        if isinstance(creds, St2UserCredentials):
            token = self.authenticate_user(creds)
        if isinstance(creds, St2UserToken):
            token = self.authenticate_token(creds)
        if isinstance(creds, St2ApiKey):
            token = self.authenticate_key(creds)
        if token is False:
            LOG.warning("Unsupported st2 authentication object [{}] {}.".format(type(creds), creds))
        return token


class ServerSideAuthHandler(BaseAuthHandler):
    """
    Server side authentication handler is used when StackStorm maintains a list of chat user
    accounts and associates them with a StackStorm login account.

    err-stackstorm's authentication credentials must be configured as a service in StackStorm.
    This will permit err-stackstorm to request a user token on behalf of the chat user account.

    StackStorm will return a user token for a valid user and err-stackstorm will cache this token
    for subsequence action-alias executions by the corresponding chat user account.
    """
    def __init__(self, cfg=None):
        self.cfg = cfg

    def authenticate_user(self, creds, bot_creds):
        add_headers = bot_creds.requests()
        add_headers["X-Authenticate"] = add_headers["Authorization"]
        del add_headers["Authorization"]
        raise NotImplementedError

    def authenticate_token(self, creds, bot_creds):
        st2_endpoint = "/auth/v1/tokens/validate"
        # use bot_token to communicate with StackStorm API
        add_headers = bot_creds.requests()
        # Pass the supplied user token as the request payload
        payload = creds.st2client()

        response = self._http_request(
            "GET",
            path=st2_endpoint,
            headers=add_headers,
            payload=payload
        )
        if response == 200:
            return creds
        else:
            return False

    def authenticate_key(self, creds, bot_creds):
        raise NotImplementedError

    def authenticate(self, creds, bot_creds):
        token = False
        if isinstance(creds, St2UserCredentials):
            token = self.authenticate_user(creds, bot_creds)
        if isinstance(creds, St2UserToken):
            token = self.authenticate_token(creds, bot_creds)
        if isinstance(creds, St2ApiKey):
            token = self.authenticate_key(creds, bot_creds)
        if token is False:
            LOG.warning("Unsupported st2 authentication object {} - '{}'".format(
                type(creds),
                creds)
            )
        return False


class ClientSideAuthHandler(BaseAuthHandler):
    """
    Client side authentication handler will use the configured errbot credentials to query
    StackStorm credentials supplied via the authentication login page.  If the credentials are
    successfully validated, the returned token is cached by errbot.  Authenticated chat users will
    be looked up in the session manager to fetch their StackStorm token with each call to the
    StackStorm API.
    """
    def __init__(self, cfg=None):
        self.cfg = cfg

    def authenticate_user(self, creds, bot_creds):
        st2_endpoint = "/auth/v1/token"
        add_headers = creds.requests(st2_x_auth=True)
        response = self._http_request("GET", path=st2_endpoint, headers=add_headers)
        if response == 200:
            return response.token
        else:
            return False

    def authenticate_token(self, creds, bot_creds):
        st2_endpoint = "/auth/v1/tokens/validate"
        # use bot_token to communicate with StackStorm API
        add_headers = bot_creds.requests()
        # Pass the supplied user token as the request payload
        payload = creds.st2client()

        response = self._http_request(
            "GET",
            path=st2_endpoint,
            headers=add_headers,
            payload=payload
        )
        if response == 200:
            return creds
        else:
            return False

    def authenticate_key(self, creds, bot_creds):
        st2_endpoint = "/auth/v1/key"
        add_headers = creds.requests()
        response = self._http_request("GET", path=st2_endpoint, header=add_headers)

        if response == 200:
            return creds
        else:
            return False

    def authenticate(self, creds, bot_creds):
        token = False
        if isinstance(creds, St2UserCredentials):
            token = self.authenticate_user(creds, bot_creds)
        if isinstance(creds,  St2UserToken):
            token = self.authenticate_token(creds, bot_creds)
        if isinstance(creds, St2ApiKey):
            token = self.authenticate_key(creds, bot_creds)
        if token is False:
            LOG.warning("Unsupported st2 authentication object [{}] {}.".format(type(creds), creds))
        return token
