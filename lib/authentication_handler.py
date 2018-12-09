# coding:utf-8
import abc
import requests
import logging
from urllib.parse import urlparse, urljoin
from lib.credentials_adapters import St2UserCredentials, St2UserToken, St2ApiKey

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
    def authenticate(self, user_creds, bot_creds):
        raise NotImplementedError


class BaseAuthHandler(AbstractAuthHandler):
    def __init__(self, chat_user=None, user_creds=None, bot_creds=None):
        self.chat_user = chat_user
        self.user_creds = user_creds
        self.bot_creds = bot_creds

    def _http_request(
        self,
        verb="GET",
        base="",
        path="/",
        headers={},
        payload=None,
        auth=None,
        timeout=5
    ):
        """
        Generic HTTP call.
        """
        get_kwargs = {
            'headers': headers,
            'timeout': timeout,
            'verify': self.cfg.verify_cert
        }

        if auth:
            get_kwargs['auth'] = auth

        if payload is not None:
            get_kwargs["json"] = payload

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
    def __init__(self, cfg):
        self.cfg = cfg

    def authenticate_user(self, st2_creds):
        add_headers = st2_creds.requests()
        response = self._http_request(
            'POST',
            self.cfg.auth_url,
            path="/tokens",
            headers=add_headers,
            payload={"ttl": 86400}
        )
        if response.status_code in [requests.codes.created]:
            return St2UserToken(response.json().get("token"))
        else:
            LOG.info('API response to token = {} {}'.format(response.status_code, response.reason))
        return False

    def authenticate_token(self, st2_creds):
        """

        """
        token = False

        response = self._http_request(
            "GET",
            path="/api/v1/token/validate",
            headers=st2_creds.requests()
        )

        if response.status_code in [requests.codes.created]:
            token = response.json().get("token", False)
            if token:
                token = St2UserToken(token)
            else:
                LOG.warning("Token not found in reponse {}".foramt(resposne))
        else:
            LOG.info('API response to token = {} {}'.format(response.status_code, response.reason))

        return token

    def authenticate_key(self, st2_creds):
        """
        Authenicate against StackStorm API using API Key.
        """
        api_key = False

        response = self._http_request(
            "GET",
            path="/api/v1/key/check",
            headers=st2_creds.request()
        )

        if response.status_code in [requests.codes.created]:
            api_key = response.token

        return api_key

    def authenticate(self, chat_user=None, st2_creds=None, bot_creds=None):
        """
        param: chat_user -
        param: st2_creds -
        param: bot_creds - not used, but present to have the same signature as other AuthHandlers.
        """
        token = False
        if isinstance(st2_creds, St2UserCredentials):
            token = self.authenticate_user(st2_creds)
        if isinstance(st2_creds, St2UserToken):
            token = self.authenticate_token(st2_creds)
        if isinstance(st2_creds, St2ApiKey):
            token = self.authenticate_key(st2_creds)
        if token is False:
            LOG.warning(
                "Unsupported st2 authentication object [{}] {}.".format(
                    type(st2_creds),
                    st2_creds
                )
            )
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
    def __init__(self, cfg):
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

    def authenticate(self, chat_user=None, st2_creds=None, bot_creds=None):
        token = False
        if isinstance(st2_creds, St2UserCredentials):
            token = self.authenticate_user(st2_creds, bot_creds)
        if isinstance(st2_creds, St2UserToken):
            token = self.authenticate_token(st2_creds, bot_creds)
        if isinstance(st2_creds, St2ApiKey):
            token = self.authenticate_key(st2_creds, bot_creds)
        if token is False:
            LOG.warning(
                "Unsupported st2 authentication object {} - '{}'".format(type(st2_creds), st2_creds)
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
    def __init__(self, cfg):
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

    def authenticate(self, chat_user=None, st2_creds=None, bot_creds=None):
        token = False
        if isinstance(st2_creds, St2UserCredentials):
            token = self.authenticate_user(st2_creds, bot_creds)
        if isinstance(st2_creds,  St2UserToken):
            token = self.authenticate_token(st2_creds, bot_creds)
        if isinstance(st2_creds, St2ApiKey):
            token = self.authenticate_key(st2_creds, bot_creds)
        if token is False:
            LOG.warning(
                "Unsupported st2 authentication object [{}] {}.".format(type(st2_creds), st2_creds)
            )
        return token
