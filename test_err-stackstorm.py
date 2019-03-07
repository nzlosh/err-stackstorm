# coding:utf-8
# import os
import time
# import sys
# import st2
import pytest
from lib.session import Session
from lib.errors import SessionExpiredError, SessionInvalidError, SessionConsumedError, \
    SessionExistsError

pytest_plugins = ["errbot.backends.test"]
extra_plugin_dir = '.'


# secret_store
## get a secret
## set a secret
## delete a secret
## list secrets

# access_control
# create a session
# get a session by session_id
# get a session by chat_user
# delete a session by session_id
# delete a session by chat_user
# list sessions
# set an st2 token by chat_user
# get an st2 token by session_id

# chat_adapters
# slack
# xmpp
# mattermost
# rocketchat
# gitter
# discord

# bot_commands
# display help
# match and execute action-alias


# session tests
def test_session():
    user_id = "test_id"
    secret = "test_secret"
    session = Session(user_id, secret)

    # Session not expired
    assert False is session.is_expired()

    # Unseal a session
    assert True is session.is_sealed()
    session.unseal()
    assert False is session.is_sealed()

    # Time-to-live
    assert 3600 == session.ttl()
    session.ttl(300)
    assert 300 == session.ttl()

    # Secret
    assert True is session.match_secret(secret)

    # Expired session
    session.ttl(1)
    time.sleep(2)
    with pytest.raises(SessionExpiredError):
        session.is_expired()


if __name__ == "__main__":
    print("Run with pytest")
    exit(1)
