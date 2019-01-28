# coding:utf-8
import json
import time
import urllib3
import logging
import requests
import sseclient
import traceback

from requests.exceptions import HTTPError
from st2client.client import Client
from st2client.models.action_alias import ActionAliasMatch
from st2client.models.aliasexecution import ActionAliasExecution
from urllib.parse import urlparse, urlunparse

LOG = logging.getLogger(__name__)


class ResultSet(object):
    def __init__(self, error_code=None, result=None):
        self.error_code = error_code
        self.result = result

    def OK(self, result):
        self.error_code = 0
        self.result = result

    def error(self, error_code, result):
        self.error_code = error_code
        self.result = result


class StackStormAPI(object):
    stream_backoff = 10
    authenticate_backoff = 10

    def __init__(self, cfg, accessctl):
        self.cfg = cfg
        self.accessctl = accessctl

        if self.cfg.verify_cert is False:
            urllib3.disable_warnings()

    def actionalias_help(self, pack=None, filter=None, limit=None, offset=None, st2_creds=None):
        """
        Call StackStorm API for action alias help.
        """
        # curl -v -H "X-Auth-Token: $ST2_AUTH_TOKEN"
        # -H 'Content-Type: application/json'
        # -XGET localhost:9101/v1/actionalias/help -d '{}'

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

        headers = st2_creds.requests()
        response = requests.get(url, headers=headers, params=params, verify=self.cfg.verify_cert)
        if response.status_code == requests.codes.ok:
            return response.json().get("helpstrings", [])
        else:
            response.raise_for_status()

    def _baseurl(self, url):
        tmp = urlparse(url)
        return urlunparse((tmp.scheme, tmp.netloc, "", None, None, None))

    def match(self, text, st2token):
        LOG.debug("StackStorm Token is {}".format(st2token))
        auth_kwargs = st2token.st2client()

        if LOG.level <= logging.DEBUG:
            auth_kwargs['debug'] = True

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

        resp = ResultSet()
        try:
            resp.OK(st2_client.managers['ActionAlias'].match(alias_match))
        except HTTPError as e:
            if e.response is not None and e.response.status_code == 400:
                resp.error(
                    1,
                    "st2 command '{}' not found.  View available commands with {}st2help.".format(
                        text, self.cfg.bot_prefix
                    )
                )
                LOG.info(resp.result)
            else:
                resp.error(2, "HTTPError {}".format(str(e)))
                LOG.error(resp.result)
        except Exception as e:
                resp.error(3, "Unexpected error {}".format(e))
                LOG.error(resp.result)
        return resp

    def execute_actionalias(self, action_alias, representation, msg, chat_user, st2token):
        """
        @action_alias: the st2client action_alias object.
        @representation: the st2client representation for the action_alias.
        @msg: errbot message.
        """
        auth_kwargs = st2token.st2client()

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
        execution.user = chat_user

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

    def st2stream_listener(self, callback=None, bot_identity=None):
        """
        Listen for events passing through the stackstorm bus
        """
        LOG.info("*** Starting stream listener ***")

        def listener(callback=None, bot_identity=None):
            token = self.accessctl.get_token_by_userid(bot_identity)
            headers = token.requests()
            LOG.debug("Authentication headers {}".format(headers))

            headers.update({'Accept': 'text/event-stream'})
            with requests.Session() as session:
                response = session.get(
                    "".join([self.cfg.stream_url, "/stream"]),
                    headers=headers,
                    stream=True,
                    verify=self.cfg.verify_cert
                )
                if response.raise_for_status():
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
                            p.get('whisper'),
                            p.get('message'),
                            p.get('user'),
                            p.get('channel'),
                            p.get('extra')
                        )

        StackStormAPI.stream_backoff = 10
        while True:
            try:
                listener(callback, bot_identity)
            except TypeError as err:
                LOG.critical(
                    "St2 stream listener - Type Error: {}.  "
                    "Backing off {} seconds.".format(err, StackStormAPI.stream_backoff))
            except Exception as err:
                LOG.critical(
                    "St2 stream listener - An error occurred: {} {}.  "
                    "Backing off {} seconds.".format(type(err), err, StackStormAPI.stream_backoff)
                )
                LOG.critical(traceback.print_exc())

            time.sleep(StackStormAPI.stream_backoff)
