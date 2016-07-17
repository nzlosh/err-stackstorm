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
        _msg = str(msg)
        if _msg == '{0}helpst2'.format(self.bot_prefix):
            return self.help

        data = self.match(_msg)
        if data:
            action_ref = data.pop('__action_ref')
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
        #fiter color
        output = re.sub(r'\x1b\[.{3}(?P<content>.*)\x1b\[0m', r'\g<content>', output)
        return output


    def timer_gen_patterns_and_help(self):
        """
        auto update patterns and help.
        :return:
        """
        while True:
            time.sleep(self.timer_update)
            logging.info('Auto update st2 pattern and help after sleep %d s' % self.timer_update)
            tolerant_gen_patterns_and_help()


    def tolerant_gen_patterns_and_help(self):
        """
        A wrapper method to check for API access authorisation.
        """
        try:
            self.gen_patterns_and_help()
        except Exception as err:
            logging.error('Exception was caught, %s' % err.message)
            self._trial_token()
            self.gen_patterns_and_help()


    def gen_patterns_and_help(self):
        """
        gen pattern and help for action alias
        :return:
        """
        _help = ''
        pattern_action = {}

        st2_client = Client(base_url=self.base_url, api_url=self.api_url, token=self.api_token)

        for alias_obj in st2_client.managers['ActionAlias'].get_all():
            formats = alias_obj.formats

            for _format in formats:
                pattern = _format
                logging.info("Pattern = %s" % pattern)
                if type(pattern) != type(str):
                    continue
                keys = re.findall('{{(.+?)}}', _format)
                if keys:
                    for key in keys:
                        pattern = pattern.replace('{{'+key+'}}', '(?P<{0}>.+)'.format(key.strip()))
                # just match cmd which startswith bot_prefix
                pattern = r'^{0}{1}'.format(self.bot_prefix, pattern)
                pattern = re.compile(pattern, re.I)
                pattern_action[pattern] = alias_obj.action_ref
                _help += '{0}{1} -- {2}\r\n'.format(self.bot_prefix, _format, alias_obj.description)
        self.help = _help
        self.pattern_action = pattern_action


    def match(self, text):
        """
        Match the text against an action and return the action reference.
        """
        results = []
        for pattern in self.pattern_action:
            res = pattern.search(text)
            if res:
                data = res.groupdict()
                data['__action_ref'] = self.pattern_action[pattern]
                results.append(data)

        if not results:
            return None

        results.sort(reverse=True)
        return results[0]
