#coding:utf-8
import os
import st2
#from errbot.backends.test import testbot

pytest_plugins = ["errbot.backends.test"]

class TestHelloBot(object):
    extra_plugin_dir = '.'

    def test_st2help(self, testbot):
        testbot.push_message('.st2help')
        assert 'packs' in testbot.pop_message()

