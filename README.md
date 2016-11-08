#err-stackstorm
A plugin to run Stackstorm actions.  This brings Stackstorm's chatops
functionality to errbot.


##Install
```
!repos install https://github.com/fmnisme/err-stackstorm.git
```


##Configuration
Edit `config.py` configuration file which is used to define how the plugin will communicate with Stackstorm's API and authentication end points.

###Authentication
The errbot plugin must have valid credentials to use Stackstorm's API.  The credentials may be;

 - username/password
 - user token
 - api key

See https://docs.stackstorm.com/authentication.html for more details.

####Username/Password
Using a username and password will allow errbot to renew the user token when it expires.  If a _User Token_ is supplied, it will over-ride username/password authentication.

####User Token
To avoid using the username/password pair in a configuration file, it's possible to supply a pre-generated _User Token_ as supplied by StackStorm.  Note when the token expires, a new one must be generated and updated in `config.py`.

####API Key
Provisions have been made to implement support for _API Key_ support in the future.  As of the writing of this document, it is not implemented.

```
STACKSTORM = {
    'base_url': 'https://stackstorm.example.com',
    'auth_url': 'https://stackstorm.example.com/auth',
    'api_url': 'https://stackstorm.example.com/api/v1',
    'api_version': 'v1',
    'api_auth': {
        'user': {
            'name': 'my_username',
            'password': "my_password",
            'token': "<User token>",
        },
        'key': '<API Key>'
    },
    'timer_update': 60, # Unit: second.  Interval for errbot to refresh to list of available action aliases.
    'web_server': {
        'enable': true
        'port': 8888
    }
}
```


##Commands
 1. Connect errbot to your chat environment.
 2. Write an action alias in Stackstorm.
 3. Either restart errbot or wait for the refresh interval for errbot to update the action alias list.
 4. Type `!st2help` in your chat program for the list of available commands.
 5. Type the desired command in your chat program, as shown in the help.


##Authentication
Authentication is possible with username/password or User Token.  In the case of a username and password, the plugin is able to request a new User Token after it expires.

API Key support has been provisioned but hasn't been implemented to date.


##Send message from stackstorm to errbot

Errbot has a built in webserver.  It is configured and enabled through the bots admin chat interface.
It listens for Stackstorm's chatops messages and delivers them to the attached chat backend.

Configure errbot's webserver plugin.
```
!plugin config Webserver {'HOST': '0.0.0.0',
'PORT': 8888,
'SSL': {'certificate': '',
'enabled': False,
'host': '0.0.0.0',
'key': '',
'port': 8889}}
```

Enable to webserver plugin.
```
!plugin activate Webserver
```
