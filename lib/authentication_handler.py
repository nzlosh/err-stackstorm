# coding:utf-8
import logging
from types import SimpleNamespace
from requests.auth import HTTPBasicAuth

LOG = logging.getLogger(__name__)


# Strategy pattern to vary authentication behaviour amoung the authentication handler classes.
class St2UserCredentials(object):
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

    def requests(self):
        # Nasty hack until I find a nice way for requests to produce the header.
        return HTTPBasicAuth(self.username, self.password).__call__(
            SimpleNamespace(**{"headers":{}})
        ).headers

    def st2client(self):
        raise NotImplementedError


class St2UserToken(object):
    def __init__(self, token=None):
        self.token = None
        if token:
            self.token = token

    def requests(self):
        return {"X-Auth-Token": self.token}

    def st2client(self):
        return {"token": self.token}


class St2ApiKey(object):
    def __init__(self, apikey=None):
        self.apikey = None
        if apikey:
            self.apikey = apikey

    def requests(self):
        return {'St2-Api-Key': self.apikey}

    def st2client(self):
        return {'api_key': self.apikey}


class AuthUserStandalone(object):
    def __init__(self, username, password):
        # set X-Authenticate: username/password
        # connect to api/v1/auth
        # if return 200 return (0, Token)
        # else return (x, ErrorMessage)
        raise NotImplementedError


class AuthUserProxied(object):
    def __init__(self, username, password, bot_token):
        raise NotImplementedError


class ValidateTokenStandalone(object):
    def __init__(self, token):
        # connect to api/v1/token/validate
        # if return http 200 return (0, Token)
        # else return (x, ErrorMessage)
        raise NotImplementedError


class ValidateTokenProxied(object):
    def __init__(self, username, password, bot_token):
        raise NotImplementedError


class ValidateApiKeyStandalone(object):
    def __init__(self, api_key):
        # connect to api/v1/token/validate
        # if return http 200 return (0, ApiKey)
        # else return (x, ErrorMessage)
        raise NotImplementedError


class ValidateApiKeyProxied(object):
    def __init__(self, api_key, bot_token):
        raise NotImplementedError


class StandaloneAuthHandler(object):
    """
    Standalone authentication handler will only use the stackstorm
    authentication credentials provided in the errbot configuration
    for all stackstorm api calls.
    """
    def __init__(self):
        pass

    def authenticate(self, creds):
        if isinstance(creds, St2UserCredentials):
            return AuthUserStandalone(creds.username, creds.password)
        if isinstance(creds, St2UserToken):
            return ValidateTokenStandalone(creds.token)
        if isinstance(creds, St2ApiKey):
            return ValidateApiKeyStandalone(creds.api_key)
        LOG.warning("Unsupported st2 authentication object {} - '{}'".format(type(creds), creds))
        return False


class ProxiedAuthHandler(object):
    """
    Proxied authentication handler will use the configured errbot credentials with the
    expectation they are defined as a service in StackStorm.  Calls to the StackStorm API will
    made with cached credentials, or looked up if no credentials are currently cached.
    """
    def authenticate_user(self, username, password):
        self.user_auth = AuthUserProxied(username, password)

    def validate_token(self, token):
        self.token_validate = ValidateTokenProxied(token)

    def validate_api_key(self, api_key):
        self.api_key_validate = ValidateApiKeyProxied(api_key)


class OutOfBandsAuthHandler(object):
    """
    OutOfBands authentication handler will use the configured errbot credentials to query StackStorm
    credentials supplied via the authentication login page.  If the credentials are successfully
    validated, the returned token is cached by errbot.  Authenticated chat users will be looked up
    in the session manager to fetch their StackStorm token with each call to the StackStorm API.
    """
    def authenticate_user(self, username, password):
        self.user_auth = AuthUserProxied(username, password)

    def validate_token(self, token):
        self.token_validate = ValidateTokenProxied(token)

    def validate_api_key(self, api_key):
        self.api_key_validate = ValidateApiKeyProxied(api_key)
