# Reference material

## Stackstorm client API

### ActionAlias match
When st2client matches an actinalias, an object is returned with the following methods

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

### API call to alias_execution

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



## Errbot


### Message received from Slack backend

    msg.body
    msg.ctx
    msg.delayed
    msg.extras
    msg.flow
    msg.frm
    msg.is_direct
    msg.is_group
    msg.to

#### Private chat to bot.
    msg.body =      shinken service overview
    msg.ctx =       {}
    msg.delayed =   False
    msg.extras =    {'attachments': None}
    msg.flow =      @ch
    msg.frm =       @ch
    msg.is_direct = True
    msg.is_group =  False
    msg.to =        @prime

#### Channel chat to bot.
    msg.body =      shinken service overview
    msg.ctx =       {}
    msg.delayed =   False
    msg.extras =    {'attachments': None}
    msg.flow =      #ops/ch
    msg.frm =       #ops/ch
    msg.is_direct = False
    msg.is_group =  True
    msg.to =        #ops



### FROM CHANNEL

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

### SlackPerson

    channelid=D11LRK2LF,
    channelname=D11LRK2LF,
    client=D11LRK2LF,
    domain=XXXXXXX,
    fullname=First Last,
    nick=ch,
    person=@ch,
    userid=U110FGZSQ,
    username=ch

## Stackstorm trigger

### st2.generic.notifytrigger

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
