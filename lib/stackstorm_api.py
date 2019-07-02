# coding:utf-8
import json
import time
import urllib3
import logging
import requests
import sseclient
import traceback

from requests.exceptions import HTTPError

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
    stream_backoff = 10
    authenticate_backoff = 10

    def __init__(self, cfg, accessctl):
        self.cfg = cfg
        self.accessctl = accessctl

        if self.cfg.verify_cert is False:
            urllib3.disable_warnings()

    def refresh_bot_credentials(self):
        LOG.warning("Bot credentials re-authentication required.")
        self.accessctl.bot.authenticate_bot_credentials()

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
        elif response.status_code == 401:
            self.refresh_bot_credentials()
        else:
            response.raise_for_status()

    def match(self, text, st2token):
        headers = st2token.requests()
        url = "/".join([self.cfg.api_url, "actionalias/match"])

        payload = json.dumps({"command": text})
        headers["Content-Type"] = "application/json"

        result = Result()
        try:
            response = requests.post(
                url,
                headers=headers,
                data=payload,
                verify=self.cfg.verify_cert
            )
            if response.status_code == 200:
                result.OK(response.json())
            elif response.status_code == 400:
                result.error(
                    1,
                    "st2 command '{}' not found.  View available commands with {}st2help.".format(
                        text, self.cfg.bot_prefix
                    )
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

    def execute_actionalias(self, action_alias, representation, msg, chat_user, st2token):
        """
        @action_alias: the st2client action_alias object.
        @representation: the st2client representation for the action_alias.
        @msg: errbot message.
        """
        headers = st2token.requests()

        url = "/".join([self.cfg.api_url, "aliasexecution/match_and_execute"])

        payload = {
            "command": msg.body,
            "user": chat_user,
            "notification_route": 'errbot'
        }

        if msg.is_direct is False:
            payload["source_channel"] = str(msg.to)
            payload["notification_channel"] = str(msg.to)
        else:
            payload["source_channel"] = str(msg.frm)
            payload["notification_channel"] = str(msg.frm)

        msg = ""
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                verify=self.cfg.verify_cert
            )

            if response.status_code == 201:
                msg = response.json()
            else:
                msg = response.body
        except Exception as e:
            msg = "Error getting execution and match:  {}".format(str(e))
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

            stream_kwargs = {
                "headers": token.requests(),
                "verify": self.cfg.verify_cert
            }

            stream_url = "".join([self.cfg.stream_url, "/stream"])

            stream = sseclient.SSEClient(stream_url, **stream_kwargs)
            for event in stream:
                if event.event in ["st2.announcement__errbot"]:
                    LOG.debug(
                        "*** Errbot announcement event detected! ***\n{}\n{}\n".format(
                            event.dump(),
                            stream
                        )
                    )
                    data = json.loads(event.data)
                    p = data["payload"]
                    callback(
                        p.get('whisper'),
                        p.get('message'),
                        p.get('user'),
                        p.get('channel'),
                        p.get('extra')
                    )
                # Test for shutdown after event to avoid losing messages.
                if self.accessctl.bot.run_listener is False:
                    break

        StackStormAPI.stream_backoff = 10
        while self.accessctl.bot.run_listener:
            try:
                self.refresh_bot_credentials()
                listener(callback, bot_identity)
            except Exception as err:
                LOG.critical(
                    "St2 stream listener - An error occurred: {} {}.  "
                    "Backing off {} seconds.".format(type(err), err, StackStormAPI.stream_backoff)
                )
                traceback.print_exc()
                time.sleep(StackStormAPI.stream_backoff)
        LOG.info("*** Exit stream listener ***")
