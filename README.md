# err-stackstorm
A plugin to run StackStorm actions, bringing StackStorm's ChatOps to Errbot.

## Table of Contents
1. [Getting help](#GettingHelp)
1. [Installation](#Installation)
1. [Requirements](#Requirements)
1. [Supported Chat Backends](#SupportedChatBackends)
1. [Configuration](#Configuration)
1. [Setup Action-Aliases](#ActionAliases)
1. [Webhook](#Webhook)
1. [Server-Side Events](#ServerSideEvents)
1. [ChatOps Pack](#ChatOpsPack)
1. [Troubleshooting](#Troubleshooting)

## Getting help <a name="GettingHelp">
You can find users of err-stackstorm on Gitter.  https://gitter.im/err-stackstorm/community or Slack https://stackstorm-community.slack.com `#err-stackstorm`
 
## Installation <a name="Installation"></a>
Installation of the err-stackstorm plugin is performed from within a running Errbot instance.  Ensure Errbot is up and running before attempting to install the plugin.  See the Errbot installation documentation here https://github.com/Errbotio/Errbot for instructions on how to setup Errbot on your chat back-end.  These instructions assume a running instance of StackStorm is already in place.  See the official [StackStorm documentation](https://docs.stackstorm.com/install/index.html) for details.

 1. Install Errbot on the target system using standard package manager or Errbot installation method.
 1. Configure Errbot, see the [Configuration](#Configuration) section for help.
 1. Enable Errbot's internal web server, see the [Webhook](#Webhook) section for help.
 1. Install ChatOps pack on StackStorm, see the [ChatOps Pack](#ChatOpsPack) section for help.
 1. Connect to your chat back-end and starting interacting with your StackStorm/Errbot instance.

The below command will install the plugin.
```
!repos install https://github.com/nzlosh/err-stackstorm.git
```

## Requirements <a name="Requirements"></a>
The plugin has been developed and tested against the below software.  For optimal operation it is recommended to use the following versions:

plugin tag (version) | Python | Errbot | StackStorm client
--- | --- | --- | ---
2.0 | 3.4 | 5.2.0 | 2.10
1.4 | 3.4 | 5.1.2 | 2.5
1.3 | 3.4 | 5.1.2 | 2.5
1.2 | 3.4 | 5.0   | 2.2
1.1 | 3.4 | 4.3   | 2.2
1.0 | 2.7 | 3.x   | 2.1

## Supported Chat Back-ends <a name="SupportedChatBackends"></a>
Errbot provides official support for a few of major chat back-ends and many more chat back-ends are available through unofficial plugins.

Back end | Mode value | Support type
--- | --- | ---
Slack | `slack` | Integrated
Text | `text` | Integrated
XMPP | `xmpp` | Integrated
[Mattermost](https://about.mattermost.com/) | `mattermost` | [Plugin](https://github.com/Vaelor/errbot-mattermost-backend)
[Rocket Chat](https://rocket.chat/) | `aoikrocketchaterrbot` | [Plugin](https://github.com/AoiKuiyuyou/AoikRocketChatErrbot)
[Gitter](gitter.im/) | `gitter` | [Plugin](https://github.com/errbotio/err-backend-gitter)
[Discord](https://www.discordapp.com/) | `discord` | [Plugin](https://github.com/gbin/err-backend-discord)

Back-end support will provide a minimum set of back-end chat functionality to the err-stackstorm plugin like `connect` to and `authenticate` with chat back-end, `identify` users/rooms and `send_message` to users/rooms.  Advanced formatting may not be available on all back-ends since adaptor code is required in the err-stackstorm plugin to translate ActionAlias `extra` parameter on a per back-end basis.

Currently supported extra back-ends
* Slack
* XMPP


## Configuration <a name="Configuration"></a>
Edit the `config.py` configuration file which is used to describe how the plugin will communicate with StackStorm's API and authentication end points.
If you followed the Errbot setup documentation this file will have been created by downloading a template from the Errbot GitHub site.   If this file has not already been created, please create it following the instructions at https://github.com/Errbotio/Errbot

```
STACKSTORM = {
    'auth_url': 'https://stackstorm.example.com/auth/v1',
    'api_url': 'https://stackstorm.example.com/api/v1',
    'stream_url': 'https://stackstorm.example.com/stream/v1',

    'verify_cert': True,
    'secrets_store': {
        'cleartext': {}
        'keyring': {
            'keyring_password': "<keyring_password>"
        },
        'vault': {}
    },
    'api_auth': {
        'user': {
            'name': 'my_username',
            'password': "my_password",
        },
        'token': "<User token>",
        'key': '<API Key>'
    },
    'rbac_auth': {
        'standalone': {},
        'serverside': {},
        'clientside': {
            'url': '<url_to_errbot_webserver>',
        }
    },
    'timer_update': 900, #  Unit: second.  Interval for Errbot to refresh to list of available action aliases.
}
```

Option | Description
--- | ---
`auth_url` | StackStorm's authentication url end point.  Used to authenticate credentials against StackStorm.
`api_url` | StackStorm's API url end point.  Used to execute action aliases received from the chat back-end.
`stream_url` | StackStorm's Stream url end point.  Used to received ChatOps notifications.
`verify_cert` | Default is *True*.  Verify the SSL certificate is valid when using https end points.  Applies to all end points.
`api_auth.user.name` | Errbot username to authenticate with StackStorm.
`api_auth.user.password` | Errbot password to authenticate with StackStorm.
`api_auth.token` | Errbot user token to authenticate with StackStorm.  Used instead of a username/password pair.
`api_auth.key` | Errbot API key to authenticate with StackStorm.  Used instead of a username/password pair or user token.
`timer_update` | Unit: seconds.  Default is *60*. Interval for err-stackstorm to refresh to list of available action aliases.  (deprecated)
`rbac_auth.standalone` | Standalone authentication.
`rbac_auth.serverside` | Serverside authentication, err-stackstorm will request StackStorm credentials on behalf of a chat user from StackStorm.
`rbac_auth.clientside` | Clientside authentication, a chat user will supply StackStorm credentials to err-stackstorm via an authentication page.
`rbac_auth.clientside.url` | Url to the authentication web page.
`secrets_store.cleartext` | Use the in memory store.
`secrets_store.keyring` | Use the system's keyring store.
`secrets_store.keyring.keyring_password` | Password to unlock the keyring.
`secrets_store.vault` | Use Hashicorp Vault store.

### Locale
Errbot uses the systems locale for handling text, if your getting errors handling non ascii characters from chat
`UnicodeEncodeError: 'ascii' codec can't encode character '\xe9' in position 83: ordinal not in range(128)`
Make sure the systems locale is using a unicode encoding, the `.UTF8` indicates the system encoding uses unicode.
```
# locale
LANG=en_NZ.UTF8
LANGUAGE=
LC_CTYPE="en_NZ.UTF8"
LC_NUMERIC="en_NZ.UTF8"
LC_TIME="en_NZ.UTF8"
LC_COLLATE="en_NZ.UTF8"
LC_MONETARY="en_NZ.UTF8"
LC_MESSAGES="en_NZ.UTF8"
LC_PAPER="en_NZ.UTF8"
LC_NAME="en_NZ.UTF8"
LC_ADDRESS="en_NZ.UTF8"
LC_TELEPHONE="en_NZ.UTF8"
LC_MEASUREMENT="en_NZ.UTF8"
LC_IDENTIFICATION="en_NZ.UTF8"
LC_ALL=en_NZ.UTF8
```

### Authentication <a name="Authentication"></a>
Authentication is possible with username/password, User Token or API Key.  In the case of a username and password, the plugin is requests a new User Token after it expires.  In the case of a User Token or API Key, once it expires, the Errbot plugin will no longer have access to the st2 API.

The Errbot plugin must have valid credentials to use StackStorm's API.  The credentials may be;

 - username/password
 - user token
 - api key

See https://docs.stackstorm.com/authentication.html for more details.

#### Username/Password
Using a username and password will allow Errbot to renew the user token when it expires.  If a _User Token_ is supplied, it will be used in preference to username/password authentication.

#### User Token
To avoid using the username/password pair in a configuration file, it's possible to supply a _User Token_ as generated by StackStorm when a username/password is authenticated successfully.  Note when the token expires, a new one must be generated and updated in `config.py` which in turn requires Errbot to be restarted.
This form of authentication is the least practical for production environments.

#### API Key
_API Key_ support has been included since StackStorm v2.0.  When an _API Key_ is provided, it is used in preference to a _User Token_ or _username/password_ pair.  It is considered a mistake to supply a token or username/password pair when using the API Key.

### Secrets Store
The secrets store is used by err-stackstorm to cache StackStorm API credentials.  The available backends are:

 - `cleartext`
 - `keyring`
 - `vault`

#### ClearText
The `cleartext` store maintains the cache in memory and does not encrypt the contents to disk.  This is option doesn't protect the stored secrets.

#### KeyRing
The `keyring` store uses the systems keyring manager to create a namespace and write secrets to it.  Secrets are persisted to disk in an encrypted format.  The keyring must be unlocked when errbot is started.  [detail](http://man7.org/linux/man-pages/man7/keyrings.7.html)

#### HashiCorp Vault
The `vault` store uses Hashicorp's Vault to store secrets.  [details](https://www.vaultproject.io)

### Role Based Access Control Authentication

#### Standalone RBAC

This is the original authentication method where by err-stackstorm uses its own credentials for all
calls to the StackStorm API.  All action-alias' issued by chat service users execute the underlying
workflows with err-stackstorm credentials.


##### Configuration
It is considered an error to have multiple RBAC authentication configurations present at the same time.
An empty dictionary in the *standalone* key is all that is required to maintain Err-stackstorm's
original authentication method.
```
    'rbac_auth': {
        'standalone': {},
    },
```

#### Server-side RBAC

The "server-side" RBAC implementation uses err-stackstorm credentials to call the StackStorm API
to pass chat service user identification.  The err-stackstorm credentials must be defined as a
service.  Chat service user identifications must be registered with StackStorm before being used.

When a chat service user matches, StackStorm will return the associated user token and err-stackstorm
will cache the result.  When a chat user triggers an action-alias, the associated workflow will be
executed with the cached user token.

##### Configuration
It is considered an error to have multiple RBAC authentication configurations present at the same time.
Only the *serverside* key with an empty dictionary is required to enable Server-side RBAC for ChatOps.

```
    'rbac_auth': {
        'serverside': {}
    },
```

#### Client-side RBAC

Err-stackstorm provides a way to associate the chat service user account with a StackStorm
username/password, user token or api token.

This implementation is specific to err-stackstorm.  It is achieved by requesting a new authentication
session with err-stackstorm.  A Universally Unique Identifier (UUID) is generated for the session
and the chat user is invited to follow a URL to the authentication page hosted by errbot.  For
security reasons, the UUID is a one time use and is consumed when the page is accessed.

The login page must be protected by TLS encryption and ideally require an ssl client certificate.
The login page should not be exposed directly to the internet, but have a reverse proxy such as
nginx place between it and any external service consumers.

The user enters their StackStorm credentials via the login page which err-stackstorm will validate
against the StackStorm API.  If the credentials are valid, the user token or api key will be cached
by err-stackstorm and the supplied credentials discarded.

Once a chat user is associated with their StackStorm credentials, any action-alias will be executed
using the associated StackStorm credentials.


##### Configuration
It is considered an error to have both *extended* and *proxied* RBAC authentication configurations
present at the same time.  A *proxied* key with *url* and *keyring_password* are required to correctly
configure Out-of-bands authentication for ChatOps.
```
    'rbac_auth': {
        'clientside': {
            'url': 'https://<hostname>:<port>/',
            'keyring_password': "<password>"
        }
    },
```

Option | Description
--- | ---
`url` | Errbot's authentication web server end point.  Used for the out-of-bands authentication web page.
`keyring_password` | The password used to unlock the keyring to read/write stored data.



## How to expose action-aliases as plugin commands <a name="ActionAliases"></a>
 1. Connect Errbot to your chat environment.
 1. Write an [action alias](https://docs.stackstorm.com/chatops/aliases.html) in StackStorm.
 1. Errbot will automatically refresh its action alias list.
 1. Type `!st2help` in your chat program to list available StackStorm commands.
 1. Type the desired command in your chat program, as shown in the help.

## Send messages from StackStorm to Errbot using Errbot's native webhook support <a name="Webhook"></a>

Errbot has a built in web server which is configured and enabled through the bots admin chat interface.  The StackStorm plugin is written to listen for StackStorm's ChatOps messages and delivers them to the attached chat back-end.

To configure Errbot's web server plugin, the command below can be sent to Errbot:
```
!plugin config Webserver {'HOST': '0.0.0.0', 'PORT': 3141,
'SSL': {'enabled': False, 'host': '0.0.0.0', 'port': 3142, 'certificate': '', 'key': ''}}
```

**NOTE:** _The variables must be adjusted to match the operating environment in which Errbot is running.  See Errbot documentation for further configuration information._

The configuration above is only applied for the current runtime and will not
persist after the errbot process being restarted. Making the configuration
change permanent is as simple as installing a special plugin:
```
!repos install https://github.com/tkit/errbot-plugin-webserverconfiguration
```
The configuration command from above is not required prior to installing this
plugin.

In production environments it may be desirable to place a reverse-proxy like nginx in front of errbot.

## Send notifications to Errbot from StackStorm using Server-Side Events (SSE) <a name="ServerSideEvents"></a>

As of StackStorm 1.4. server-sent events (SSE) were added which allowed ChatOps messages to be
streamed from StackStorm to a connected listener (err-stackstorm in our case).  The StackStorm
stream url must be supplied in the configuration so err-stackstorm knows where to establish the
http connection.  The SSE configuration is complementary to the webhook method and both must be
enabled for full ChatOps support between StackStorm and Errbot.

## StackStorm ChatOps pack configuration. <a name="ChatOpsPack"></a>

StackStorm's [ChatOps pack](https://github.com/StackStorm/st2/tree/master/contrib/chatops) is required
to be installed and a notify rule file added to the pack.

The notify rule must be placed in `/<stackstorm installation>/packs/chatops/rules`.  The rule file
[notify_errbot.yaml](https://raw.githubusercontent.com/fmnisme/err-stackstorm/master/contrib/stackstorm-chatops/rules/notify_errbot.yaml) can be found
in this repository under

Edit the `chatops/actions/post_message.yaml` file to use the errbot route as it's default value.
```
  route:
    default: "errbot"
```

## Troubleshooting <a name="Troubleshooting"></a>

### Is the Errbot process running?
Check an instance of Errbot is running on the host
```
# ps faux | grep errbo[t]
root     158707  0.1  0.0 2922228 59640 pts/21  Sl+  Aug14   2:29  |   \_ /opt/errbot/bin/python3 /opt/errbot/bin/errbot -c /data/errbot/etc/config.py
```

### Is the Errbot webhook listening?
Check Errbot's internal web server is listening on the correct interface.
```
# ss -tlpn | grep 158707
LISTEN     0      128                       *:8888                     *:*      users:(("errbot",158707,21))
```
OR
```
# netstat -tlpn | grep 158707
tcp        0      0 0.0.0.0:8888            0.0.0.0:*               LISTEN      158707/python3
```

### Is the Errbot machine able to communicate with the StackStorm end points?
From the errbot machine perform a curl to the StackStorm endpoint:

```
curl http://<stackstorm_host>/api/v1/rules
```

### Are the Errbot authentication credentials for StackStorm correct?
To test if the username/password pair, user token or api key supplied in the configuration is valid.
In the examples below, the username for the bot is `errbot`.:

#### username/password pair
A successful username / password authentication is shown below:
```
$ st2 auth errbot
Password:
+----------+----------------------------------+
| Property | Value                            |
+----------+----------------------------------+
| user     | errbot                           |
| token    | 10342978da134ae5bbb7dc94d2ba9c08 |
| expiry   | 2017-09-29T14:31:20.799212Z      |
+----------+----------------------------------+
```
If the username and password are valid and correctly entered in errbot's configuration file, errbot
will be authorised to interact with StackStorm's API/Stream end points.

#### user token

Test the errbot user token from the configuration using the `st2` command.  Make
sure no environment variables are set that could provide a valid token or api key already.

```
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
```
If a list of action aliases are shown, the token is valid.

#### api key
Confirm the api key has been created and still registered with StackStorm by using it with the `st2` command.
```
$ st2 apikey list --api-key ZzVk3DEBZ4FiZmMEmDBkM2x5ZmM5jWZkZWZjZjZmMZEwYzQwZD2iYzUyM2RhYTkTNMYmNDYNODIOOTYwMzE20A
+--------------------------+--------+-------------------------------------------+
| id                       | user   | metadata                                  |
+--------------------------+--------+-------------------------------------------+
| 586e6deadbeef66deadbeef6 | errbot | {u'used_by': u'errbot api access'}        |
+--------------------------+--------+-------------------------------------------+
```


### Is Errbot connected correctly to the chat back-end?
How to test if the bot is connected to the chat back-end is dependant on the back-end.  The simplest way is to send a message to the bot user account requesting the built in help.

E.g. Using a slack client the following command would be used
```/msg @bot_name !help```.

The bot should respond with its help text.

```
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
```

### Is the StackStorm ChatOps pack installed and configured correctly?
Err-stackstorm requires the ChatOps pack to be installed.  To confirm it is installed, use the st2 cli.

```
$ st2 pack list
+-------------------+-------------------+--------------------------------+---------+----------------------+
| ref               | name              | description                    | version | author               |
+-------------------+-------------------+--------------------------------+---------+----------------------+
| chatops           | chatops           | ChatOps integration pack       | 0.2.0   | Kirill Enykeev       |
```

Confirm the `notify_errbot.yaml` is inside the `chatops/rules` directory
```
$ cat /opt/stackstorm/packs/chatops/rules/notify_errbot.yaml
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
```

The rule should be available via the st2 command `st2 rule get chatops.notify-errbot`

```
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
```


### Are events being sent via the StackStorm Stream?

From the errbot host connect to the StackStorm stream endpoint and watch for events emitted as actions
are executed by StackStorm.

```
curl -s -v -H 'Accept: text/event-stream' -H 'X-Auth-Token: 10342978da134ae5bbb7dc94d2ba9c08' http://<stackstorm_host>/stream/v1
```

### Are the events seen in the errbot logs using `errbot` as their route?

To see the events in the log, the debug level `BOT_LOG_LEVEL = logging.DEBUG` will need to be added to errbot's configuration file `config.py`.

If events are configured correctly, logs will be shown like this (`st2.announcement__errbot`)
```
17:04:12 DEBUG    root                      Dispatching st2.announcement__errbot event, 990 bytes...
17:04:12 DEBUG    lib.st2pluginapi          *** Errbot announcement event detected! ***
st2.announcement__errbot event, 990 bytes
```

If the announcement event is showing as
```
2018-01-26 15:51:55,246 DEBUG    sseclient                 Dispatching st2.announcement__chatops event, 508 bytes...
```
This indicates that the route wasn't set to `errbot`, see the Install ChatOps section.


## Acknowledgements

The err-stackstorm plugin was founded by (fmnisme)[https://github.com/fmnisme], thanks for starting the project.

## Legal

StackStorm logo used with permission by StackStorm.
Errbot logo used with permission by Errbot development team.
