#coding:utf-8
from errbot import BotPlugin, re_botcmd
from st2client.client import Client
import subprocess
import re
import logging
import threading
import time

class St2(BotPlugin):
    """A plugin for st2"""
    def __init__(self):
        super(St2,self).__init__()

        self.bot_prefix=self.bot_config.BOT_PREFIX
        self.st2_config=self.bot_config.ST2
        self.st2_base_url=self.st2_config.get('st2_base_url') or 'http://localhost'
        self.st2_auth_url=self.st2_config.get('st2_auth_url') or 'http://localhost:9100'
        self.st2_api_url=self.st2_config.get('st2_api_url') or 'http://localhost:9100/v1'
        self.st2_api_version=self.st2_config.get('st2_api_version') or 'v1'
        self.timer_update=self.st2_config.get('timer_update') or 60

        self.pattern_action={}
        self.help=''  #show help doc with exec `!helpst2`
        self.gen_patterns_and_help()

        th1=threading.Thread(target=self.timer_gen_patterns_and_help)
        th1.setDaemon(True)
        th1.start()

    @re_botcmd(pattern=r'.*',prefixed=False)
    def st2_run(self,msg, match):
        _msg=str(msg)
        if _msg=='{0}helpst2'.format(self.bot_prefix):
            return self.help

        data=self.match(_msg)
        if data:
            action_ref=data.pop('__action_ref')
            res=self.run_action(action_ref,**data)
            logging.debug('st2 run response: {0}'.format(res))
            return res

    def run_action(self,action,**kwargs):
        """
        run action
        """
        cmd=r'st2 --url="{0}" --auth-url="{1}" --api-url="{2}" --api-version={3} run {4} {5}'.format(
            self.st2_base_url,
            self.st2_auth_url,
            self.st2_api_url,
            self.st2_api_version,
            action,
            ' '.join('{0}="{1}"'.format(k,v) for k,v in kwargs.iteritems())
        )
        sp=subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output=sp.communicate()[0]
        returncode=sp.returncode
        #fiter color
        output=re.sub(r'\x1b\[.{3}(?P<content>.*)\x1b\[0m',r'\g<content>',output)
        return output

    def timer_gen_patterns_and_help(self):
        """
        auto update patterns and help.
        :return:
        """
        while True:
            time.sleep(self.timer_update)
            logging.debug('Auto update st2 pattern and help after sleep {0}s'.format(self.timer_update))
            self.gen_patterns_and_help()

    def gen_patterns_and_help(self):
        """
        gen pattern and help for action alias

        大概步骤是获取alias ，将其中的{{key}}替换成(?P<key>.+)，然后用正则表达式匹配所有的聊天记录，如果匹配到则执行相应的action。
        :return:
        """
        #一次性替换完helps与pattern_action，减少timer_gen_patterns_and_helps线程干扰可能性。maybe?
        help=''
        pattern_action={}

        st2_client=Client()
        for alias_obj in st2_client.managers['ActionAlias'].get_all():
            formats=alias_obj.formats
            for format in formats:
                pattern=format
                keys=re.findall('{{(.+?)}}',format)
                if keys:
                    for key in keys:
                        pattern=pattern.replace('{{'+key+'}}','(?P<{0}>.+)'.format(key.strip()))
                pattern=r'^{0}{1}'.format(self.bot_prefix,pattern)  #just match cmd which startswith bot_prefix
                pattern=re.compile(pattern,re.I)
                pattern_action[pattern]=alias_obj.action_ref
                help+='{0}{1} -- {2}\r\n'.format(self.bot_prefix,format,alias_obj.description)
        self.help=help
        self.pattern_action=pattern_action

    def match(self,text):
        res=[]
        for pattern in self.pattern_action:
            m=pattern.search(text)
            if m:
                data=m.groupdict()
                data['__action_ref']=self.pattern_action[pattern]
                res.append(data)

        if not res:
            return None

        #可能会匹配到多个patter，这里以匹配到的最长的dict为正确的结果。
        res.sort(reverse=True)
        return res[0]