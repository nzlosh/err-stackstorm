.. _installation:

*************
Installation
*************

.. contents:: :local:

Installation of the err-stackstorm plugin can be performed from within a running Errbot instance. Ensure Errbot is up and running before attempting to install the plugin.

.. note:: See the Errbot installation documentation `here <http://errbot.io/en/latest/user_guide/setup.html>`_  for instructions on how to setup Errbot with the chat backend of your choice.

.. important:: These instructions assume a running instance of StackStorm is already in place. See the `official StackStorm documentation <https://docs.stackstorm.com/>`_ for details.

Setting up Errbot's Webserver
-----------------------------

`err-stackstorm` operates by listening for StackStorm's ChatOps messages and delivers to the chat backend of your choice. In order for StackStorm to be able to reach Errbot, we need to enable Errbot's `webserver plugin <http://errbot.io/en/latest/user_guide/plugin_development/webhooks.html>`_.

Permanently enabling Errbot's webserver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to permanently enable the webserver plugin, send the following command to Errbot::

   !repos install https://github.com/tkit/errbot-plugin-webserverconfiguration

.. warning:: In production environments it is recommended to place a reverse-proxy like `nginx <https://github.com/nginx/nginx>`_ or `Apache <https://httpd.apache.org/>`_ in front of Errbot.

Temporarily enabling Errbot's webserver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you don't want to permanently enable the webserver or perhaps simply wants to run a quick test, send the following command to Errbot::

   !plugin config Webserver {'HOST': '0.0.0.0', 'PORT': 3141, 'SSL': {'enabled': False, 'host': '0.0.0.0', 'port': 3142, 'certificate': '', 'key': ''}}

The variables must be adjusted to match the operating environment in which Errbot is running. See `Errbot documentation <http://errbot.io/en/latest/user_guide/plugin_development/webhooks.html>`_ for further configuration information.

.. note:: The command above is only applied for the current runtime and may not persist after the errbot process is restarted.

Update Errbot's config.py
--------------------------

Paste the sample configuration below in Errbot's ``config.py`` file adjusting the URLs to match your Stackstorm instance and set up one of the authentication methods.

.. code-block:: python

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


See :ref:`configuration` for in-depth explanation.

Installing err-stackstorm
--------------------------

Confirm Errbot is configured to install plugin dependencies. The below line should be present in Errbot's `config.py`::

   AUTOINSTALL_DEPS = True

This line ensures that Errbot's will attempt to automatically install the requirements of any plugin you may ask it to install.

Now install err-stackstorm::

   !repos install https://github.com/nzlosh/err-stackstorm.git

The plugin will fail to install if any errors are encountered. This is often caused by configuration errors in Errbot's config.py.

You can confirm that is installed by typing::

    !repos list

The list should contain the ``nzlosh/err-stackstorm`` repo.
