# Reference material

Chatops commands must traverse multiple software stacks when being sent from the users chat device
through to StackStorm's backend and back again.  The information here are based on observations of the
interactions between the adjacent components.

## Stackstorm client API

### ActionAlias match
When st2client matches an actionalias, an object is returned with the following methods
```
    class 'st2client.models.action_alias.ActionAlias'>
    ral_display_name'
    'ack'
    'action_ref'
    'description'
    'deserialize'
    'enabled'
    'extra'
    'formats'
    'get_alias'
    'get_display_name'
    'get_plural_display_name'
    'get_plural_name'
    'get_url_path_name'
    'id'
    'name'
    'pack'
    'ref'
    'result'
    'serialize'
    'to_dict'
    'uid'

    ack={'enabled': False}
    action_ref=livestatus.state_overview
    description=Get an overview of Service states via ChatOps
    deserialize=<bound method type.deserialize of
            <class 'st2client.models.action_alias.ActionAlias'>>
    enabled=True
    extra={}
    formats=['shinken service overview']
    get_alias=<bound method type.get_alias of
            <class 'st2client.models.action_alias.ActionAlias'>>
    get_display_name=<bound method type.get_display_name of
            <class 'st2client.models.action_alias.ActionAlias'>>
    get_plural_display_name=<bound method type.get_plural_display_name of
            <class 'st2client.models.action_alias.ActionAlias'>>
    get_plural_name=<bound method type.get_plural_name of
            <class 'st2client.models.action_alias.ActionAlias'>>
    get_url_path_name=<bound method type.get_url_path_name of
            <class 'st2client.models.action_alias.ActionAlias'>>
    id=5830ccebdc599a4f6bcef869
    name=state_overview
    pack=livestatus
    ref=livestatus.state_overview
    result={'format': 'Standard out says {{ execution.result.result }} ... \\o/'}
    serialize=<bound method ActionAlias.serialize of
    <ActionAlias name=state_overview,pack=livestatus,action_ref=livestatus.state_overview>>
    to_dict=<bound method ActionAlias.to_dict of
    <ActionAlias name=state_overview,pack=livestatus,action_ref=livestatus.state_overview>>
    uid=action:livestatus:state_overview
```

### API call to alias_execution

```
    curl -X POST
    -H  'Connection: keep-alive'
    -H  'Accept-Encoding: gzip, deflate'
    -H  'Accept: */*'
    -H  'User-Agent: python-requests/2.11.1'
    -H  'content-type: application/json'
    -H  'X-Auth-Token: XXXX'
    -H  'Content-Length: 200'
    --data-binary '
    {
        "notification_channel": "@prime",
        "name":                 "state_overview",
        "source_channel":       "@ch",
        "notification_route":   "errbot",
        "format":               "shinken service overview",
        "command":              "shinken service overview",
        "user":                 "@ch"
    }'
    http://127.0.0.1:9101/v1/aliasexecution
```


## Errbot

MESSAGE FROM SLACK CHANNEL TO BOT IN CHANNEL.
```
_from [<class 'yapsy_loaded_plugin_Slack_0.SlackRoomOccupant'>] #ops/ch
_extras [<class 'dict'>] {'slack_event': {'text': '.st2 test notify test test', 'source_team': 'T0V6H6HCJ', 'ts': '1506953521.000382', 'user': 'U110FGZSQ', 'type': 'message', 'channel': 'C110T9SMT', 'team': 'T0V6H6HCJ'}, 'attachments': None, 'url': 'https://infradmtest.slack.com/archives/ops/p1506953521000382'}
_flow [<class 'NoneType'>] None
_body [<class 'str'>] test notify test test
_parent [<class 'NoneType'>] None
ctx [<class 'dict'>] {}
_delayed [<class 'bool'>] False
_to [<class 'yapsy_loaded_plugin_Slack_0.SlackRoom'>] #ops


[
  {
    "name": "notify_errbot_test",
    "notification_route": "errbot",
    "command": "test notify test test",
    "format": "test notify {{tag_key}} {{tag_value}}",
    "user": "#ops/ch",
    "source_channel": "#ops",
    "notification_channel": "#ops"
  }
]
```


### Message received from Slack backend
```
    msg.body
    msg.ctx
    msg.delayed
    msg.extras
    msg.flow
    msg.frm
    msg.is_direct
    msg.is_group
    msg.to
```

#### Private chat to bot.
```
    msg.body =      shinken service overview
    msg.ctx =       {}
    msg.delayed =   False
    msg.extras =    {'attachments': None}
    msg.flow =      @ch
    msg.frm =       @ch
    msg.is_direct = True
    msg.is_group =  False
    msg.to =        @prime
```

