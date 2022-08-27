.. _installation:

************************************************************************
Installation
************************************************************************

.. contents:: :local:

``err-stackstorm`` can be installed using system packages or by following installation instructions.
It is recommended to use the system packages.   Manual installation instuctions are provided below.

System Package
------------------------------------------------------------------------

System packages are provided to install ``err-stackstorm`` easily in an isolated Python Virtual Environment.

Ubuntu
  Installation is available for bionic, focal and jammy.

  1. Add apt repository

  ::

    sudo echo 'deb https://nzlosh.github.io/repo/ubuntu bionic main' > /etc/apt/source.list.d/err-stackstorm.list

  2. Import public key

  ::

    curl https://nzlosh.github.io/repo/repo_nzlosh_public.gpg | gpg --import -

  3. Update apt indexes

  ::

    apt update

  4. Install err-stackstorm

  ::

    apt install err-stackstorm


Debian
  Installation is available for buster and bullseye.

  1. Add apt repository

  ::

    sudo echo 'deb https://nzlosh.github.io/repo/debian buster main' > /etc/apt/source.list.d/err-stackstorm.list

  2. Import public key

  ::

    curl https://nzlosh.github.io/repo/repo_nzlosh_public.gpg | gpg --import -

  3. Update apt indexes

  ::

    apt update

  4. Install err-stackstorm

  ::

    apt install err-stackstorm

CentOS
  Installation is available for CentOS 8.

  In the new file, enter the command (replacing the IP address with the IP address of your server):

  1. add the yum repository

  ::

    [remote]
    name=err-stackstorm
    baseurl=https://nzlosh.github.io/repo/rhel/8/
    enabled=1
    gpgcheck=1

Rocky
  Installation is available in Rocky 9.

  1. Add a new repository using the ``dnf config-manager --add-repo`` command

  ::

    sudo dnf config-manager --add-repo https://nzlosh.github.io/repo/rhel/8/err-stackstorm.repo


Python Virtual Environment
------------------------------------------------------------------------



Installation of the err-stackstorm plugin can be performed from within a running Errbot instance.  Ensure Errbot is up and running before attempting to install the plugin.

.. note:: See the Errbot installation documentation `here <http://errbot.io/en/latest/user_guide/setup.html>`_  for instructions on how to setup Errbot with the chat backend of your choice.

.. important:: These instructions assume a running instance of StackStorm is already in place.  See the `official StackStorm documentation <https://docs.stackstorm.com/>`_ for details.

Setting up Errbot's Webserver
------------------------------------------------------------------------

.. note:: Configuring the Web server is optional and not required for err-stackstorm to function correctly.

`err-stackstorm` uses a webhook that listens for messages to post to the backend.  This is a convenience feature to simplify pushing message from StackStorm workflows.  `webserver plugin <http://errbot.io/en/latest/user_guide/plugin_development/webhooks.html>`_.

Enabling Errbot's webserver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Enable the webserver by sending the following command to Errbot::

   !plugin config Webserver {'HOST': '0.0.0.0', 'PORT': 3141, 'SSL': {'enabled': False, 'host': '0.0.0.0', 'port': 3142, 'certificate': '', 'key': ''}}

The variables must be adjusted to match the operating environment in which Errbot is running.  See `Errbot documentation <http://errbot.io/en/latest/user_guide/plugin_development/webhooks.html>`_ for further configuration information.

.. warning:: In production environments it is recommended to place a reverse-proxy like `nginx <https://github.com/nginx/nginx>`_ or `Apache <https://httpd.apache.org/>`_ in front of Errbot.

.. note:: Docker users have reported the webserver does not start with container restarts.  It is recommended to install the webserver configuration plugin to enable the webserver in containered environments. ``!repos install https://github.com/tkit/errbot-plugin-webserverconfiguration``


Update Errbot's config.py
------------------------------------------------------------------------

Paste the sample configuration below in Errbot's ``config.py`` file adjusting the URLs to match your StackStorm instance and set up one of the authentication methods.

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
------------------------------------------------------------------------

Confirm Errbot is configured to install plugin dependencies.  The below line should be present in Errbot's `config.py`::

   AUTOINSTALL_DEPS = True

This line ensures that Errbot will attempt to automatically install the requirements of any plugin you may ask it to install.

Now install err-stackstorm::

   !repos install https://github.com/nzlosh/err-stackstorm.git

The plugin will fail to install if any errors are encountered.  This is often caused by configuration errors in Errbot's config.py.

You can confirm that it installed by typing::

    !repos list

The list should contain the ``nzlosh/err-stackstorm`` repo.
