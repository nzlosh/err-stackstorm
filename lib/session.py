# coding:utf-8
import uuid
import string
import hashlib
import logging
from datetime import datetime as dt
from random import SystemRandom
from lib.store_adapters import StoreAdapterFactory
from lib.stackstorm_api import St2PluginAPI

LOG = logging.getLogger(__name__)


def generate_password(length=8):
    rnd = SystemRandom()
    if length > 255:
        length = 255
    return "".join([rnd.choice(string.hexdigits) for _ in range(length)])


class SessionExpiredError(Exception):
    pass


class SessionInvalidError(Exception):
    pass



class Session(object):
    def __init__(self, user_id, user_secret):
        self.bot_secret = None
        self.hashed_secret = self._hash_secret(user_secret)
        del user_secret
        self.user_id = user_id
        self._session_id_available = True
        self.session_id = uuid.uuid4()
        self.create_date = int(dt.now().timestamp())
        self.modified_date = self.create_date
        self.ttl_in_seconds = 3600

    def expired(self):
        """
        Returns true if both create and modified timestamps have exceeded the ttl.
        """
        now = int(dt.now().timestamp())
        create_expiry = self.create_date + self.ttl_in_seconds
        modified_expiry = self.modified_date + self.ttl_in_seconds
        return create_expiry < now and modified_expiry < now

    def __repr__(self):
        return "".join([
            "UserID: {}, ".format(str(self.user_id)),
            "Session Consumed: {}, ".format(str(self._session_id_available)),
            "SessionID: {}, ".format(str(self.session_id)),
            "Creation Date: {}, ".format(str(dt.fromtimestamp(self.create_date))),
            "Modified Date: {}, ".format(str(dt.fromtimestamp(self.modified_date))),
            "Expiry Date: {}".format(
                str(dt.fromtimestamp(self.modified_date + self.ttl_in_seconds))
            )
        ])

    def use_session_id(self):
        ret = self._session_id_available
        if self._session_id_available:
            self._session_id_available = False
        return ret

    def session_id_available(self):
        """
        Return the state of the one time use
        """
        return self._session_id_available

    def id(self):
        return str(self.session_id)

    def ttl(self, ttl=None):
        if ttl is None:
            return self.ttl_in_seconds

        if isinstance(ttl, int()):
            self.ttl_in_seconds = ttl
            self.modified_date = dt.now()
        else:
            LOG.warning("session ttl must be an integer type, got '{}'".format(ttl))

    def _hash_secret(self, user_secret):
        """
        Generate a unique token by hashing a random bot secret with the user secrets.
        param: user_secret[string] - The users secret provided in the chat backend.
        """
        if self.bot_secret is None:
            self.bot_secret = generate_password(8)
        h = hashlib.sha256()
        h.update(bytes(user_secret, "utf-8"))
        del user_secret
        h.update(bytes(self.bot_secret, "utf-8"))
        return h.hexdigest()
