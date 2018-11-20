# coding:utf-8
import json
import time
import urllib3
import logging
import requests
import sseclient

from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from st2client.client import Client
from st2client.models.action_alias import ActionAliasMatch
from st2client.models.aliasexecution import ActionAliasExecution
from urllib.parse import urlparse, urlunparse, urljoin

LOG = logging.getLogger(__name__)


def QRCode(decoratee):
    """
    Decorator used to extract OTP from ChatOps command
    """
    print("Initialisation of QRCode OTP")
    def decorate(self, *args, **kwargs):
        print("Calling '{}' for QRCode decorator.".format(decoratee.__name__))
        return decoratee(self, *args, **kwargs)
        # Get access to QRCode store backend.


def RBACCredentials(decoratee):
    """
    Decorator used to lookup RBAC credentials or errbot service credentials.
    """
    print("Initialisation of RBAC Credentials")
    def decorate(self, *args, **kwargs):
        # get bot credentials
        # get access to secrets store backend.
        print("Calling '{}' with RBAC Credentials".format(decoratee.__name__))
        return decoratee(self, *args, **kwargs)
    return decorate


class St2UserCredentials(object):
    def __init__(self, username=None, password=None):
        self.username = None
        self.password = None
        if username:
            self.username = username
        if password:
            self.password = password

    def requests(self):
        return HTTPBasicAuth(self.username, self.password)

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


class St2PluginAuth(object):
    """
    Helper to manage API key or user token authentication with the stackstorm API
    """
    def __init__(self, st2config):
        self.cfg = st2config
        self.verify_cert = st2config.verify_cert
        if self.verify_cert is False:
            urllib3.disable_warnings()

    @RBACCredentials
    def validate_credentials(self, credentials):
        """
        Attempt to access API endpoint.

        Check if the credentials are valid to access stackstorm API
        Returns: True if access is permitted and false if access fails.
        """
        add_headers = credentials.requests()
        r = self._http_request('GET', self.cfg.api_url, '/', headers=add_headers)
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

            r = self._http_request('POST', self.cfg.auth_url, "/tokens", auth=auth)
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
            'verify': self.verify_cert
        }

        if auth:
            get_kwargs['auth'] = auth

        o = urlparse(base)
        new_path = "{}{}".format(o.path, path)

        url = urljoin(base, new_path)
        LOG.debug("HTTP Request: {} {} {}".format(verb, url, get_kwargs))
        return requests.request(verb, url, **get_kwargs)


class St2PluginAPI(object):
    stream_backoff = 10
    authenticate_backoff = 10

    def __init__(self, st2config):
        self.cfg = st2config
        self.st2auth = St2PluginAuth(st2config)
        if self.cfg.verify_cert is False:
            urllib3.disable_warnings()

    @RBACCredentials
    def actionalias_help(self, pack=None, filter=None, limit=None, offset=None):
        """
        Call StackStorm API for action alias help.
        """
        # curl -v -H "X-Auth-Token: $ST2_AUTH_TOKEN"
        # -H 'Content-Type: application/json'
        # -XGET localhost:9101/v1/actionalias/help -d '{}'

        # TODO: Replace this function once help is implemented in st2client library.
        url = "/".join([self.cfg.api_url, "actionalias/help"])

        params = {}
        if pack is not None:
            params["pack"] = pack
        if filter is not None:
            params["filter"] = filter
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        # TODO: Fetch bot credentials for action-alias call. (This may change if filtering by user is implemented on the st2 api side)
        headers = self.st2auth.auth_method("requests")
        r = requests.get(url, headers=headers, params=params, verify=self.cfg.verify_cert)
        if r.status_code == requests.codes.ok:
            return r.json().get("helpstrings", [])
        else:
            raise r.raise_for_status()

    def _baseurl(self, url):
        tmp = urlparse(url)
        return urlunparse((tmp.scheme, tmp.netloc, "", None, None, None))

    @RBACCredentials
    def match(self, text):
        auth_kwargs = self.st2auth.auth_method("st2client")
