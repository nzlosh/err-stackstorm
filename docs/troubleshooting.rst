.. _troubleshooting:

****************
Troubleshooting
****************

.. contents:: :local:

Basic Checks
=============

Is the Errbot process running?
-------------------------------

Check if an instance of Errbot is running on the host::

    # ps faux | grep errbo[t]
    root     158707  0.1  0.0 2922228 59640 pts/21  Sl+  Aug14   2:29  |   \_ /opt/errbot/bin/python3 /opt/errbot/bin/errbot -c /data/errbot/etc/config.py

Is the Errbot webhook listening?
--------------------------------

Check Errbot's internal web server is listening on the correct interface. Use the PID from the previous command to filter the output to find which port the errbot process is listening on. You can use ``ss``::

    # ss -tlpn | grep 158707
    LISTEN     0      128       *:3141      *:*      users:(("errbot",158707,21))


or Netstat::

    # netstat -tlpn | grep 158707
    tcp        0      0 0.0.0.0:3141            0.0.0.0:*               LISTEN      158707/python3


If the result is empty, errbot is not listening on any ports. Refer to the Webserver section in :ref:`installation`.


Is the Errbot machine able to communicate with the StackStorm end points?
--------------------------------------------------------------------------

From the errbot machine perform a curl to the StackStorm endpoint::

    curl http://<stackstorm_host>/api/v1/rules

Are the Errbot authentication credentials for StackStorm correct?
------------------------------------------------------------------

Here's you can test that the authentication is working.

Username/password
"""""""""""""""""

A successful username/password authentication is shown below::

    $ st2 auth errbot
    Password:
    +----------+----------------------------------+
    | Property | Value                            |
    +----------+----------------------------------+
    | user     | errbot                           |
    | token    | 10342978da134ae5bbb7dc94d2ba9c08 |
    | expiry   | 2017-09-29T14:31:20.799212Z      |
    +----------+----------------------------------+


If the username and password are valid and correctly entered in errbot's configuration file, errbot will be authorised to interact with StackStorm's API/Stream end points.

User Token
""""""""""

You can test the user token from the configuration using the ``st2`` command and passing the token with ``-t`` argument.

.. important:: Make sure no environment variables are set that could provide a valid token or api key already.

.. code-block:: bash

    $ st2 action-alias list -t 10342978da134ae5bbb7dc94d2ba9c08
    +-----------------------------------+------------+---------------------------------------+---------+
    | ref                               | pack       | description                           | enabled |
    +-----------------------------------+------------+---------------------------------------+---------+
    | packs.pack_get                    | packs      | Get information about installed       | True    |
    |                                   |            | StackStorm pack.                      |         |
    | packs.pack_install                | packs      | Install/upgrade StackStorm packs.     | True    |
    | packs.pack_search                 | packs      | Search for packs in StackStorm        | True    |
    |                                   |            | Exchange and other directories.       |         |
    | packs.pack_show                   | packs      | Show information about the pack from  | True    |
    +-----------------------------------+------------+---------------------------------------+---------+


If a list of action aliases are shown, the token is valid.

API Key
"""""""

Confirm the api key has been created and still registered with StackStorm by using it with the st2 command::

    $ st2 apikey list --api-key ZzVk3DEBZ4FiZmMEmDBkM2x5ZmM5jWZkZWZjZjZmMZEwYzQwZD2iYzUyM2RhYTkTNMYmNDYNODIOOTYwMzE20A
    +--------------------------+--------+-------------------------------------------+
    | id                       | user   | metadata                                  |
    +--------------------------+--------+-------------------------------------------+
    | 586e6deadbeef66deadbeef6 | errbot | {u'used_by': u'errbot api access'}        |
    +--------------------------+--------+-------------------------------------------+

Is Errbot connected correctly to the chat back-end?
----------------------------------------------------

How to test if the bot is connected to the chat back-end is dependant on the back-end. The simplest way is to send a message to the bot user account requesting the built-in help.

For example, using a slack client the following command would be used ``/msg @bot_name !help``. The bot should respond with its help text::

    bot [11:01 AM]
    _All commands_

    *Backup*
    _Backup related commands._
    • *.backup* - Backup everything.
    *ChatRoom*
    _This is a basic implementation of a chatroom_
    • *.room join* - Join (creating it first if needed) a chatroom.
    • *.room occupants* - List the occupants in a given chatroom.
    • *.room invite* - Invite one or more people into a chatroom.
    • *.room topic* - Get or set the topic for a room.


Is the StackStorm ChatOps pack installed and configured correctly?
--------------------------------------------------------------------

err-stackstorm requires the ChatOps pack to be installed. To confirm it is installed, use the ``st2`` cli.

