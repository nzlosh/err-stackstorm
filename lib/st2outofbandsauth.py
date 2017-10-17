# coding:utf-8

import uuid
import string
from random import SystemRandom


def run():
    user_secret = 'to be defined'
    rnd = SystemRandom(user_secret)

    bot_secret = "".join([rnd.choice(string.hexdigits) for i in range(8)])

    print uuid.uuid4(), user_secret, bot_secret
