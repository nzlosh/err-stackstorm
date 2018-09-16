# -*- coding: utf-8 -*-
from pathlib import Path
import time
import string
import keyring
# TODO: replace SystemRandom secrets which is added to Python 3.6
from random import SystemRandom
import hvac
import abc
import logging

LOG = logging.getLogger("{}".format(__name__))


class AbstractStoreAdapterFactory(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def keyring_adapter(self):
        pass

    @abc.abstractmethod
    def vault_adpater(self):
        pass


class StoreAdapterFactory(AbstractStoreAdapterFactory):

    @staticmethod
    def keyring_adapter():
        return KeyringStoreAdapter()

    @staticmethod
    def vault_adapter():
        return VaultStoreAdapter()


class AbstractStoreAdapter(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def setup(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def set(self, name, secret, namespace):
        pass

    @abc.abstractmethod
    def get(self, name, namespace):
        pass

    @abc.abstractmethod
    def teardown(self, user):
        pass


class KeyringStoreAdapter(AbstractStoreAdapter):
    def __init__(self):
        rnd = SystemRandom(str(int(time.time()) % 1000))
        self.password = "".join([rnd.choice(string.hexdigits) for _ in range(46)])

    def setup(self, filename='errbot_secrets.conf'):
        self.kr = keyring.get_keyring()
        self.kr.filename = filename
        # TODO: fix calls to remove stored file when bot stops running.
        # Path.unlink(self.kr.file_path)

    def set(self, name, secret, namespace="errst2"):
        self.kr.set_password(namespace, name, secret)

    def get(self, name, namespace="errst2"):
        self.kr.get_password(namespace, name)

    def teardown(self):
        # TODO: fix calls to remove stored file when bot stops running.
        # Path.unlink(self.kr.file_path)
        Path(".").exists()


class VaultStoreAdapter(AbstractStoreAdapter):
    def __init__(self):
        self.client = None

    def setup(self, filename):
        self.client = hvac.Client()

    def set(self, name, secret, namespace="errst2"):
        raise NotImplementedError

    def get(self, name, namespace="errst2"):
        raise NotImplementedError

    def teardown():
        raise NotImplementedError
