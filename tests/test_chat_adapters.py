# coding:utf-8
from mock import Mock

from errst2lib.chat_adapters import (
    ChatAdapterFactory,
    GenericChatAdapter,
    MattermostChatAdapter,
    SlackChatAdapter,
    XMPPChatAdapter,
)

pytest_plugins = ["errbot.backends.test"]
extra_plugin_dir = "."


def test_chat_adapters():
    """
    Chat Adapters
    """
    slack = ChatAdapterFactory.instance("slack")(Mock())
    assert isinstance(slack, SlackChatAdapter)

    mattermost = ChatAdapterFactory.instance("mattermost")(Mock())
    assert isinstance(mattermost, MattermostChatAdapter)

    xmpp = ChatAdapterFactory.instance("xmpp")(Mock())
    assert isinstance(xmpp, XMPPChatAdapter)

    generic = ChatAdapterFactory.instance("generic")(Mock())
    assert isinstance(generic, GenericChatAdapter)


if __name__ == "__main__":
    print("Run with pytest")
    exit(1)
