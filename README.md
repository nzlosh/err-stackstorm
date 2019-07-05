# err-stackstorm
A plugin to run StackStorm actions, bringing StackStorm's ChatOps to Errbot.

## Table of Contents
1. [Help](#Help)
1. [Installation](#Installation)
1. [Requirements](#Requirements)
1. [Supported Chat Backends](#SupportedChatBackends)
1. [Configuration](#Configuration)
1. [Setup Action-Aliases](#ActionAliases)
1. [Webhook](#Webhook)
1. [Server-Side Events](#ServerSideEvents)
1. [ChatOps Pack](#ChatOpsPack)
1. [Troubleshooting](#Troubleshooting)

## Help <a name="GettingHelp">

You can find users of err-stackstorm on Gitter.  https://gitter.im/err-stackstorm/community or Slack https://stackstorm-community.slack.com `#err-stackstorm`.  There's also the comprehensive [troubleshooting](#Troubleshooting) section to help guide you through possible break/fix scenarios.

If you think you've found a bug or need a new feature open an issue on the [github repository](https://github.com/nzlosh/err-stackstorm/issues).

If you want to contribute to the err-stackstorm project, there are plenty of improvements to be made, contact nzlosh via chat or email to discuss how you can get involved.

## Installation <a name="Installation"></a>
Installation of the err-stackstorm plugin can be performed from within a running Errbot instance.  Ensure Errbot is up and running before attempting to install the plugin.  See the Errbot installation documentation here https://github.com/errbotio/errbot for instructions on how to setup Errbot on your chat back-end.  These instructions assume a running instance of StackStorm is already in place.  See the official [StackStorm documentation](https://docs.stackstorm.com/install/index.html) for details.

 1. Install Errbot on the target system using standard package manager or Errbot installation method.
 1. Configure Errbot, see the [Configuration](#Configuration) section for help.
 1. Enable Errbot's internal web server, see the [Webhook](#Webhook) section for help.
 1. Install ChatOps pack on StackStorm, see the [ChatOps Pack](#ChatOpsPack) section for help.
 1. Connect to your chat back-end and starting interacting with your StackStorm/Errbot instance.

After completing the above steps, issue The below command will install the plugin.

 1. Confirm Errbot is configured to install plugin dependencies. The below line should be present in `config.py`, if it is not add it.
    ```
    AUTOINSTALL_DEPS = True
    ```
 1. From the chat backend, issue the command to install err-stackstorm.
    ```
    !repos install https://github.com/nzlosh/err-stackstorm.git
    ```
*The plugin will fail to install if any errors are encountered.  This is often caused by configuration errors in `config.py`.*

## Requirements <a name="Requirements"></a>
The plugin has been developed and tested against the below software combinations.  For optimal operation it is recommended to use the following versions:

plugin tag (version) | Python | Errbot | StackStorm client
--- | --- | --- | ---
2.1 | 3.6 | 6.0.0 | not used
2.0 | 3.4 | 5.2.0 | 2.10
1.4 | 3.4 | 5.1.2 | 2.5
1.3 | 3.4 | 5.1.2 | 2.5
1.2 | 3.4 | 5.0   | 2.2
1.1 | 3.4 | 4.3   | 2.2
1.0 | 2.7 | 3.x   | 2.1

Nginx to serve static content.

## Supported Chat Back-ends <a name="SupportedChatBackends"></a>
Errbot provides official support for most major chat back-ends and many more chat back-ends are available through unofficial plugins.

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
`api_auth.apikey` | Errbot API key to authenticate with StackStorm.  Used instead of a username/password pair or user token.
`timer_update` | Unit: seconds.  Default is *60*. Interval for err-stackstorm to the user token is valid.
`rbac_auth.standalone` | Standalone authentication.
`rbac_auth.clientside` | Clientside authentication, a chat user will supply StackStorm credentials to err-stackstorm via an authentication page.
`rbac_auth.clientside.url` | Url to the authentication web page.
`secrets_store.cleartext` | Use the in memory store.


### Locale
Errbot uses the systems locale for handling text, if you're getting errors handling non-ascii characters from chat
`UnicodeEncodeError: 'ascii' codec can't encode character '\xe9' in position 83: ordinal not in range(128)`

Make sure the systems locale is configured for unicode encoding.  In the below example, the machine
was set the English (`en`) New Zealand (`NZ`) with utf-8 encoding (`.UTF8`).

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

#### ClearText
The `cleartext` store maintains the cache in memory and does not encrypt the contents to disk.  This is option doesn't protect the stored secrets in memory.


### StackStorm Authentication Credentials

#### Standalone RBAC Authentication

This is the original authentication method where err-stackstorm used its own credentials for all
calls to the StackStorm API.  All action-alias' issued by chat service users execute the underlying
workflows with err-stackstorm credentials.  Any Role Based Access Control policies would only be
applied to the bot user which gives coarse control.


##### Standalone RBAC Configuration
Do not configure multiple RBAC authentication configurations at the same time.
An empty dictionary in the *standalone* key is all that is required to maintain err-stackstorm's
original authentication method.
```
    'rbac_auth': {
        'standalone': {},
    },
```

#### Client-side Authentication

err-stackstorm provides a way to associate the chat service user account with a StackStorm
username/password or api token.

This implementation is specific to err-stackstorm.  It is achieved by requesting a new
authentication session with err-stackstorm.  A Universally Unique Identifier (UUID) is generated
for the session and the chat user is invited to follow a URL to the authentication page hosted by
errbot.  For security reasons, the UUID is a one time use and is consumed when the page is
accessed.  Any subsequent attempts to access the page will result in an error.

The login page must be protected by TLS encryption and ideally require an ssl client certificate.
The login page should not be exposed directly to the internet, but have a reverse proxy such as
nginx placed between it and any external service consumers.

The user enters their StackStorm credentials via the login page which err-stackstorm will validate
against the StackStorm API.  If the credentials are valid, the user token or api key will be cached
by err-stackstorm and the supplied credentials discarded.

Once a chat user is associated with their StackStorm credentials, any action-alias will be executed
using the associated StackStorm credentials.


##### Client-side authentication configuration

The are two parts to configuring Client-side authentication,  1. nginx's 2. errbot's.  Nginx is used
to serve static web content for the authentication web page and errbot functions as an API for authentication calls.

###### nginx configuration

This example is provided as a guide and you are expected to know and understand how to configure nginx for your environment.  It is outside the scope of this documentation to explain [SSL certificates](https://www.google.com/search?q=ssl+certificate+nginx+tutorial).

The below example does not show how to secure access using ssl client certificates despite it being highly recommended for use in production.

To help understand the example below, the follow is assumed:
 * the nginx server is running on the same host as errbot.
 * the hosts fully qualified domain name is `my_host.my_fqdn`.
 * nginx listens on the ip address for `my_host.my_fqdn` TCP port 443 with ssl enabled.
 * errbot's webserver listens on the ip address `127.0.0.1` TCP port 3141 without ssl enabled.
 * errbot's plugins directory is `/data/errbot/plugins`
 * err-stackstorm is installed in `/data/errbot/plugins/nzlosh/err-stackstorm`.
 * the ssl certificate and private key used by nginx are called `errbot.crt` and `errbot.key`.

You will need to update the configuration to *match your environment*.

```
server {
  listen       my_host.my_fqdn:443 ssl;
  server_name  my_host.my_fqdn;

  ssl on;

  ssl_certificate           /etc/ssl/errbot.crt;
  ssl_certificate_key       /etc/ssl/errbot.key;
  ssl_session_cache         shared:SSL:10m;
  ssl_session_timeout       5m;
  ssl_protocols             TLSv1 TLSv1.1 TLSv1.2;
  ssl_ciphers               EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:ECDHE-RSA-AES128-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA128:DHE-RSA-AES128-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA128:ECDHE-RSA-AES128-SHA384:ECDHE-RSA-AES128-SHA128:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA384:AES128-GCM-SHA128:AES128-SHA128:AES128-SHA128:AES128-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4;
  ssl_prefer_server_ciphers on;

  index  index.html index.htm;

  access_log            /var/log/nginx/ssl-errbot.access.log combined;
  error_log             /var/log/nginx/ssl-errbot.error.log;

  add_header              Front-End-Https on;
  add_header              X-Content-Type-Options nosniff;

  location /login/ {
    proxy_pass            http://127.0.0.1:3141$request_uri;
    proxy_read_timeout    90;
    proxy_connect_timeout 90;
    proxy_redirect        off;

    proxy_set_header      Host my_host.my_fqdn;
    proxy_set_header      X-Real-IP $remote_addr;
    proxy_set_header      X-Forwarded-For $proxy_add_x_forwarded_for;

    proxy_set_header Connection '';
    chunked_transfer_encoding off;
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Host my_host.my_fqdn;
  }

  location / {
    root      /data/errbot/plugins/nzlosh/err-stackstorm/html/;
    index     index.html index.htm;
  }
}
```
After successfully setting up nginx, the client side authentication url would be `https://my_host.my_fqdn:443/`

###### err-stackstorm configuration

A *url* is required to correctly configure client-side authentication for ChatOps.
```
    'rbac_auth': {
        'clientside': {
            'url': 'https://<hostname>:<port>/'
        }
    },
```

Option | Description
--- | ---
`url` | Errbot's authentication web server end point.  Used for the client-side authentication web page.

## Errbot ACLs
Errbot comes with native Access Control List support.  It can be configured to constrain command execution by grouping `command`, `channel` and `user`.  Glob patterns can be used in each field to provide flexibility in ACL definitions.

As an example,  a StackStorm instance has an automatic package upgrade workflow.  Its progress can be viewed by executing the action alias: `apu stats <role>`, which is defined as shown below.

```
| action_ref    | st2dm_apu.apu_status                                         |
| formats       | [                                                            |
|               |     {                                                        |
|               |         "representation": [                                  |
|               |             "apu status {{role}}"                            |
|               |         ],                                                   |
|               |         "display": "apu status <role>"                       |
|               |     }                                                        |
|               | ]                                                            |
```
The below Errbot ACL configuration allows `@user1` to view the status of the upgrade, but not start/stop the upgrade process (they are other action aliases that are triggered with `st2 apu ...`)
```
ACL_SQUAD_INFRA = ["@admin1", "@admin2", "@admin3", "@admin4"]
ACL_APU_USERS = ['@user1']
ACL_EVERYONE = ["*"]
ACCESS_CONTROLS = {
    'whoami': {
        'allowrooms': ['@bot_user'],
        'allowusers': ACL_EVERYONE
    },
    'st2 apu status*':{
        'allowrooms': ['#channel'],
        'allowusers': ACL_SQUAD_INFRA + ACL_APU_USERS
    },
    'st2 apu*':{
        'allowrooms': ['#channel'],
        'allowusers': ACL_SQUAD_INFRA
    },
}
```

Getting the correct usernames to fill into `allowusers`/`denyusers` isn't obvious.  On a small
scale it's possible to use the `!whoami` command to get the correct user account name.  For large
installation it'd make more sense to use a pre-defined pattern.

Errbot matches `username` against the ACL definition.  This information isn't found easily in the Slack interface.  Use errbot's `!whoami`  command to find the value from the `nick` field which can be used with ACL definitions.


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
!plugin config Webserver {'HOST': '0.0.0.0', 'PORT': 3141, 'SSL': {'enabled': False, 'host': '0.0.0.0', 'port': 3142, 'certificate': '', 'key': ''}}
```

**NOTE:** _The variables must be adjusted to match the operating environment in which Errbot is running.  See Errbot documentation for further configuration information._

---
### Optional
The configuration above is only applied for the current runtime and may not persist after the errbot
process is restarted.  Making the configuration change permanent is as simple as installing a
special plugin:

```
!repos install https://github.com/tkit/errbot-plugin-webserverconfiguration
```
The configuration command from above is not required prior to installing this plugin.

In production environments it may be desirable to place a reverse-proxy like nginx in front of errbot.

## Send notifications to Errbot from StackStorm using Server-Side Events (SSE) <a name="ServerSideEvents"></a>

As of StackStorm 1.4. server-sent events (SSE) were added which allowed ChatOps messages to be
streamed from StackStorm to a connected listener (err-stackstorm in our case).  The StackStorm
stream url must be supplied in the configuration so err-stackstorm knows where to establish the
http connection.  The SSE configuration is complementary to the webhook method and both must be
enabled for full ChatOps support between StackStorm and Errbot.

## StackStorm ChatOps pack configuration. <a name="ChatOpsPack"></a>

StackStorm's [ChatOps pack](https://github.com/StackStorm/st2/tree/master/contrib/chatops) is required to be installed and a notify rule file added to the pack.

The notify rule must be placed in `/<stackstorm installation>/packs/chatops/rules`.  The rule file [notify_errbot.yaml](https://raw.githubusercontent.com/nzlosh/err-stackstorm/master/contrib/stackstorm-chatops/rules/notify_errbot.yaml) can be found in this repository under

Edit the `chatops/actions/post_message.yaml` file to use the errbot route as it's default value.
```
  route:
    default: "errbot"
```

## Troubleshooting <a name="Troubleshooting"></a>

### Is the virtual environment active?

If Errbot was installed in a python virtual environment and a `command is not found` is reported.
```
errbot --init, the command is not found.
```
Make sure the virtual environment is activated correctly.

### Is the Errbot process running?
Check an instance of Errbot is running on the host
```
# ps faux | grep errbo[t]
root     158707  0.1  0.0 2922228 59640 pts/21  Sl+  Aug14   2:29  |   \_ /opt/errbot/bin/python3 /opt/errbot/bin/errbot -c /data/errbot/etc/config.py
```

### Is the Errbot webhook listening?
Check Errbot's internal web server is listening on the correct interface.  Use the PID `158707` from the previous command to filter the output to find which port the errbot process is listening on.  If the result is empty, errbot is not listening on any ports.
```
# ss -tlpn | grep 158707
LISTEN     0      128                       *:3141                     *:*      users:(("errbot",158707,21))
```
OR
```
# netstat -tlpn | grep 158707
tcp        0      0 0.0.0.0:3141            0.0.0.0:*               LISTEN      158707/python3
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
err-stackstorm requires the ChatOps pack to be installed.  To confirm it is installed, use the st2 cli.

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

A special thank you to [fmnisme](https://github.com/fmnisme) who started the err-stackstorm plugin project.
Thanks to the StackStorm and Errbot community for their support and interest.


## Legal

StackStorm logo used with permission by StackStorm.
Errbot logo used with permission by Errbot development team.
