#coding:utf-8
import os
import sys

# The st2 module to be tested in the parent directory, apppend the path so it can be imported.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# ~ import st2
pytest_plugins = ["errbot.backends.test", "st2"]

class TestHelloBot(object):
    extra_plugin_dir = '.'

    def test_st2help(self, testbot):
        testbot.push_message('.st2help')
        assert 'packs' in testbot.pop_message()


