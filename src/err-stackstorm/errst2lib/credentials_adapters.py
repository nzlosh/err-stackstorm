# coding:utf-8
import abc
import logging
from types import SimpleNamespace

from requests.auth import HTTPBasicAuth

LOG = logging.getLogger("errbot.plugin.st2.creds_adapter")


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
        return {"user": St2UserCredentials, "token": St2UserToken, "apikey": St2ApiKey}.get(
            credential_type, St2UserCredentials
        )


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

    def __repr__(self):
        return "".join([self.username, " : ", "".join(["*" for c in self.password])])

    def requests(self, st2_x_auth=False):
        # TODO: FIX: Find a cleaner way for requests to produce the header.
        headers = (
            HTTPBasicAuth(self.username, self.password)
            .__call__(SimpleNamespace(**{"headers": {}}))
            .headers
        )
        if st2_x_auth:
            headers["X-Authenticate"] = headers["Authorization"]
            del headers["Authorization"]
        return headers

    def st2client(self):
        raise NotImplementedError


class St2UserToken(AbstractCredentials):
    def __init__(self, token=None):
        self.token = None
        if token:
            self.token = token

    def __repr__(self):
        return self.token

    def requests(self):
        return {"X-Auth-Token": self.token}

    def st2client(self):
        return {"token": self.token}


class St2ApiKey(AbstractCredentials):
    def __init__(self, apikey=None):
        self.apikey = None
        if apikey:
            self.apikey = apikey

    def __repr__(self):
        return self.apikey

    def requests(self):
        return {"St2-Api-Key": self.apikey}

    def st2client(self):
        return {"api_key": self.apikey}
