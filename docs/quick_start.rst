.. _quick_start:

************************************************************************
Quick Start
************************************************************************

If you are familiar with Errbot and StackStorm, this guide will get you up and running in no time.  For in-depth information, refer to :ref:`installation` and :ref:`configuration`

1.  Enable Errbot's webserver (the following command must be a private message to the bot by a bot admin) ::

    !plugin config Webserver {
        "HOST": "0.0.0.0",
        "PORT": 3141,
        "SSL": {
            "certificate": "",
            "enabled": False,
            "host": "0.0.0.0",
            "key": "",
            "port": 3142
        }
    }

    !plugin activate Webserver

2.  Paste the sample configuration below in Errbot's ``config.py`` file adjusting the URLs to match your StackStorm instance and set up one of the authentication methods.::

    STACKSTORM = {
        'auth_url': 'https://your.stackstorm.com/auth/v1',
        'api_url': 'https://your.stackstorm.com/api/v1',
        'stream_url': 'https://your.stackstorm.com/stream/v1',
        'route_key': 'errbot',
        'plugin_prefix': 'st2',
        'verify_cert': True,
        'secrets_store': 'cleartext',
        'api_auth': {
            'user': {
                'name': 'my_username',
                'password': "my_password",
            },
            'token': "<User token>",
            'apikey': '<API Key>'
        },
        'rbac_auth': {
            'standalone': {},
        },
        'timer_update': 900, #  Unit: second.  Interval to check the user token is still valid.
    }


3.  Install err-stackstorm::

   !repos install https://github.com/nzlosh/err-stackstorm.git

6.  Set up an `action alias <https://docs.stackstorm.com/chatops/aliases.html>`_ on StackStorm.  See :ref:`action_alias` for more details.

7.  Sending ``!st2help`` to your bot will list the available StackStorm's aliases.

8.  Aliases can be run like this: ``!st2 run date on 192.168.5.1``

.. important:: When restarting StackStorm, a warning may be produced to inform you `st2chatops` is not running.   This warning can be ignored because `err-stackstorm` is used for StackStorm ChatOps.