#### Channel chat to bot.
```
    msg.body =      shinken service overview
    msg.ctx =       {}
    msg.delayed =   False
    msg.extras =    {'attachments': None}
    msg.flow =      #ops/ch
    msg.frm =       #ops/ch
    msg.is_direct = False
    msg.is_group =  True
    msg.to =        #ops
```

### FROM CHANNEL

```
    msg=['.st2 shinken service overview',
    {},
    False,
    {'attachments': None},
    <yapsy_loaded_plugin_Slack_0.SlackPerson object at 0x7fee8c48cfd0>,
    <yapsy_loaded_plugin_Slack_0.SlackPerson object at 0x7fee8c48cfd0>,
    True,
    False,
    <yapsy_loaded_plugin_Slack_0.SlackPerson object at 0x7fee8c48cef0>],
    match=<_sre.SRE_Match object; span=(0, 28), match='st2 shinken service overview'>
```

### SlackPerson
```
    channelid=D11LRK2LF,
    channelname=D11LRK2LF,
    client=D11LRK2LF,
    domain=XXXXXXX,
    fullname=First Last,
    nick=ch,
    person=@ch,
    userid=U110FGZSQ,
    username=ch
```

## Stackstorm trigger

### st2.generic.notifytrigger
```
    {
        "type": "object",
        "properties": {
            "status": {},
            "start_timestamp": {},
            "route": {},
            "runner_ref": {},
            "execution_id": {},
            "action_ref": {},
            "data": {},
            "message": {},
            "channel": {},
            "end_timestamp": {}
        }
    }
```



## MS Teams user feedback

The below error is caused by err-stackstorm not passing the conversation object to StackStorm and
getting it back again for the result response.  https://docs.microsoft.com/en-us/microsoftteams/platform/bots/how-to/conversations/send-proactive-messages?tabs=dotnet#create-the-conversation

