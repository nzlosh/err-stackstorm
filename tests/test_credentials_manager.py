# coding:utf-8
from errst2lib.credentials_adapters import (
    CredentialsFactory,
    St2ApiKey,
    St2UserCredentials,
    St2UserToken,
)

pytest_plugins = ["errbot.backends.test"]
extra_plugin_dir = "."


def test_credentials_manager():
    """
    Credentials manager
    """
    username = "peter.parker"
    password = "stickyweb"
    token = "abcdef1234"
    apikey = "1234abcdef"

    # request user
    user_creds = CredentialsFactory.instantiate("user")(username, password)
    assert isinstance(user_creds, St2UserCredentials)
    assert user_creds.requests() == {"Authorization": "Basic cGV0ZXIucGFya2VyOnN0aWNreXdlYg=="}

    # requests token
    token_creds = CredentialsFactory.instantiate("token")(token)
    assert isinstance(token_creds, St2UserToken)
    assert token_creds.requests() == {"X-Auth-Token": token}

    # requests api key
    apikey_creds = CredentialsFactory.instantiate("apikey")(apikey)
    assert isinstance(apikey_creds, St2ApiKey)
    assert apikey_creds.requests() == {"St2-Api-Key": apikey}


if __name__ == "__main__":
    print("Run with python -m pytest")
    exit(1)
