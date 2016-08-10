#coding:utf-8
from errbot import BotPlugin, re_botcmd
from st2client.client import Client
import subprocess
import re
import logging
import threading
import time
import requests
from requests.auth import HTTPBasicAuth

class St2(BotPlugin):
    """
    A plugin for StackStorm
    """
    def __init__(self, bot):
        super(St2, self).__init__(bot)
        self.bot_prefix = self.bot_config.BOT_PREFIX
        self.st2_config = self.bot_config.STACKSTORM
        self.base_url = self.st2_config.get('base_url') or 'http://localhost'
        self.auth_url = self.st2_config.get('auth_url') or 'http://localhost:9100'
        self.api_url = self.st2_config.get('api_url') or 'http://localhost:9100/v1'
        self.api_version = self.st2_config.get('api_version') or 'v1'
        self.timer_update = self.st2_config.get('timer_update') or 60

        # API user authentication.
        api_auth = self.st2_config.get('api_auth') or {}
        tmp_user = api_auth.get('user') or None
        if tmp_user:
            self.api_username = tmp_user.get('name') or None
            self.api_password = tmp_user.get('password') or None
            self.api_token = tmp_user.get("token") or None

        # API Key support doesn't exist in st2client as of version 1.4
        # but it's being worked on # so it's provisioned here for future
        # use.
        self.api_key = api_auth.get('key') or None

        self.pattern_action = {}
        self.help = ''  #show help doc with exec `!helpst2`
        self.tolerant_gen_patterns_and_help()

        th1 = threading.Thread(target=self.timer_gen_patterns_and_help)
        th1.setDaemon(True)
        th1.start()


    @re_botcmd(pattern=r'.*', prefixed=False)
    def st2_run(self, msg, match):
        """
        Run an arbitrary stackstorm command.
        Available commands can be listed using %shelpst2
        """ % self.bot_prefix
        _msg = str(msg)
        if _msg == '{0}helpst2'.format(self.bot_prefix):
            logging.info("Sending help : %s" % self.help)
            return self.help
        logging.debug("Received message: %s" % _msg)
        data = self.match(_msg)
        if data:
            action_ref = data.pop('__action_ref')
            logging.debug('st2 run request %s : %s' % (_msg, action_ref))
            res = self.run_action(action_ref, **data)
            logging.debug('st2 run response: {0}'.format(res))
            return res


    def _trial_token(self):
        """
        Send token header 'X-Auth-Token: <token>'
        to API endpoint https://<stackstorm host>/api/'
        """
        logging.info('trail token "{}"'.format(self.api_token))
        add_headers = {'X-Auth-Token': self.api_token}
        r = self._http_request('GET', '/api/', headers=add_headers)
        logging.info('Server response %d %s' % (r.status_code, r.reason))
        if r.status_code == 401: # unauthorised try to get a new token.
            self._renew_token()
        else:
            logging.info('API response to token = {} {}'.format(r.status_code, r.reason))


    def _renew_token(self):
        """
        Request a new user token be created by stackstorm and use it
        to query the API end point.
        """
        logging.info('renew token with {}:{}'.format(self.api_username, self.api_password))
        auth = HTTPBasicAuth(self.api_username, self.api_password)

        r = self._http_request('POST', '/auth/{}/tokens'.format(self.api_version), auth=auth)
        logging.info('Server response %d %s' % (r.status_code, r.reason))

        if r.status_code == 201: # created.
            auth_info = r.json()
            self.api_token = auth_info["token"]
            logging.info("Received token %s" % self.api_token)
        else:
            logging.warning('Failed to get new user token. {} {}'.format(r.status_code, r.reason))


    def _http_request(self, verb="GET", url="/", headers={}, auth=None):
        """
        Generic HTTP call.
        """
        get_kwargs = {
            'headers': headers,
            'timeout': 5,
            'verify': False
        }

        if auth:
            get_kwargs['auth']=auth

        host = self.base_url.rsplit('//')[1]
        response = requests.request(verb, 'https://{}{}'.format(host,url), **get_kwargs)

        return response


    def run_action(self, action, **kwargs):
        """
        run action
        """
        # This method is not ideal as it requires the bot to run on the
        # same host as the st2 installation.  Stackstorm provides a
        # rest api.
        #
        # USE THE DEBUG INFO TO APPLY THE ACTION.
        # # -------- begin 140213707749136 request ----------
        # curl -X GET -H  'Connection: keep-alive' -H  'Accept-Encoding: gzip, deflate' -H  'Accept: */*' -H  'User-Agent: python-requests/2.10.0' -H  'X-Auth-Token: 1cdc4d360ed74c998e35b2acacddefea' http://127.0.0.1:9101/v1/actions/core.local
        # # -------- begin 140213707749136 response ----------
        # {"name": "local", "parameters": {"cmd": {"required": true, "type": "string", "description": "Arbitrary Linux command to be executed on the remote host(s)."}, "sudo": {"immutable": true}}, "tags": [], "description": "Action that executes an arbitrary Linux command on the localhost.", "enabled": true, "entry_point": "", "notify": {}, "uid": "action:core:local", "pack": "core", "ref": "core.local", "id": "57584182fd6f06e36ec70fb5", "runner_type": "local-shell-cmd"}


        cmd = r'st2 --url="{0}" --auth-url="{1}" --api-url="{2}" --api-version={3} run -t {4} {5} {6}'.format(
            self.base_url,
            self.auth_url,
            self.api_url,
            self.api_version,
            self.api_token,
            action,
            ' '.join('{0}="{1}"'.format(k, v) for k, v in kwargs.iteritems())
        )
        logging.info('running command : {} '.format(cmd))
        sp = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = sp.communicate()[0]
        returncode = sp.returncode
        #filter color
        output = re.sub(r'\x1b\[.{3}(?P<content>.*)\x1b\[0m', r'\g<content>', output)
        return output


    def tolerant_gen_patterns_and_help(self):
        """
        A wrapper method to check for API access authorisation.
        """
        try:
            self.gen_patterns_and_help()
        except Exception as e:
            logging.error('Error while fetching action aliases. %s' % e.message)
            self._trial_token()
            self.gen_patterns_and_help()


    def timer_gen_patterns_and_help(self):
        """
        auto update patterns and help.
        :return:
        """
        while True:
            time.sleep(self.timer_update)
            logging.info('Auto update st2 pattern and help after sleep %d s' % self.timer_update)
            self.tolerant_gen_patterns_and_help()


    def gen_patterns_and_help(self):
        """
        gen pattern and help for action alias

        Aliases have evolved

         {
            "display": "pack deploy <repo_name> [packs <packs>] [branch <branch=master>]",
            "representation": [
                "pack deploy {{repo_name}} packs {{packs}} branch {{branch}}",
                "pack deploy {{repo_name}} packs {{packs}}"
            ]
        },
        "salt {{module}}"

        :return:
        """
        self.help = ''
        self.pattern_action = {}

        st2_client = Client(base_url=self.base_url, api_url=self.api_url, token=self.api_token)

        try:
            for alias_obj in st2_client.managers['ActionAlias'].get_all():
                formats = alias_obj.formats
                display, representation = self.normalise_format(_format)
                for _format in formats:
                    pattern = _format
                    logging.info("Format = %s" % pattern)
                    if not type(pattern) in [type(str()), type(unicode())]:
                        logging.info("Skipping: %s which is type %s" % (alias_obj.action_ref, type(pattern)))
                        continue
                    #~ keys = re.findall('{{(.+?)}}', _format)
                    #~ if keys:
                        #~ for _key in keys:
                            #~ _key = _key.split("=")[0]
                            #~ logging.info("Key: %s" % _key ))
                            #~ pattern = pattern.replace('{{' + _key + '}}', '(?P<{0}>.+)'.format(_key.strip()))
                            #~ logging.info("Pattern: %s" % pattern)
                    # just match cmd which startswith bot_prefix
                    #~ pattern = r'^{0}{1}'.format(self.bot_prefix, pattern)
                    #~ pattern = re.compile(pattern, re.I)
                    pattern = self.format_to_pattern(_format)
                    self.pattern_action[pattern] = alias_obj.action_ref
                    self.help += '{0}{1} -- {2}\r\n'.format(self.bot_prefix, _format, alias_obj.description)
                    logging.info("Added %s" % _format)

        except requests.exceptions.HTTPError as e:
            # Raise HTTP Error to allow re-authentication
            raise e
        except Exception as e:
            logging.error("Error while fetching action aliases %s" % e.message)

    def normalise_format(self, _format):
        if type(_format) in [type(str), type(unicode)]:
            display = _format
            representation = [_format]
        if type(_format) == type(dict):
            display = _format.display
            representation = _format.representation
        return (display, representation)

    def format_to_pattern(self, alias_format):
        """
        ** Comment and regex taken from hubot stackstorm integration **
        Note: We replace format parameters with ([\s\S]+?) and allow arbitrary
        number of key=value pairs at the end of the string
        Format parameters with default value {{param=value}} are allowed to
        be skipped.
        Note that we use "[\s\S]" instead of "." to allow multi-line values
        and multi-line commands in general.
        """
        extra_params = r'(\\s+(\\S+)\\s*=("([\\s\\S]*?)"|\'([\\s\\S]*?)\'|({[\\s\\S]*?})|(\\S+))\\s*)*'
        alias_pattern = re.sub('(\s*){{\s*\S+\s*=\s*(?:({.+?}|.+?))\s*}}(\s*)', '\\s*(<1>([\\s\\S]+?)<3>)?\\s*', alias_format)
        alias_pattern = re.sub('\s*{{.+?}}\s*', '\\s*([\\s\\S]+?)\\s*', alias_pattern)
        alias_pattern = r'^{0}{1}$'.format(self.bot_prefix, alias_pattern)
        return re.compile(alias_pattern, re.I)


    def match(self, text):
        """
        Match the text against an action and return the action reference.
        """
        results = []
        for pattern in self.pattern_action:
            logging.debug("Search: %s using '%s'" % (text, pattern.pattern))
            res = pattern.search(text)
            if res:
                data = res.groupdict()
                data['__action_ref'] = self.pattern_action[pattern]
                results.append(data)

        if not results:
            return None

        results.sort(reverse=True)
        return results[0]
