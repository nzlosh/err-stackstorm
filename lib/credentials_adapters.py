# coding:utf-8
import abc
import logging
from types import SimpleNamespace
from requests.auth import HTTPBasicAuth

LOG = logging.getLogger(__name__)


class AbstractCredentialsFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def instantiate(self, credential_type=None):
        raise NotImplementedError


class CredentialsFactory(AbstractCredentialsFactory):
    def __init__(self):
        pass

    @staticmethod
    def instantiate(credential_type="user"):
        if credential_type == "token":
            return St2UserToken
        elif credential_type == "api":
            return St2ApiKey
        else:
            return St2UserCredentials


class AbstractCredentials(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, username=None, password=None):
        raise NotImplementedError

    @abc.abstractmethod
    def requests(self):
        raise NotImplementedError

    @abc.abstractmethod
    def st2client(self):
        raise NotImplementedError


class St2UserCredentials(AbstractCredentials):
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

    def requests(self):
        # Nasty hack until I find a nice way for requests to produce the header.
        return HTTPBasicAuth(self.username, self.password).__call__(
            SimpleNamespace(**{"headers": {}})
        ).headers

    def st2client(self):
        raise NotImplementedError


class St2UserToken(AbstractCredentials):
    def __init__(self, token=None):
        self.token = None
        if token:
            self.token = token

    def requests(self):
        return {"X-Auth-Token": self.token}

    def st2client(self):
        return {"token": self.token}


class St2ApiKey(AbstractCredentials):
    def __init__(self, apikey=None):
        self.apikey = None
        if apikey:
            self.apikey = apikey

    def requests(self):
        return {'St2-Api-Key': self.apikey}

    def st2client(self):
        return {'api_key': self.apikey}
