# coding:utf-8

class SessionExpiredError(Exception):
    pass


class SessionInvalidError(Exception):
    pass


class SessionConsumedError(Exception):
    pass
