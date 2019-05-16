# coding:utf-8
import time

import pytest
from mock import Mock

from lib.session import Session
from lib.session_manager import SessionManager
from lib.credentials_adapters import CredentialsFactory
from lib.store_adapters import ClearTextStoreAdapter, StoreAdapterFactory
from lib.errors import SessionExpiredError, SessionInvalidError, SessionConsumedError, \
    SessionExistsError


pytest_plugins = ["errbot.backends.test"]
extra_plugin_dir = '.'


def test_chat_adapters():
    """
    Chat Adapters
    """
# chat_adapters
# slack
# xmpp
# mattermost
# rocketchat
# gitter
# discord


if __name__ == "__main__":
    print("Run with pytest")
    exit(1)
