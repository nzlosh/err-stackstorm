# coding:utf-8
import json
import logging
import time
import traceback

import requests
import urllib3
from requests.exceptions import HTTPError

import sseclient

LOG = logging.getLogger("errbot.plugin.st2.st2_api")


class Result(object):
    def __init__(self, return_code=None, message=None):
        self.return_code = return_code
        self.message = message

    def OK(self, message):
        self.return_code = 0
        self.message = message

    def error(self, return_code, message):
        self.return_code = return_code
        self.message = message


class StackStormAPI(object):
    retry_delay = 10
    last_error = 0

    def __init__(self, cfg, accessctl):
        self.cfg = cfg
        self.accessctl = accessctl

        if self.cfg.verify_cert is False:
            urllib3.disable_warnings()

    def refresh_bot_credentials(self):
        LOG.warning("Bot credentials re-authentication required.")
        session_id = self.accessctl.get_session(self.accessctl.bot.internal_identity)
        self.accessctl.bot.reauthenticate_bot_credentials(session_id)

    def action_get(self, action_id, st2_creds=None):
        url = f"{self.cfg.api_url}/actions/{action_id}"
        params = {}
        headers = st2_creds.requests()
        return requests.get(url, headers=headers, params=params, verify=self.cfg.verify_cert)

    def execution_get(self, action_id, st2_creds=None):
        """
        the Inquiry ID is the same as the action execution ID that raised it
        """
        url = f"{self.cfg.api_url}/executions/{action_id}"
        params = {}
        headers = st2_creds.requests()
        return requests.get(url, headers=headers, params=params, verify=self.cfg.verify_cert)
        # Returned data includes _workflow_execution_ that will be resolved to report on the
        # context in which the core.ask was run.

    def enquiry_list(self, st2_creds=None):
        """
        curl -X GET -H 'X-Auth-Token: X' 'http://127.0.0.1:9101/v1/inquiries/?limit=50'
        """
        url = f"{self.cfg.api_url}/inquiries/"
        params = {}
        headers = st2_creds.requests()
        return requests.get(url, headers=headers, params=params, verify=self.cfg.verify_cert)

    def enquiry_get(self, enquiry_id, st2_creds=None):
        """
        StackStorm currently uses the draft4 jsonschema validator.

        Fetch the contents of an inquiry given its id.

        {
            "id": "60a7c8876d573fae8028be34",
            "route": "slack_query",
            "ttl": 1440,
            "users": [],
            "roles": [],
            "schema": {
                "type" : "object",
                "properties": {
                    "password": {
                        "type": "string",
                        "description": "Enter your not so secret password",
                        "required": true
                    }
                }
            }
        }
        """

        url = f"{self.cfg.api_url}/inquiries/{enquiry_id}"
        params = {}
        headers = st2_creds.requests()
        response = requests.get(url, headers=headers, params=params, verify=self.cfg.verify_cert)

        if response.status_code == requests.codes.ok:
            return response.json()
        elif response.status_code == 401:
            self.refresh_bot_credentials()
            return "Attempted to access API without authentication.  "
            "Try again or fix the bot authorisation."
        else:
            return response.json()

    def actionalias_help(self, pack=None, filter=None, limit=None, offset=None, st2_creds=None):
        """
        Call StackStorm API for action alias help.
        """
        # curl -v -H "X-Auth-Token: $ST2_AUTH_TOKEN"
        # -H 'Content-Type: application/json'
        # -XGET localhost:9101/v1/actionalias/help -d '{}'

        url = f"{self.cfg.api_url}/actionalias/help"

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
        elif response.status_code == 401:
            self.refresh_bot_credentials()
        else:
            response.raise_for_status()

    def match(self, text, st2token):
        headers = st2token.requests()
        url = f"{self.cfg.api_url}/actionalias/match"

        payload = json.dumps({"command": text})
        headers["Content-Type"] = "application/json"

        result = Result()
        try:
            response = requests.post(
                url, headers=headers, data=payload, verify=self.cfg.verify_cert
            )
            if response.status_code == 200:
                result.OK(response.json())
            elif response.status_code == 400:
                result.error(
                    1,
                    "st2 command '{}' not found.  View available commands with {}st2help.".format(
                        text, self.cfg.bot_prefix
                    ),
                )
                LOG.error(result.message)
            else:
                response.raise_for_status()
        except HTTPError as e:
            result.error(2, "HTTPError {}".format(str(e)))
            LOG.error(result.message)
        except Exception as e:
            result.error(3, "Unexpected error {}".format(e))
            LOG.error(result.message)
        return result

    def execute_actionalias(self, msg, chat_user, st2token):
        """
        :msg: errbot message.
        :chat_user: the chat provider user/channel to pass to StackStorm for the execution
                    result response.
        :st2token: The st2 api token/key to be used when submitting the action-alias execution.
        """
        headers = st2token.requests()

        url = f"{self.cfg.api_url}/aliasexecution/match_and_execute"

        payload = {"command": msg.body, "user": chat_user, "notification_route": self.cfg.route_key}

        if msg.is_direct is False:
            payload["source_channel"] = str(msg.to)
            payload["notification_channel"] = str(msg.to)
        else:
            payload["source_channel"] = str(msg.frm)
            payload["notification_channel"] = str(msg.frm)

        msg = ""
        try:
            response = requests.post(
                url, headers=headers, json=payload, verify=self.cfg.verify_cert
            )

            if response.status_code in [201, 400]:
                msg = response.json()
            else:
                msg = response.text
        except Exception as e:
            msg = "Error executing action-alias:  {}".format(str(e))
        return msg

    def st2stream_listener(self, callback=None, bot_identity=None):
        """
        Listen for events passing through the stackstorm bus
        """
        LOG.info("*** Start stream listener ***")

        def listener(callback=None, bot_identity=None):
            token = self.accessctl.get_token_by_userid(bot_identity)
            if not token:
                self.refresh_bot_credentials()
                token = self.accessctl.get_token_by_userid(bot_identity)
                if not token:
                    LOG.debug(
                        "[STREAM] Failed to get a valid token for the bot."
                        "Reconnecting to stream api."
                    )
                    raise ValueError("Bot token is not valid for Stream API.")

            stream_kwargs = {"headers": token.requests(), "verify": self.cfg.verify_cert}

            stream_url = f"{self.cfg.stream_url}/stream"

            stream = sseclient.SSEClient(stream_url, **stream_kwargs)
            for event in stream:
                if event.event == f"st2.announcement__{self.cfg.route_key}":
                    LOG.debug(
                        "*** Errbot announcement event detected! ***\n{}\n{}\n".format(
                            event.dump(), stream
                        )
                    )
                    data = json.loads(event.data)
                    if data.get("context") is not None:
                        LOG.info("Enquiry payload detected, looking up enquiry data.")
                    else:
                        p = data["payload"]
                        callback(
                            p.get("whisper"),
                            p.get("message"),
                            p.get("user"),
                            p.get("channel"),
                            p.get("extra"),
                        )
                # Test for shutdown after event to avoid losing messages.
                if self.accessctl.bot.run_listener is False:
                    break

        def reconnect_delay(self, ttl: int = 600, interval: int = 5, delay: int = 60) -> int:
            """
            Performs a delay that will grow over repeated calls until
            the maximum backoff delay is reached.

            ttl - The duration an error period is active before resetting the retry delay.
            interval - The interval of time to increment the backoff delay.
            delay - The maximum backoff delay to prevent excessively long recoveries.
            """
            instability_ttl = ttl
            delay_interval = interval
            maximum_delay = delay

            error_ts = int(time.time())
            if error_ts - StackStormAPI.last_error > instability_ttl:
                StackStormAPI.retry_delay = delay_interval
            else:
                if StackStormAPI.retry_delay < maximum_delay:
                    StackStormAPI.retry_delay += delay_interval
            LOG.info("Reconnection attempt delay for %d seconds.", StackStormAPI.retry_delay)
            time.sleep(StackStormAPI.retry_delay)

        while self.accessctl.bot.run_listener:
            try:
                self.refresh_bot_credentials()
                listener(callback, bot_identity)
            except Exception as err:
                LOG.critical(
                    "St2 stream listener - An error occurred: %s %s.  " "Backing off %s seconds.",
                    type(err),
                    err,
                    StackStormAPI.stream_backoff,
                )
                traceback.print_exc()
                reconnect_delay()

        LOG.info("*** Exit stream listener ***")
