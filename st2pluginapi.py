# coding:utf-8
import six
import json
import time
import pprint
import logging
import requests
import sseclient
import subprocess

from st2pluginauth import St2PluginAuth
from st2client.client import Client
from st2pluginactionaliasparser import St2PluginActionAliasParser
from st2client.models.action_alias import ActionAliasMatch
from st2client.models.aliasexecution import ActionAliasExecution
from requests.exceptions import HTTPError
LOG = logging.getLogger(__name__)


class St2PluginAPI(object):
    def __init__(self, st2config):
        self.st2config = st2config
        self.st2auth = St2PluginAuth(st2config)
        self.parser = St2PluginActionAliasParser(st2config.full_prefix)

    def show_help(self):
        """
        Pass-through to action alias parser.
        """
        # curl -v -H "X-Auth-Token: $ST2_AUTH_TOKEN"
        # -H 'Content-Type: application/json'
        # -XPOST localhost:9101/v1/actionalias/help -d '{}'
        return self.parser.show_help()

    def match(self, text):
        auth_kwargs = self.st2auth.auth_method("st2client")

        LOG.info("Create st2 client with {} {} {}".format(self.st2config.base_url,
                                                          self.st2config.api_url,
                                                          auth_kwargs))

        st2_client = Client(base_url=self.st2config.base_url,
                            api_url=self.st2config.api_url,
                            **auth_kwargs)

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

    def run_action(self, action, **kwargs):
        """
        Perform the system call to execute the Stackstorm action.
        """
        opt, auth = self.st2auth.auth_method("st2").popitem()
        cmd = ['/opt/stackstorm/st2/bin/st2',
               '--url={}'.format(self.st2config.base_url),
               '--auth-url={}'.format(self.st2config.auth_url),
               '--api-url={}'.format(self.st2config.api_url),
               '--api-version={}'.format(self.st2config.api_version),
               'run',
               '-j',
               '{}'.format(opt),
               '{}'.format(auth),
               '{}'.format(action)]
        for k, v in six.iteritems(kwargs):
            cmd.append('{}={}'.format(k, v))

        sp = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              cwd='/opt/stackstorm/st2/bin')
        output = sp.communicate()[0].strip().decode('utf-8')
        returncode = sp.returncode
        LOG.info(output)
        return output

    def action_execution(self, msg, action_ref, action_alias, **kwargs):
        """
        Execute actions via api
        @action - Action reference.
        @msg - Errbot's chat message.
        @kwargs - a dict containing 0 or more arguments to be provided when calling the action.
        """

        LOG.info("\u001b[35m Action={} kwargs={} \u001b[0m".format(action_alias.name, kwargs))

        # run packs.info pack=livestatus
        # Step 1. Fetch action metadata
        #       http://127.0.0.1:9101/v1/actions/packs.info

        auth_kwargs = self.st2auth.auth_method("st2client")
        LOG.info("Create st2 client with {} {} {}".format(self.st2config.base_url,
                                                          self.st2config.api_url,
                                                          auth_kwargs))

        st2_client = Client(base_url=self.st2config.base_url,
                            api_url=self.st2config.api_url,
                            **auth_kwargs)

        LOG.info("\u001b[35m {} {}\u001b[0m".format(action_ref, kwargs))
        action_meta = st2_client.actions.get_by_id(action_ref)
        if not action_meta.enabled:
            return "{}.{} won't execute because it's disabled.".format(action_meta.pack,
                                                                       action_meta.name)
        LOG.info("\u001b[35m action_meta={}\u001b[0m".format(action_meta))

        # Step 2. Extract runner-type (and validate parameters)
        #          "runner_type" : "python-script",
        # action_meta=<Action name=state_overview,pack=livestatus,enabled=True,
        #                                   runner_type=action-chain>
        runnertype_meta = st2_client.runners.get_by_name(action_meta.runner_type)
        LOG.info("\u001b[35m runnertype_meta={}\u001b[0m".format(runnertype_meta))

        # Step 3. Fetch runner-type metadata
        #       http://127.0.0.1:9101/v1/runnertypes/?name=python-script
        #
        # Step 4. Not sure what to do with runner-type metadata
        #
        # Step 5. Call execute API with JSON payload containing parameters
        #       '{"action": "packs.info", "user": null, "parameters":
        #                       {"pack": "livestatus"}}' http://127.0.0.1:9101/v1/executions
        LOG.info([action_meta.pack, action_meta.name, msg.body, msg.frm, msg.channelname])

        url = self.st2config.api_url+"executions"
        payload = {
            'action': "{}.{}".format(action_meta.pack, action_meta.name),
            'format': "xxxx",
            'command': msg.body,
            'user': str(msg.frm),
            'parameters': {"pack": action_meta.pack},
            'source_channel': msg.channelname,
            'notification_route': 'errbot'
        }

        payload = "{} {} {}".format(str(dir(action_meta)),
                               str(dir(msg)),
                               str(dir(runnertype_meta)))

        LOG.info("\u001b[35m PAYLOAD={}\u001b[0m".format(payload))
        r = requests.post(url, json=payload, verify=False)
        LOG.info(r)
        # Step 6. Get the state of the execution http://127.0.0.1:9101/v1/executions/<exec_id>
        return {
            "url": url,
            "payload": str(payload),
            "runnertype_meta": str(runnertype_meta),
            "action_meta": str(action_meta),
            "ebbot_msg": str(msg)
        }
        raise NotImplementedError

    def execute_actionalias(self, action_alias, representation, msg):
        """
        @action_alias: the st2client action_alias object.
        @representation: the st2client representation for the action_alias.
        @msg: errbot message.
        """
        auth_kwargs = self.st2auth.auth_method("st2client")
        LOG.info("Create st2 client with {} {} {}".format(self.st2config.base_url,
                                                          self.st2config.api_url,
                                                          auth_kwargs))

        st2_client = Client(base_url=self.st2config.base_url,
                            api_url=self.st2config.api_url,
                            debug=True,
                            **auth_kwargs)

        execution = ActionAliasExecution()
        execution.name = action_alias.name
        execution.format = representation
        execution.command = msg.body
        execution.source_channel = str(msg.frm)
        if msg.is_direct == False:
            execution.notification_channel = str(msg.frm)
        else:
            execution.notification_channel = str(msg.to)
        execution.notification_route = 'errbot'
        execution.user = str(msg.frm)

        LOG.info("Execution: {}".format([execution.command,
                                         execution.format,
                                         execution.name,
                                         execution.notification_channel,
                                         execution.notification_route,
                                         execution.source_channel,
                                         execution.user]))

        action_exec_mgr = st2_client.managers['ActionAliasExecution']
        execution = action_exec_mgr.create(execution)

        LOG.info("AFTER {}{}".format(type(execution), dir(execution)))
        LOG.info("AFTER {}{}".format(execution.execution, execution.message))
        return " ".join([execution.message])

    def st2stream_listener(self, callback=None):
        """
        Listen for events passing through the stackstorm bus
        """
        LOG.info("\u001b[35m Starting stream listener \u001b[0m")

        def listener(callback=None):
            headers = self.st2auth.auth_method("requests")
            headers.update({'Accept': 'text/event-stream'})

            response = requests.get(self.st2config.stream_url, headers=headers, stream=True)

            client = sseclient.SSEClient(response)
            for event in client.events():
                data = json.loads(event.data)
                if event.event in ["st2.announcement__errbot"]:
                    LOG.info("\u001b[35mErrbot announcement event detected!\u001b[0m")
                    channel = data["payload"].get('channel')
                    message = data["payload"].get('message')

                    user = data["payload"].get('user')
                    whisper = data["payload"].get('whisper')
                    extra = data["payload"].get('extra')

                    callback(whisper, message, user, channel, extra)

        while True:
            try:
                listener(callback)
            except Exception as e:
                LOG.critical("St2 stream listener - An error occurred: %s" % e)
                time.sleep(60)

    def generate_actionaliases(self):
        """
        A wrapper method to check for API access authorisation.
        """
        try:
            if not self.st2auth.valid_credentials():
                self.st2auth.renew_token()
        except requests.exceptions.HTTPError as e:
            LOG.info("Error while validating credentials %s (%s)" % (e.reason, e.code))

        try:
            self._generate_actionaliases()
        except Exception as e:
            LOG.error("Error while fetching action aliases %s" % e)

    def _generate_actionaliases(self):
        """
        generate pattern and help for action alias
        """
        self.help = ''
        self.pattern_action = {}

        base_url = self.st2config.base_url
        api_url = self.st2config.api_url

        auth_kwargs = self.st2auth.auth_method("st2client")
        LOG.info("\u001b[35m Create st2 client with {} {} {} \u001b[0m".format(base_url,
                                                                               api_url,
                                                                               auth_kwargs))
        st2_client = Client(base_url=base_url, api_url=api_url, **auth_kwargs)
        self.parser.process_actionaliases(st2_client.managers['ActionAlias'].get_all())
