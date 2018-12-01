# coding:utf-8


class SessionExpiredError(Exception):
    def __init__(self, message="Session has expired."):
        self.message = message


class SessionInvalidError(Exception):
    def __init__(self, message="Session is invalid."):
        self.message = message


class SessionConsumedError(Exception):
    def __init__(self, message="Session has been consumed."):
        self.message = message


class SessionExistsError(Exception):
    def __init__(self, message="Session already exists."):
        self.message = message
