# coding:utf-8
import time

import pytest
from mock import Mock

from errst2lib.credentials_adapters import CredentialsFactory
from errst2lib.errors import (
    SessionConsumedError,
    SessionExistsError,
    SessionExpiredError,
    SessionInvalidError,
)
from errst2lib.session import Session
from errst2lib.session_manager import SessionManager
from errst2lib.store_adapters import ClearTextStoreAdapter, StoreAdapterFactory

pytest_plugins = ["errbot.backends.test"]
extra_plugin_dir = "."


def test_bot_commands():
    """
    Bot Commands
    """


# bot_commands
# display help
# match and execute action-alias

if __name__ == "__main__":
    print("Run with pytest")
    exit(1)
