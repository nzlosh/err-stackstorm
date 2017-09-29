# coding:utf-8
import six
import json
import time
import pprint
import logging
import requests
import sseclient

from st2pluginauth import St2PluginAuth
from st2client.client import Client
from st2client.models.action_alias import ActionAliasMatch
from st2client.models.aliasexecution import ActionAliasExecution
from requests.exceptions import HTTPError
LOG = logging.getLogger(__name__)


class St2PluginAPI(object):
    def __init__(self, st2config):
        self.st2config = st2config
        self.st2auth = St2PluginAuth(st2config)

    def show_help(self, pack=None, filter=None, limit=None, offset=None):
        """
        Call StackStorm API for action alias help.
        """
        # curl -v -H "X-Auth-Token: $ST2_AUTH_TOKEN"
        # -H 'Content-Type: application/json'
        # -XGET localhost:9101/v1/actionalias/help -d '{}'

        # TODO: Replace this function once hellp is implemented in st2client library.
        url = "/".join([self.st2config.api_url, self.st2config.api_version, "actionalias/help"])

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
        r = requests.get(url, headers=headers, params=params, verify=self.st2config.verify_cert)
        if r.status_code == requests.codes.ok:
            help_result = r.json().get("helpstrings", [])
            if isinstance(help_result, list) and len(help_result) == 0:
                return "No help found for the search."
            else:
                return self._format_help(help_result)
        else:
            raise r.raise_for_status()

    def _format_help(self, r):
        help_text = ""
        for help_obj in r:
            help_text += "{}{} {} - {}\n".format(
                self.st2config.bot_prefix,
                self.st2config.plugin_prefix,
                help_obj["display"],
                help_obj["description"])
        return help_text

    def match(self, text):
        auth_kwargs = self.st2auth.auth_method("st2client")
#        auth_kwargs['debug'] = False

        LOG.debug("Create st2 client with {} {} {}".format(
            self.st2config.base_url,
            self.st2config.api_url,
            auth_kwargs)
        )

        st2_client = Client(
            base_url=self.st2config.base_url,
            api_url=self.st2config.api_url,
            **auth_kwargs
        )

        alias_match = ActionAliasMatch()
        alias_match.command = text

        try:
            return st2_client.managers['ActionAlias'].match(alias_match)
        except HTTPError as e:
            if e.response is not None and e.response.status_code == 400:
                print("No match found")
            else:
                print("HTTPError %s" % e)
        return None

    def execute_actionalias(self, action_alias, representation, msg):
        """
        @action_alias: the st2client action_alias object.
        @representation: the st2client representation for the action_alias.
        @msg: errbot message.
        """
        auth_kwargs = self.st2auth.auth_method("st2client")
        LOG.debug("Create st2 client with {} {} {}".format(
            self.st2config.base_url,
            self.st2config.api_url,
            auth_kwargs)
        )

        st2_client = Client(
            base_url=self.st2config.base_url,
            api_url=self.st2config.api_url,
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
        execution.user = str(msg.frm)

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
            LOG.debug("Execution: {}\nMessage: {}".format(
                pprint.pprint(execution.execution),
                pprint.pprint(execution.message))
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
            headers.update({'Accept': 'text/event-stream'})

            with requests.Session() as session:
                response = session.get(
                    self.st2config.stream_url,
                    headers=headers,
                    stream=True,
                    verify=self.st2config.verify_cert
                )

                client = sseclient.SSEClient(response)
                for event in client.events():
                    data = json.loads(event.data)
                    if event.event in ["st2.announcement__errbot"]:
                        LOG.debug("*** Errbot announcement event detected! ***")
                        channel = data["payload"].get('channel')
                        message = data["payload"].get('message')

                        user = data["payload"].get('user')
                        whisper = data["payload"].get('whisper')
                        extra = data["payload"].get('extra')

                        callback(whisper, message, user, channel, extra)

        while True:
            try:
                listener(callback)
            except TypeError as err:
                LOG.critical("St2 stream listener - Type Error: {}".format(err))
            except Exception as err:
                backoff = 10
                LOG.critical(
                    "St2 stream listener - An error occurred: {} {}. Backing off {} seconds".format(
                        type(err),
                        err,
                        backoff
                    )
                )
                time.sleep(backoff)

    def validate_credentials(self):
        """
        A wrapper method to check for API access authorisation and refresh expired user token.
        """
        try:
            if not self.st2auth.valid_credentials():
                self.st2auth.renew_token()
        except requests.exceptions.HTTPError as e:
            LOG.error("Error while validating credentials %s (%s)" % (e.reason, e.code))