#        auth_kwargs['debug'] = False

        base_url = self._baseurl(self.cfg.api_url)

        LOG.debug("Create st2 client with {} {} {}".format(
            base_url,
            self.cfg.api_url,
            auth_kwargs)
        )

        st2_client = Client(
            base_url=base_url,
            api_url=self.cfg.api_url,
            **auth_kwargs
        )

        alias_match = ActionAliasMatch()
        alias_match.command = text

        try:
            return st2_client.managers['ActionAlias'].match(alias_match)
        except HTTPError as e:
            if e.response is not None and e.response.status_code == 400:
                LOG.info("No match found - {}".format(str(e)))
            else:
                LOG.error("HTTPError {}".format(str(e)))
        except Exception as e:
                LOG.error("Unexpected error {}".format(e))
        return None

    @QRCode
    @RBACCredentials
    def execute_actionalias(self, action_alias, representation, msg, backend=None):
        """
        @action_alias: the st2client action_alias object.
        @representation: the st2client representation for the action_alias.
        @msg: errbot message.
        """
        auth_kwargs = self.st2auth.auth_method("st2client")

        base_url = self._baseurl(self.cfg.api_url)
        LOG.debug("Create st2 client with {} {} {}".format(
            base_url,
            self.cfg.api_url,
            auth_kwargs)
        )

        st2_client = Client(
            base_url=base_url,
            api_url=self.cfg.api_url,
            **auth_kwargs
        )

        execution = ActionAliasExecution()
        execution.name = action_alias.name
        execution.format = representation
        execution.command = msg.body
        if msg.is_direct is False:
            execution.notification_channel = str(msg.to)
            execution.source_channel = str(msg.to)
        else:
            execution.notification_channel = str(msg.frm)
            execution.source_channel = str(msg.frm)

        execution.notification_route = 'errbot'
        execution.user = backend.get_username(msg)

        LOG.debug("Execution: {}".format([
            execution.command,
            execution.format,
            execution.name,
            execution.notification_channel,
            execution.notification_route,
            execution.source_channel,
            execution.user])
        )

        action_exec_mgr = st2_client.managers['ActionAliasExecution']
        execution = action_exec_mgr.create(execution)

        try:
            ret_msg = execution.message
            LOG.debug("Execution Result: {}\nMessage: {}".format(
                execution.execution,
                execution.message)
            )
        except AttributeError as e:
            ret_msg = ""
        return ret_msg

    def st2stream_listener(self, callback=None):
        """
        Listen for events passing through the stackstorm bus
        """
        LOG.info("*** Starting stream listener ***")

        def listener(callback=None):
            headers = self.st2auth.auth_method("requests")
            LOG.debug("authentication headers {}".format(headers))

            headers.update({'Accept': 'text/event-stream'})
            with requests.Session() as session:
                response = session.get(
                    "".join([self.cfg.stream_url, "/stream"]),
                    headers=headers,
                    stream=True,
                    verify=self.cfg.verify_cert
                )
                if response.status_code >= 400:
                    raise HTTPError("HTTP Error {} ({})".format(
                        response.reason,
                        response.status_code
                    ))
                client = sseclient.SSEClient(response)
                for event in client.events():
                    data = json.loads(event.data)
                    if event.event in ["st2.announcement__errbot"]:
                        LOG.debug("*** Errbot announcement event detected! ***\n{}\n".format(event))
                        p = data["payload"]
                        callback(
                            p.get('message'),
                            p.get('user'),
                            p.get('channel'),
                            p.get('whisper'),
                            p.get('extra')
                        )

        St2PluginAPI.stream_backoff = 10
        while True:
            try:
                listener(callback)
            except TypeError as err:
                LOG.critical(
                    "St2 stream listener - Type Error: {}."
                    "Backing off {} seconds.".format(err, St2PluginAPI.backoff))
            except Exception as err:
                LOG.critical(
                    "St2 stream listener - An error occurred: {} {}."
                    "Backing off {} seconds.".format(type(err), err, St2PluginAPI.backoff)
                )
            time.sleep(St2PluginAPI.backoff)

    @RBACCredentials
    def validate_credentials(self):
        """
        A wrapper method to check for API access authorisation and refresh expired user token.
        """
        def backoff(wait_time):
            if wait_time > 0:
                LOG.info("Backing off {} seconds.".format(backoff))
                time.sleep(wait_time)

        St2PluginAPI.authenticate_backoff = 10
        try:
            if not self.st2auth.valid_credentials():
                self.st2auth.renew_token()
                St2PluginAPI.authenticate_backoff = 0
        except requests.exceptions.HTTPError as e:
            LOG.error("Error while validating credentials {} ({}).".format(e.reason, e.code))
        except Exception as e:
            LOG.exception("An unexpected error has occurred.")
            backoff(St2PluginAPI.authenticate_backoff)
