#coding:utf-8
import os
import st2
from errbot.backends.test import testbot


class TestHelloBot(object):
    extra_plugin_dir = '.'

    def test_st2(self, testbot):
        testbot.push_message('.st2help')
        assert 'Hello, gbin@localhost' in testbot.pop_message()
