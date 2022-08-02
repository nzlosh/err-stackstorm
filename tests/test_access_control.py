# coding:utf-8
import time

import pytest
from mock import Mock

from lib.credentials_adapters import CredentialsFactory
from lib.errors import (
    SessionConsumedError,
    SessionExistsError,
    SessionExpiredError,
    SessionInvalidError,
)
from lib.session import Session
from lib.session_manager import SessionManager
from lib.store_adapters import ClearTextStoreAdapter, StoreAdapterFactory

pytest_plugins = ["errbot.backends.test"]
extra_plugin_dir = "."


def test_access_control():
    """
    Access Control
    """


# access_control
# create a session
# get a session by session_id
# get a session by chat_user
# delete a session by session_id
# delete a session by chat_user
# list sessions
# set an st2 token by chat_user
# get an st2 token by session_id


if __name__ == "__main__":
    print("Run with pytest")
    exit(1)
