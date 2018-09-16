# coding:utf-8
import json
import time
import logging
import requests
import sseclient
import urllib3

from urllib.parse import urlparse, urlunparse
from lib.st2pluginauth import St2PluginAuth
from st2client.client import Client
from st2client.models.action_alias import ActionAliasMatch
from st2client.models.aliasexecution import ActionAliasExecution
from requests.exceptions import HTTPError

LOG = logging.getLogger("{}".format(__name__))


class St2PluginAPI(object):
    def __init__(self, st2config):
        self.cfg = st2config
        self.st2auth = St2PluginAuth(st2config)
        if self.cfg.verify_cert is False:
            urllib3.disable_warnings()

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

        headers = self.st2auth.auth_method("requests")
        r = requests.get(url, headers=headers, params=params, verify=self.cfg.verify_cert)
        if r.status_code == requests.codes.ok:
            return r.json().get("helpstrings", [])
        else:
            raise r.raise_for_status()

    def _baseurl(self, url):
        tmp = urlparse(url)
        return urlunparse((tmp.scheme, tmp.netloc, "", None, None, None))

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
            ret_msg = "Something is happening ... "
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
                        message = data["payload"].get('message')
                        user = data["payload"].get('user')
                        channel = data["payload"].get('channel')
                        whisper = data["payload"].get('whisper')
                        extra = data["payload"].get('extra')

                        callback(whisper, message, user, channel, extra)

        backoff = 10
        while True:
            try:
                listener(callback)
            except TypeError as err:
                LOG.critical(
                    "St2 stream listener - Type Error: {}."
                    "Backing off {} seconds.".format(err, backoff))
            except Exception as err:
                LOG.critical(
                    "St2 stream listener - An error occurred: {} {}."
                    "Backing off {} seconds.".format(type(err), err, backoff)
                )
            time.sleep(backoff)

    def validate_credentials(self):
        """
        A wrapper method to check for API access authorisation and refresh expired user token.
        """
        def backoff(wait_time):
            if wait_time > 0:
                LOG.info("Backing off {} seconds.".format(backoff))
                time.sleep(wait_time)

        timeout = 10
        try:
            if not self.st2auth.valid_credentials():
                self.st2auth.renew_token()
                timeout = 0
        except requests.exceptions.HTTPError as e:
            LOG.error("Error while validating credentials {} ({}).".format(e.reason, e.code))
        except Exception as e:
            LOG.exception("An unexpected error has occurred.")
            backoff(timeout)
