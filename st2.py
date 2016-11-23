#coding:utf-8
import re
import logging
import threading

from errbot import BotPlugin, re_botcmd, botcmd, webhook
from st2pluginapi import St2PluginAPI

PLUGIN_PREFIX="st2"

class St2(BotPlugin):
    """
    Stackstorm plugin for authentication and Action Alias execution.  Try !st2help for action alias help.
    """
    def __init__(self, bot):
        super(St2, self).__init__(bot)

        # Append plugin prefix to avoid conflicts between action alias and native errbot plugins
        self.bot_prefix = "{}{} ".format(self.bot_config.BOT_PREFIX, PLUGIN_PREFIX)

        c = self.bot_config.STACKSTORM
        self.st2api = St2PluginAPI(
            c.get('api_auth') or {},
            c.get('base_url') or 'http://localhost',
            c.get('api_url') or 'http://localhost:9100/api/v1',
            c.get('auth_url') or 'http://localhost:9100',
            c.get('stream_url') or 'http://localhost:9102/v1/stream',
            c.get('api_version') or 'v1',
            self.bot_prefix
        )
        self.timer_update = c.get('timer_update') or 60


        # Fetch available action-aliases
        self.st2api.generate_actionaliases()

        th1 = threading.Thread(target=self.st2api.st2stream_listener)
        th1.setDaemon(True)
        th1.start()


    def activate(self):
        """
        Enable poller to fetch st2 action alias patterns and help
        """
        super().activate()
        logging.info("\u001b[35m Poller activated \u001b[0m")
        self.start_poller(self.timer_update, self.st2api.generate_actionaliases)


    @re_botcmd(pattern='^{} .*'.format(PLUGIN_PREFIX))
    def st2_run(self, msg, match):
        """
        Run an arbitrary stackstorm command.
        Available commands can be listed using !st2help
        """
        _msg = msg.body
        data = self.st2api.match(_msg)
        logging.info("st2 matched with the following %s" % data)
        if data:
            action_ref = data.pop('action_ref')
            logging.info('st2 run request %s : %s' % (_msg, action_ref))
            res = self.st2api.run_action(action_ref, **data["kwargs"])
            logging.info('st2 run response: {0}'.format(res))
            return res
        else:
            return "st2 command not found '{}'.  Check help with !st2help".format(_msg)


    @botcmd
    def st2help(self, msg, args):
        """
        Provide help for stackstorm action aliases.
        """
        return self.st2api.show_help()


    @webhook('/chatops/message')
    def chatops_message(self, request):
        """
        Webhook entry point for stackstorm to post messages into
        errbot which will relay them into the chat backend.
        """
        logging.info(request)

        channel = request['channel']
        message = request['message']

        user = request.get('user')
        whisper = request.get('whisper')

        self.send(
            self.build_identifier(channel),
            message,
        )
        truncated = ""
        if len(message) > 96:
            truncated = " ..."
        logging.info("'{}{}'".format(message[:97], truncated))
        return "Message Received."

