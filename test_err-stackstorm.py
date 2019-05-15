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


def test_secret_store():
    """
    Test StoreAdapter and each StoreAdapter.
    """
    st2_token = "123456-abcdef-123456"

    cleartext = StoreAdapterFactory.instantiate("cleartext")
    assert isinstance(cleartext, ClearTextStoreAdapter)

    # set a secret
    cleartext.set("token", st2_token)

    # get a secret

    # list secrets

    # delete a secret

    # list secrets


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

def test_credentials_manager():
    """
    Test credentials manager
    """
    username = "peter.parker"
    password = "stickyweb"
    token = "abcdef1234"
    apikey = "1234abcdef"

    user_creds = CredentialsFactory.instantiate("user")(username, password)
    token_creds = CredentialsFactory.instantiate("token")(token)
    apikey_creds = CredentialsFactory.instantiate("api")(apikey)

    # request user
    assert user_creds.requests() == {'Authorization': 'Basic cGV0ZXIucGFya2VyOnN0aWNreXdlYg=='}

    # requests token
    assert token_creds.requests() == {'X-Auth-Token': token}

    # requests api key
    assert apikey_creds.requests() == {'St2-Api-Key': apikey}


def test_session_manager():
    """
    SessionManager class tests
    """
    cfg = Mock()
    cfg.secrets_store = "cleartext"

    user_id = 'test%user'
    user_secret = 'secret_for_test'
    user_token = '1234567890-0987654321'

    session_manager = SessionManager(cfg)

    # Have requested backend
    assert isinstance(session_manager.secure_store, ClearTextStoreAdapter)

    # create a new user
    s = session_manager.create(user_id, user_secret)
    assert s.user_id == user_id

    # 1 session in list
    assert len(session_manager.list_sessions()) == 1

    # create same user raise exception
    with pytest.raises(SessionExistsError):
        session_manager.create(user_id, user_secret)

    # get an existing session
    s1 = session_manager.get_by_uuid(s.id())
    assert s1.id() == s.id()

    # get a non-existent session
    with pytest.raises(SessionInvalidError):
        session_manager.get_by_uuid(s.id() + "no_uuid")

    # get an existing session by user
    s2 = session_manager.get_by_userid(user_id)
    assert s2.id() == s.id()

    # get a non-existent session by user
    with pytest.raises(SessionInvalidError):
        session_manager.get_by_userid(user_id + "no_user")

    # confirm existence
    assert session_manager.exists(user_id) is True

    # confirm non-existence
    assert session_manager.exists(user_id + "no_user") is False

    # Set value in secret store
    assert session_manager.put_secret(s.id(), user_token) is True

    # Get value in secret store
    assert session_manager.get_secret(s.id()) == user_token


def test_session():
    """
    Session class tests
    """
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