.. code-block:: bash

    $ st2 pack list
    +-------------------+-------------------+--------------------------------+---------+----------------------+
    | ref               | name              | description                    | version | author               |
    +-------------------+-------------------+--------------------------------+---------+----------------------+
    | chatops           | chatops           | ChatOps integration pack       | 0.2.0   | Kirill Enykeev       |
    +-------------------+-------------------+--------------------------------+---------+----------------------+


Confirm the ``notify_errbot.yaml`` is inside the ``chatops/rules`` directory::

    $ cat /opt/stackstorm/packs/chatops/rules/notify_errbot.yaml

You should see a YAML like the one below::

    ---
    name: "notify-errbot"
    pack: "chatops"
    enabled: true
    description: "Notification rule to send results of action executions to stream for chatops"
    trigger:
      type: "core.st2.generic.notifytrigger"
    criteria:
      trigger.route:
        pattern: "errbot"
        type: "equals"
    action:
      ref: chatops.post_result
      parameters:
        channel: "{{ trigger.data.source_channel }}"
        user: "{{ trigger.data.user }}"
        execution_id: "{{ trigger.execution_id }}"

The rule should be available using command ``st2 rule get chatops.notify-errbot``

.. code-block:: bash

    +-------------+--------------------------------------------------------------+
    | Property    | Value                                                        |
    +-------------+--------------------------------------------------------------+
    | id          | 5a6b1abc5b3a0f0f5bcd54e7                                     |
    | uid         | rule:chatops:notify-errbot                                   |
    | ref         | chatops.notify-errbot                                        |
    | pack        | chatops                                                      |
    | name        | notify-errbot                                                |
    | description | Notification rule to send results of action executions to    |
    |             | stream for chatops                                           |
    | enabled     | True                                                         |
    | action      | {                                                            |
    |             |     "ref": "chatops.post_result",                            |
    |             |     "parameters": {                                          |
    |             |         "user": "{{trigger.data.user}}",                     |
    |             |         "execution_id": "{{trigger.execution_id}}",          |
    |             |         "channel": "{{trigger.data.source_channel}}"         |
    |             |     }                                                        |
    |             | }                                                            |
    | criteria    | {                                                            |
    |             |     "trigger.route": {                                       |
    |             |         "pattern": "errbot",                                 |
    |             |         "type": "equals"                                     |
    |             |     }                                                        |
    |             | }                                                            |
    | tags        |                                                              |
    | trigger     | {                                                            |
    |             |     "type": "core.st2.generic.notifytrigger",                |
    |             |     "ref": "core.st2.generic.notifytrigger",                 |
    |             |     "parameters": {}                                         |
    |             | }                                                            |
    | type        | {                                                            |
    |             |     "ref": "standard",                                       |
    |             |     "parameters": {}                                         |
    |             | }                                                            |
    +-------------+--------------------------------------------------------------+



Are events being sent via the StackStorm Stream?
------------------------------------------------

From the errbot host connect to the StackStorm stream endpoint and watch for events emitted as actions are executed by StackStorm::

    curl -s -v -H 'Accept: text/event-stream' -H 'X-Auth-Token: 10342978da134ae5bbb7dc94d2ba9c08' http://<stackstorm_host>/stream/v1/stream

The correct URL will depend on your StackStorm installation, the URL must corresponds to https://api.stackstorm.com/stream/v1/stream/


Are the events seen in the errbot logs using errbot as their route?
--------------------------------------------------------------------

To see the events in the log, the debug level ``BOT_LOG_LEVEL = logging.DEBUG`` will need to be added to errbot's configuration file ``config.py``.

If events are configured correctly, logs will be shown like this (``st2.announcement__errbot``)::

    17:04:12 DEBUG    root                      Dispatching st2.announcement__errbot event, 990 bytes...
    17:04:12 DEBUG    lib.st2pluginapi          *** Errbot announcement event detected! ***
    st2.announcement__errbot event, 990 bytes

If the announcement event is showing as::

    2018-01-26 15:51:55,246 DEBUG    sseclient                 Dispatching st2.announcement__chatops event, 508 bytes...

This indicates that the route wasn't set to errbot, refer to :ref:`configuration`.



F.A.Q.
======


running errbot returns command not found
-----------------------------------------

If Errbot was installed in a python virtual environment, make sure the virtual environment is activated correctly.

st2chatops is not running
--------------------------

The `st2ctl` command is designed with the assumption that ``st2chatops`` is installed for St2 ChatOps.  Since ``err-stackstorm`` **replaces** ``st2chatops``, this
error message can be safely ignored.  More over, ``err-stackstorm`` does not require to be restarted when new action aliases are added since they're read at runtime
from the API.


webserver configuration doesn't persist between bot restarts
-------------------------------------------------------------

In some environments which have file system restrictions like containers, errbot can't save plugin configuration to the data store.  This in turn causes the web server configuration to be lost when the bot is restarted.  To work around this limitation, a plugin that loads the web servers configuration on bot startup can be used.  Install it with the following command:

    !repos install https://github.com/tkit/errbot-plugin-webserverconfiguration
