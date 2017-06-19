# coding:utf-8
import json
import logging
import requests
from urllib.parse import urlparse, urljoin
from requests.auth import HTTPBasicAuth

LOG = logging.getLogger(__name__)


class St2PluginAuth(object):
    """
    Helper to manage API key or user token authentication with the stackstorm API
    """
    def __init__(self, st2config):
        self.st2config = st2config
        self.base_url = st2config.base_url
        self.api_url = st2config.api_url
        self.auth_url = st2config.auth_url
        self.api_version = st2config.api_version

        self.api_key = st2config.api_auth.get('key')
        self.token = st2config.api_auth.get('token')
        tmp = st2config.api_auth.get('user')
        self.username = None
        self.password = None

        if tmp:
            self.username = tmp.get('name')
            self.password = tmp.get('password')

    def auth_method(self, name=None):
        """
        @name - the client that will use the returned authentication data
        Return the appropriate authentication method to use with an API key or User token.
        """
        client = {
            "requests": {"api_key": 'St2-Api-Key', "token": 'X-Auth-Token'},
            "st2client": {"api_key": 'api_key', "token": 'token'},
            "st2": {"api_key": "--api-key", "token": "--token"}
        }
        _kwargs = {}
        if self.api_key:
            _kwargs = {client[name]["api_key"]: self.api_key}
        if self.token:
            _kwargs = {client[name]["token"]: self.token}
        return _kwargs

    def valid_credentials(self):
        """
        Attempt to access API endpoint '<stackstorm api host>/'

        Check if the credentials a valid to access stackstorm API
        Returns: True if access is permitted and false if access fails.
        """
        add_headers = self.auth_method("requests")
        r = self._http_request('GET', self.api_url, '/', headers=add_headers)
        if r.status_code in [200]:
            return True
        LOG.info('API response to token = {} {}'.format(r.status_code, r.reason))
        return False

    def renew_token(self):
        """
        Token renew:
            POST with Content type JSON and Basic Authorisation to AUTH /tokens endpoint
        Renew user token used to query Stackstorm's API end point.
        """
        if self.username and self.password:
            auth = HTTPBasicAuth(self.username, self.password)

            r = self._http_request('POST', self.auth_url, "/{}/tokens".format(self.api_version),
                                   auth=auth)
            if r.status_code == 201:  # created.
                auth_info = r.json()
                self.token = auth_info["token"]
                LOG.info("Received new token %s" % self.token)
            else:
                LOG.warning('Failed to get new user token. {} {}'.format(r.status_code, r.reason))
        else:
            LOG.warning("Unable to renew user token because user credentials are missing.")

    def _http_request(self, verb="GET", base="", path="/", headers={}, auth=None):
        """
        Generic HTTP call.
        """
        get_kwargs = {
            'headers': headers,
            'timeout': 5,
            'verify': False
        }

        if auth:
            get_kwargs['auth'] = auth

        o = urlparse(base)
        new_path = "{}{}".format(o.path, path)

        url = urljoin(base, new_path)
        LOG.debug("HTTP Request: {} {} {}".format(verb, url, get_kwargs))
        return requests.request(verb, url, **get_kwargs)
