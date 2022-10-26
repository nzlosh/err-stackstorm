# coding:utf-8
import hashlib
import logging
import string
import uuid
from datetime import datetime as dt
from random import SystemRandom

from errst2lib.errors import SessionConsumedError, SessionExpiredError

LOG = logging.getLogger("errbot.plugin.st2.session")


def generate_password(length=8):
    rnd = SystemRandom()
    if length > 255:
        length = 255
    return "".join([rnd.choice(string.hexdigits) for _ in range(length)])


class Session(object):
    def __init__(self, user_id, user_secret, session_ttl=3600):
        self.bot_secret = None
        self.user_id = user_id
        self._is_sealed = True
        self.session_id = uuid.uuid4()
        self.create_date = int(dt.now().timestamp())
        self.modified_date = self.create_date
        self.ttl_in_seconds = session_ttl
        self._hashed_secret = self.hash_secret(user_secret)
        del user_secret

    def is_expired(self):
        """
        Returns False if both create and modified timestamps have exceeded the ttl.
        """
        now = int(dt.now().timestamp())
        modified_expiry = self.modified_date + self.ttl_in_seconds
        if modified_expiry < now:
            raise SessionExpiredError
        return False

    def attributes(self):
        return {
            "UserID": self.user_id,
            "IsSealed": self._is_sealed,
            "SessionID": self.session_id,
            "CreationDate": str(dt.fromtimestamp(self.create_date)),
            "ModifiedDate": str(dt.fromtimestamp(self.modified_date)),
            "ExpiryDate": str(dt.fromtimestamp(self.modified_date + self.ttl_in_seconds)),
        }

    def __repr__(self):
        return " ".join(
            [
                "UserID: {},".format(str(self.user_id)),
                "Is Sealed: {},".format(str(self._is_sealed)),
                "SessionID: {},".format(str(self.session_id)),
                "Creation Date: {},".format(str(dt.fromtimestamp(self.create_date))),
                "Modified Date: {},".format(str(dt.fromtimestamp(self.modified_date))),
                "Expiry Date: {}".format(
                    str(dt.fromtimestamp(self.modified_date + self.ttl_in_seconds))
                ),
            ]
        )

    def unseal(self):
        """
        Mark the session as being consumed.  Returns true if the session was available to be
        consumed or raises SessionConsumedError if the session has already been marked as consumed.
        """
        self.is_expired()
        if self._is_sealed:
            self._is_sealed = False
        else:
            raise SessionConsumedError
        return True

    def is_sealed(self):
        """
        Query the state of the one time use flag.
        Returns True if the session has not been consumed or False if the session has already been
        consumed.
        """
        self.is_expired()
        return self._is_sealed

    def id(self):
        """
        Return the UUID for the session.
        """
        return str(self.session_id)

    def ttl(self, ttl=None):
        """
        Get/Set the time to live for the session.
        param: ttl[int] The number of seconds the session should remain valid since creation or
        modification.
        Returns the number of seconds the ttl has been set to if no agrument is provided otherwise
        the ttl is set to the number of seconds provided to the ttl argument.
        """
        self.is_expired()
        if ttl is None:
            return self.ttl_in_seconds

        if isinstance(ttl, int):
            self.ttl_in_seconds = ttl
            self.modified_date = int(dt.now().timestamp())
        else:
            LOG.warning("session ttl must be an integer type, got '{}'".format(ttl))

    def hash_secret(self, user_secret):
        """
        Generate a unique token by hashing a random bot secret with the user secrets.
        param: user_secret[string] - The users secret provided in the chat backend.
        """
        self.is_expired()
        if self.bot_secret is None:
            self.bot_secret = generate_password(8)
        h = hashlib.sha256()
        h.update(bytes(user_secret, "utf-8"))
        del user_secret
        h.update(bytes(self.bot_secret, "utf-8"))
        return h.hexdigest()

    def match_secret(self, user_secret):
        """
        Compare a secret with the session's hashed secret.
        param: user_secret[string] the secret to compare.
        Return True if the user_secret hash has matches the session hash or False if it does not.
        """
        self.is_expired()
        return self._hashed_secret == self.hash_secret(user_secret)
