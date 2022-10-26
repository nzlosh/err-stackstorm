# coding:utf-8
import abc
import logging
from urllib.parse import urljoin, urlparse

import requests

from errst2lib.authentication_controller import BotPluginIdentity
from errst2lib.credentials_adapters import St2ApiKey, St2UserCredentials, St2UserToken
from errst2lib.errors import SessionInvalidError

LOG = logging.getLogger("errbot.plugin.st2.auth_handler")


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
            "standalone": StandaloneAuthHandler,
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
        self, verb="GET", base="", path="/", headers={}, payload=None, auth=None, timeout=5
    ):
        """
        Generic HTTP call.
        """
        get_kwargs = {"headers": headers, "timeout": timeout, "verify": self.cfg.verify_cert}

        if auth:
            get_kwargs["auth"] = auth

        if payload is not None:
            get_kwargs["json"] = payload

        o = urlparse(base)
        new_path = "{}{}".format(o.path, path)

        url = urljoin(base, new_path)
        # WARNING: Sensitive security information will be logged, uncomment only when necessary.
        # LOG.debug("HTTP Request: {} {} {}".format(verb, url, get_kwargs))
        return requests.request(verb, url, **get_kwargs)


class StandaloneAuthHandler(BaseAuthHandler):
    """
    Standalone authentication handler will only use the stackstorm authentication credentials
    provided in the errbot configuration for all stackstorm api calls.
    """

    def __init__(self, cfg, opts=""):
        self.cfg = cfg

    def pre_execution_authentication(self, accessctl, chat_user):
        """
        Fetch the bot token.
        :param: accessctl - Authentication Controller
        :param: chat_user - Not used in the context of Standalone authentication.
        """
        # TODO: FIXME: passing by reference to call itself isn't ideal, refactor!
        return accessctl.get_token_by_userid(accessctl.bot.internal_identity)

    def authenticate_user(self, st2_creds):
        """
        Validate the supplied Stackstorm user/password against the API.
        Returns a StackStorm token on successful authentication otherwise False.
        """
        response = self._http_request(
            "POST",
            self.cfg.auth_url,
            path="/tokens",
            headers=st2_creds.requests(),
            payload={"ttl": self.cfg.user_token_ttl},
        )
        if response.status_code in [requests.codes.created]:
            return St2UserToken(response.json().get("token"))
        else:
            LOG.info("API response to token = {} {}".format(response.status_code, response.reason))
        return False

    def authenticate_token(self, st2_creds):
        """
        Validate the supplied StackStorm Token against the API.
        Returns the token if validation was successful otherwise False.
        """
        token = False

        response = self._http_request(
            "GET", self.cfg.auth_url, path="/token/validate", headers=st2_creds.requests()
        )

        if response.status_code in [requests.codes.created]:
            token = response.json().get("token", False)
            if token:
                token = St2UserToken(token)
            else:
                LOG.warning("Token not found in reponse {}".format(response))
        else:
            LOG.info("API response to token = {} {}".format(response.status_code, response.reason))

        return token

    def authenticate_key(self, st2_creds):
        """
        Authenicate against StackStorm API using the provided API Key.
        """
        api_key = False

        response = self._http_request(
            "GET", self.cfg.api_url, path="/", headers=st2_creds.requests()
        )

        if response.status_code in [requests.codes.ok]:
            # Since the API Key is valid, return it to be used for requests.
            api_key = st2_creds

        return api_key

    def authenticate(self, chat_user=None, st2_creds=None, bot_creds=None):
        """
        param: chat_user - the chat backend user id.
        param: st2_creds - the StackStorm credentials to be validated.
        param: bot_creds - not used, but present to have the same signature as other AuthHandlers.
        Return a StackStorm token on successful authenticate otherwise False.
        """
        token = None
        if isinstance(st2_creds, St2UserCredentials):
            token = self.authenticate_user(st2_creds)
        if isinstance(st2_creds, St2UserToken):
            token = self.authenticate_token(st2_creds)
        if isinstance(st2_creds, St2ApiKey):
            token = self.authenticate_key(st2_creds)
        if token is False:
            LOG.warning("Failed to authenticate bot credentials against StackStorm API.")
        if token is None:
            token = False
            LOG.warning(
                "Unsupported st2 authentication object [{}] {}.".format(type(st2_creds), st2_creds)
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

    def __init__(self, cfg, opts=""):
        self.cfg = cfg

    def pre_execution_authentication(self, accessctl, chat_user):
        """
        TODO: Docstring
        """
        # TODO: FIXME: refactor to correct circular dependencies.
        bot_token = accessctl.get_token_by_userid(accessctl.bot.internal_identity)
        user_token = self.authenticate(chat_user, bot_creds=bot_token)
        if user_token:
            session = accessctl.create_session(chat_user, "")
            accessctl.set_token_by_session(session.id(), user_token)
        return user_token

    def fetch_user_token(self, accessctl, user):
        """
        Returns the session associated with the user.
        """
        if isinstance(user, BotPluginIdentity):
            user_id = user.name
        else:
            bot_id = accessctl.to_userid(user)
            bot_session = self.sessions.get_by_userid(bot_id)
            bot_token = self.sessions.get_token_by_session(bot_session)
            user_id = self.bot.chatbackend.normalise_user_id(user)

        session = self.sessions.get_by_userid(user_id)
        if session is False:
            self.bot.cfg.auth_handler.authenticate(user_id, bot_token)
            raise SessionInvalidError
        return session

    def authenticate_user(self, creds, bot_creds):
        """
        This method is not available for Server Side authentication.
        """
        raise NotImplementedError

    def authenticate_token(self, creds, bot_creds):
        """
        Request StackStorm user token on behalf of chat user using bot's user token
        """
        return self._request_user_token(creds, bot_creds)

    def authenticate_key(self, creds, bot_creds):
        """
        Request StackStorm user token on behalf of chat user using bot's api key
        """
        return self._request_user_token(creds, bot_creds)

    def _request_user_token(self, chat_user, bot_creds):
        """
        TODO: Docstring
        """
        token = False
        response = self._http_request(
            "GET",
            self.cfg.auth_url,
            path="/tokens/validate",
            headers=bot_creds.requests(),
            payload={"user": chat_user},
        )
        if response == requests.codes.ok:
            token = response.json().get("token", False)
            if token is not False:
                token = St2UserToken(token)
        return token

    def authenticate(self, chat_user=None, st2_creds=None, bot_creds=None):
        """
        bot_creds must be valid to fetch a token on behalf of the chat_user.
        st2_creds are not used.
        """
        token = None
        if isinstance(bot_creds, St2UserCredentials):
            token = self.authenticate_user(chat_user, bot_creds)
        if isinstance(bot_creds, St2UserToken):
            token = self.authenticate_token(chat_user, bot_creds)
        if isinstance(bot_creds, St2ApiKey):
            token = self.authenticate_key(chat_user, bot_creds)
        if token is False:
            LOG.warning("Failed to authenticate bot credentials against StackStorm API")
        if token is None:
            token = False
            LOG.warning(
                "Unsupported st2 authentication object {} - '{}'".format(type(bot_creds), bot_creds)
            )
        return token


class ClientSideAuthHandler(BaseAuthHandler):
    """
    Client side authentication handler will use the configured errbot credentials to query
    StackStorm credentials supplied via the authentication login page.  If the credentials are
    successfully validated, the returned token is cached by errbot.  Authenticated chat users will
    be looked up in the session manager to fetch their StackStorm token with each call to the
    StackStorm API.
    """

    def __init__(self, cfg, opts):
        self.cfg = cfg
        self.url = opts.get("url", "")

    def pre_execution_authentication(self, accessctl, chat_user):
        """
        Fetch the chat user's st2 token.  A valid session must exist for the token to be fetched.
        accessctl:  The bot's access controller used to lookup the session based on the chat user.
        chat_user:  The chat_user number to lookup.
        """
        # TODO: FIXME: passing by reference to call itself isn't ideal, refactor!
        user_session = accessctl.get_session(chat_user)
        if user_session:
            user_session.is_expired()
        return accessctl.get_token_by_session(user_session.id())

    def authenticate_user(self, creds, bot_creds):
        """
        Validate supplied credetials with StackStorm
        """
        response = self._http_request(
            "POST",
            self.cfg.auth_url,
            path="/tokens",
            headers=creds.requests(),
            payload={"ttl": self.cfg.user_token_ttl},
        )
        if response.status_code in [requests.codes.created]:
            return St2UserToken(response.json().get("token"))
        else:
            LOG.info("API response to token = {} {}".format(response.status_code, response.reason))
        return False

    def authenticate_token(self, creds, bot_creds):
        """
        TODO: Docstring
        """
        token = False
        response = self._http_request(
            "GET",
            self.cfg.auth_url,
            path="/tokens/validate",
            headers=bot_creds.requests(),
            payload=creds.st2client(),
        )
        if response == requests.codes.ok:
            token = response.json().get("token", False)
            if token is not False:
                token = St2UserToken(token)
        return token

    def authenticate_key(self, creds, bot_creds):
        """
        Use StackStorm API to validate the API key is valid.
        """
        api_key = False
        response = self._http_request("GET", self.cfg.api_url, path="/", header=creds.requests())
        if response.status_code in [requests.codes.ok]:
            # Since the API Key is valid, return it to be used for requests.
            api_key = creds

        return api_key

    def authenticate(self, chat_user=None, st2_creds=None, bot_creds=None):
        token = None
        if isinstance(st2_creds, St2UserCredentials):
            token = self.authenticate_user(st2_creds, bot_creds)
        if isinstance(st2_creds, St2UserToken):
            token = self.authenticate_token(st2_creds, bot_creds)
        if isinstance(st2_creds, St2ApiKey):
            token = self.authenticate_key(st2_creds, bot_creds)
        if token is False:
            LOG.warning("Failed to authenticate user credentials against StackStorm API")
        if token is None:
            token = False
            LOG.warning(
                "Unsupported st2 authentication object [{}] {}.".format(type(st2_creds), st2_creds)
            )
        return token
