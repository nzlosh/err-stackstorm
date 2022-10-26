# coding:utf-8
import pytest
from mock import Mock

from errst2lib.errors import SessionExistsError, SessionInvalidError
from errst2lib.session_manager import SessionManager
from errst2lib.store_adapters import ClearTextStoreAdapter

pytest_plugins = ["errbot.backends.test"]
extra_plugin_dir = "."


def test_session_manager():
    """
    SessionManager class tests
    """
    cfg = Mock()
    cfg.secrets_store = "cleartext"

    user_id = "test%user"
    user_secret = "secret_for_test"
    user_token = "1234567890-0987654321"
    session_ttl = 5000

    session_manager = SessionManager(cfg)

    # Have requested backend
    assert isinstance(session_manager.secure_store, ClearTextStoreAdapter)

    # create a new user
    s = session_manager.create(user_id, user_secret, session_ttl)
    assert s.user_id == user_id

    # 1 session in list
    assert len(session_manager.list_sessions()) == 1

    # create same user raise exception
    with pytest.raises(SessionExistsError):
        session_manager.create(user_id, user_secret, session_ttl)

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


if __name__ == "__main__":
    print("Run with pytest")
    exit(1)
