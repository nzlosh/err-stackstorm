#coding:utf-8
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


class St2PluginAPI(object):
    def __init__(self, api_auth, base_url, api_url, auth_url, stream_url, api_version, bot_prefix):
        self.base_url = base_url
        self.api_url = api_url
        self.auth_url = auth_url
        self.stream_url = stream_url
        self.api_version = api_version

        self.st2auth = St2PluginAuth(api_auth, base_url, api_url, auth_url, api_version)
        self.parser = St2PluginActionAliasParser(bot_prefix)


    def show_help(self):
        """
        Pass-through to action alias parser.
        """
        return self.parser.show_help()


    def match(self, text):
        """
        Pass-through to action alias parser.
        """
        return self.parser.match(text)


    def run_action(self, action, **kwargs):
        """
        Perform the system call to execute the Stackstorm action.
        """
        # This method ties errbot to the same machine as the stackstorm
        # installation.  TO DO: Investigate if errbot can execute stackstorm
        # runs from a remote host.

        # This is a hack.  Find a better way to manage authentication by token or api key.
        opt, auth = self.st2auth.auth_method("st2").popitem()
        cmd = [ '/opt/stackstorm/st2/bin/st2',
                '--url={}'.format(self.base_url),
                '--auth-url={}'.format(self.auth_url),
                '--api-url={}'.format(self.api_url),
                '--api-version={}'.format(self.api_version),
                'run',
                '-j',
                '{}'.format(opt),
                '{}'.format(auth),
                '{}'.format(action),
        ]
        for k, v in six.iteritems(kwargs):
            cmd.append('{}={}'.format(k, v))

        sp = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd='/opt/stackstorm/st2/bin')
        output = sp.communicate()[0].strip().decode('utf-8')
        returncode = sp.returncode
        logging.info(output)
        return output


    def st2_run_api(self):
        """
        execute actions via api
        """
        raise NotImplementedError

        # run packs.info pack=livestatus
        # Step 1. Fetch action metadata
        #       http://127.0.0.1:9101/v1/actions/packs.info

        extra_kwargs = self.st2auth.auth_method("st2client")
        logging.info("Create st2 client with {} {} {}".format(self.base_url, self.api_url, extra_kwargs))
        st2_client = Client(base_url=self.base_url, api_url=self.api_url, **extra_kwargs)

        self.parser.process_actionaliases(st2_client.managers['ActionAlias'].get_all())

        # Step 2. Extract runner-type (and validate parameters)
        #          "runner_type" : "python-script",
        #
        # Step 3. Fetch runner-type metadata
        #       http://127.0.0.1:9101/v1/runnertypes/?name=python-script
        #
        # Step 4. Not sure what to do with runner-type metadata
        #
        # Step 5. Call execute API with JSON payload containing parameters
        #       '{"action": "packs.info", "user": null, "parameters": {"pack": "livestatus"}}' http://127.0.0.1:9101/v1/executions
        #
        # Step 6. Get the state of the execution http://127.0.0.1:9101/v1/executions/58243ecbdc599ab304c58940


    def st2stream_listener(self):
        """
        Listen for events passing through the stackstorm bus
        """
        logging.info("\u001b[35m Starting stream listener \u001b[0m")
        def listener():
            headers = self.st2auth.auth_method("requests")
            headers.update({'Accept': 'text/event-stream'})

            response = requests.get(self.stream_url, headers=headers, stream=True)

            client = sseclient.SSEClient(response)
            for event in client.events():
                data = json.loads(event.data)

                print("\u001b[33m")
                pprint.pprint(data)
                print("\u001b[0m")

                if event.event in ["st2.announcement__chatops"]:
                    channel = data["payload"].get('channel')
                    message = data["payload"].get('message')

                    user = data["payload"].get('user')
                    whisper = data["payload"].get('whisper')
                    whisper = data["payload"].get('extra')

                    self.send(
                        self.build_identifier(channel),
                        message,
                    )

        while True:
            try:
                listener()
            except Exception as e:
                logging.critical("St2 stream listener - An error occurred: %e" % e)
                time.sleep(60)


    def generate_actionaliases(self):
        """
        A wrapper method to check for API access authorisation.
        """
        try:
            if not self.st2auth.valid_credentials():
                self.st2auth.renew_token()
        except requests.exceptions.HTTPError as e:
            logging.info("Error while validating credentials %s" % e)

        try:
            self._generate_actionaliases()
        except Exception as e:
            logging.error("Error while fetching action aliases %s" % e)


    def _generate_actionaliases(self):
        """
        generate pattern and help for action alias
        """
        self.help = ''
        self.pattern_action = {}

        auth_kwargs = self.st2auth.auth_method("st2client")
        logging.info("\u001b[35m Create st2 client with {} {} {} \u001b[0m".format(self.base_url, self.api_url, auth_kwargs))
        st2_client = Client(base_url=self.base_url, api_url=self.api_url, **auth_kwargs)
        self.parser.process_actionaliases(st2_client.managers['ActionAlias'].get_all())
