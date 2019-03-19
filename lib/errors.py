# coding:utf-8


class Error(Exception):
    def __str__(self):
        return self.message


class SessionExpiredError(Error):
    def __init__(self, message="Session has expired."):
        super(SessionExpiredError, self).__init__()
        self.message = message


class SessionInvalidError(Error):
    def __init__(self, message="Session is invalid."):
        super(SessionInvalidError, self).__init__()
        self.message = message


class SessionConsumedError(Error):
    def __init__(self, message="Session has been consumed."):
        super(SessionConsumedError, self).__init__()
        self.message = message


class SessionExistsError(Error):
    def __init__(self, message="Session already exists."):
        super(SessionExistsError, self).__init__()
        self.message = message