```
16:05:53 DEBUG    errbot.plugin.st2         Message received from chat backend.
                _body [<class 'str'>] pwgen
                _from [<class 'errbot.backends.botframework.Identifier'>] {"id": "29:1pm0yCoquliuVpq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA", "name": "FirstName Surname"}
                _to [<class 'errbot.backends.botframework.Identifier'>] {"id": "28:862d35f5-8de3-4200-8af0-31da71510155", "name": "username_nick"}
                _parent [<class 'NoneType'>] None
                _delayed [<class 'bool'>] False
                _extras [<class 'dict'>] {'conversation': <errbot.backends.botframework.Conversation object at 0x7f6c28183860>}
                _flow [<class 'NoneType'>] None
                _partial [<class 'bool'>] False
                ctx [<class 'dict'>] {}
16:05:53 DEBUG    errbot.core               Triggering callback_message on Help.
16:05:53 DEBUG    urllib3.connectionpool    Starting new HTTPS connection (1): st2.example.domain:443
16:05:53 DEBUG    errbot.core               Triggering callback_message on Plugins.
16:05:53 DEBUG    errbot.core               Triggering callback_message on Utils.
16:05:53 DEBUG    errbot.core               Triggering callback_message on VersionChecker.
16:05:53 DEBUG    errbot.core               Triggering callback_message on Webserver.
16:05:53 DEBUG    errbot.core               Triggering callback_message on Example.
16:05:53 DEBUG    errbot.core               Triggering callback_message on WebserverConfiguration.
16:05:53 DEBUG    errbot.core               Triggering callback_message on St2.
16:05:53 INFO     werkzeug                  127.0.0.1 - - [01/Jul/2021 16:05:53] "POST /botframework HTTP/1.0" 200 -
16:05:53 DEBUG    urllib3.connectionpool    https://st2.example.domain:443 "POST /api/v1/actionalias/match HTTP/1.1" 200 742
16:05:53 DEBUG    urllib3.connectionpool    Starting new HTTPS connection (1): st2.example.domain:443
16:05:53 DEBUG    urllib3.connectionpool    https://st2.example.domain:443 "POST /api/v1/aliasexecution/match_and_execute HTTP/1.1" 201 6348
16:05:53 DEBUG    errbot.plugin.st2         action alias execution result: type=<class 'dict'> {'results': [{'execution': {'action': {'tags': [], 'uid': 'action:custom_linux:genpass', 'metadata_file': 'actions/
genpass.yaml', 'name': 'genpass', 'ref': 'custom_linux.genpass', 'description': 'Generiert ein Passwort', 'enabled': True, 'entry_point': '', 'pack': 'custom_linux', 'runner_type': 'local-shell-cmd', 'parameters': {'cmd': {'default': '/usr/local/bin/xkcdpass -w ger-anlx -n 4 -v [a-z] -c 5 -d _'}}, 'output_schema': {}, 'notify': {}, 'id': '5dd661df52364c5b99f2689b'}, 'runner': {'name': 'local-shell-cmd', 'description'
: 'A runner to execute local actions as a fixed user.', 'uid': 'runner_type:local-shell-cmd', 'enabled': True, 'runner_package': 'local_runner', 'runner_module': 'local_shell_command_runner', 'runner_parame
ters': {'cmd': {'description': 'Arbitrary Linux command to be executed on the host.', 'type': 'string'}, 'cwd': {'description': 'Working directory where the command will be executed in', 'type': 'string'},
'env': {'description': 'Environment variables which will be available to the command(e.g. key1=val1,key2=val2)', 'type': 'object'}, 'kwarg_op': {'default': '--', 'description': 'Operator to use in front of
keyword args i.e. "--" or "-".', 'type': 'string'}, 'sudo': {'default': False, 'description': 'The command will be executed with sudo.', 'type': 'boolean'}, 'sudo_password': {'default': None, 'description':
 'Sudo password. To be used when passwordless sudo is not allowed.', 'type': 'string', 'secret': True, 'required': False}, 'timeout': {'default': 60, 'description': "Action timeout in seconds. Action will g
et killed if it doesn't finish in timeout seconds.", 'type': 'integer'}}, 'output_schema': {}, 'id': '5b96957cbda19029aee73a46'}, 'liveaction': {'action': 'custom_linux.genpass', 'action_is_workflow': False, 'p
arameters': {}, 'callback': {}, 'runner_info': {}, 'notify': {'on-complete': {'data': {'user': '{"id": "29:1pm0yCoquliuVpq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA", "name": "
FirstName Surname"}', 'source_channel': '{"id": "29:1pm0yCoquliuVpq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA", "name": "FirstName Surname"}', 'source_context': None}, 'routes': ['
errbot']}}, 'id': '60ddcbc1779eaf3a52114346'}, 'status': 'requested', 'start_timestamp': '2021-07-01T14:05:53.323290Z', 'context': {'action_alias_ref': {'id': '5dd662b952364c7168d3a1ad', 'name': 'genpass'},
 'api_user': '{"id": "29:1pm0yCoquliuVpq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA", "name": "FirstName Surname"}', 'user': 'herbert', 'source_channel': '{"id": "29:1pm0yCoquliuV
pq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA", "name": "FirstName Surname"}', 'pack': 'custom_linux'}, 'log': [{'timestamp': '2021-07-01T14:05:53.000000Z', 'status': 'requested'}], '
web_url': 'https://st2.example.domain/#/history/60ddcbc1779eaf3a52114347/general', 'id': '60ddcbc1779eaf3a52114347'}, 'actionalias': {'uid': 'action_alias:custom_linux:genpass', 'metadata_file': 'aliases/genpass.yaml',
 'name': 'genpass', 'ref': 'custom_linux.genpass', 'description': 'Generiere ein Passwort', 'pack': 'custom_linux', 'enabled': True, 'action_ref': 'custom_linux.genpass', 'formats': ['genpass', 'pwgen'], 'ack': {'forma
t': 'Sekunde...', 'append_url': False}, 'result': {'format': '{{execution.result.stdout}}\n'}, 'extra': {}, 'immutable_parameters': {}, 'id': '5dd662b952364c7168d3a1ad'}, 'message': 'Sekunde...'}]}
16:05:53 DEBUG    urllib3.connectionpool    Starting new HTTPS connection (1): smba.trafficmanager.net:443
16:05:53 DEBUG    urllib3.connectionpool    https://smba.trafficmanager.net:443 "POST /emea/v3/conversations/a:1tjtnFy9YhaDQe_FWcXBL_wC4CsaRSs4EG6OedQ_6OmEwUqzey76DQLoEkAkJBYq5hKtQX0utNbtJXc-Ow0XfSFsKTxrAAy
5D7atE7Ydo6T6E3droyiKiYsjkC6876Rpu/activities/1625148352141 HTTP/1.1" 201 22
16:05:53 DEBUG    errbot.flow               Test if the command st2 is a trigger for an inflight flow ...
16:05:53 DEBUG    errbot.flow               None matched.
16:05:53 DEBUG    errbot.flow               Test if the command st2 is an auto-trigger for any flow ...
16:05:55 DEBUG    errbot.plugin.st2.st2_api *** Errbot announcement event detected! ***
event: st2.announcement__errbot
data: {"payload": {"extra": {}, "context": null, "message": "<random_text1>\n<random_text2>\n<random_text3>\n<random_text4>\n<random_text5>", "whisper": false, "channel": "{\"id\": \"29:1pm0yCoquliuVpq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA\", \"name\": \"FirstName Surname\"}", "user": "{\"id\
": \"29:1pm0yCoquliuVpq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA\", \"name\": \"FirstName Surname\"}"}, "trace_context": null}
<sseclient.SSEClient object at 0x7f6c2813b080>
16:05:55 DEBUG    errbot.plugin.st2.chat_ad GenericChatAdapter posting message: whisper=False, message=<random_text1>
<random_text2>
<random_text3>
<random_text4>
<random_text5>, user={"id": "29:1pm0yCoquliuVpq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA", "name": "FirstName Surname"}, channel={"id": "29:1pm0yCoquliuV
pq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA", "name": "FirstName Surname"}, extra={}
16:05:55 DEBUG    errbot.plugin.st2.chat_ad UserID: {"id": "29:1pm0yCoquliuVpq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA", "name": "FirstName Surname"}
16:05:55 DEBUG    errbot.plugin.st2.chat_ad Channel {"id": "29:1pm0yCoquliuVpq6Y_sCJ4xyDcl4fF3tCGUjfsixDb1VlQZtjSUOFsYPuEQFkr-n8eZgYnHSyCqUU4Fydi3mizA", "name": "FirstName Surname"}
16:05:55 CRITICAL errbot.plugin.st2.st2_api St2 stream listener - An error occurred: <class 'KeyError'> 'conversation'.  Backing off 10 seconds.
Traceback (most recent call last):
  File "/opt/errbot/errbot-root/data/plugins/nzlosh/err-stackstorm/lib/stackstorm_api.py", line 187, in st2stream_listener
    listener(callback, bot_identity)
  File "/opt/errbot/errbot-root/data/plugins/nzlosh/err-stackstorm/lib/stackstorm_api.py", line 177, in listener
    p.get("extra"),
  File "/opt/errbot/errbot-root/data/plugins/nzlosh/err-stackstorm/lib/chat_adapters.py", line 154, in post_message
    self.bot_plugin.send(target_id, message)
  File "/opt/errbot/venv/lib/python3.6/site-packages/errbot/botplugin.py", line 617, in send
    return self._bot.send(identifier, text, in_reply_to, groupchat_nick_reply)
  File "/opt/errbot/venv/lib/python3.6/site-packages/errbot/core.py", line 181, in send
    self.split_and_send_message(msg)
  File "/opt/errbot/venv/lib/python3.6/site-packages/errbot/core.py", line 210, in split_and_send_message
    self.send_message(partial_message)
  File "/opt/errbot/errbot-backend-botframework/botframework.py", line 214, in send_message
    response = self._build_reply(msg)
  File "/opt/errbot/errbot-backend-botframework/botframework.py", line 155, in _build_reply
    conversation = msg.extras['conversation']
KeyError: 'conversation'
16:06:05 WARNING  errbot.plugin.st2.st2_api Bot credentials re-authentication required.
16:06:05 DEBUG    errbot.plugin.st2.auth_ct Authentication User ID is 'errbot%service'
16:06:05 WARNING  errbot.plugin.st2         Internal logic error, bot session already exists.
16:06:05 DEBUG    errbot.plugin.st2.auth_ct Authentication User ID is 'errbot%service'
16:06:05 DEBUG    errbot.plugin.st2         Bot session UserID: errbot%service, Is Sealed: False, SessionID: 677af07f-5dd0-403d-9bca-ffa3d497fb1a, Creation Date: 2021-07-01 15:45:52, Modified Date: 2021-07-
01 15:45:52, Expiry Date: 2021-07-01 16:45:52
16:06:05 DEBUG    urllib3.connectionpool    Starting new HTTPS connection (1): st2.example.domain:443
16:06:05 DEBUG    urllib3.connectionpool    https://st2.example.domain:443 "GET /api/v1/ HTTP/1.1" 200 76
16:06:05 DEBUG    errbot.plugin.st2         StackStorm authentication succeeded.
16:06:05 DEBUG    errbot.plugin.st2.auth_ct Authentication User ID is 'errbot%service'
16:06:05 DEBUG    errbot.plugin.st2.auth_ct Get token for session id 677af07f-5dd0-403d-9bca-ffa3d497fb1a
16:06:05 DEBUG    urllib3.connectionpool    Starting new HTTPS connection (1): st2.example.domain:443
16:06:05 DEBUG    urllib3.connectionpool    https://st2.example.domain:443 "GET /stream/v1/stream HTTP/1.1" 200 None
```
