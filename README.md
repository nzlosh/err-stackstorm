#err-stackstorm
Plugin to run action-alias in Stackstorm.

##Install
```
!repos install https://github.com/nzlosh/err-stackstorm.git
```

##Edit config.py
The configuration defines how the plugin will communicate with the Stackstorm's API and Authenticate end points.

###Authentication
The errbot plugin must authenticate itself to be able to interface with the Stackstorm API.  See https://docs.stackstorm.com/authentication.html for more details.

####Username/Password
Using a username and password will allow errbot to renew the user token when it expires.  Do not enter a _User Token_ when you want to use username/password authentication.
####User Token
If it using a username and password isn't sufficiently secure for the environment errbot is operating, it's possible to supply a pre-generated _User Token_ as supplied by StackStorm.
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
    'timer_update': 60 #second. auto update patterns and help from st2.
}
```
##Commands
1. Write alias in stackstorm.
2. Type `!st2help` in errbot.

##Authentication
Authentication is possible with username/password or User Token.  In the case of a username and password, the plugin is able to request a new User Token after it expires.

API Key support has been provisioned but hasn't been implmented to date.

##How to send message from stackstorm to errbot?

As of writing, this feature hasn't been implemented.  The original author of errbot left this feature to be implemented by others with the follow message:

> If you want to send a message from Stackstorm to errbot, you should write a simple httpserver in your backend, and post message to your backend just like `hubot.post_message` does in stackstorm.

If time permits, this will be implemented in the near future.
