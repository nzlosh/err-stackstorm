# coding:utf-8
from errst2lib.store_adapters import ClearTextStoreAdapter, StoreAdapterFactory

pytest_plugins = ["errbot.backends.test"]
extra_plugin_dir = "."


def test_secret_store():
    """
    Clear Text Store backend.
    """
    st2_token = "123456-abcdef-123456"

    cleartext = StoreAdapterFactory.instantiate("cleartext")()
    assert isinstance(cleartext, ClearTextStoreAdapter)

    # set a secret
    cleartext.set("token", st2_token)

    # get a secret
    assert st2_token == cleartext.get("token")

    # delete a secret
    cleartext.delete("token")
    assert None is cleartext.get("token")


if __name__ == "__main__":
    print("Run with python -m pytest")
    exit(1)
