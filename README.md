#err-stackstorm
A plugin to run Stackstorm actions.  This brings Stackstorm's chatops
functionality to errbot.


##Install
```
!repos install https://github.com/nzlosh/err-stackstorm.git
```


##Configuration
Edit `config.py` which contains the configuration which is used to define how the plugin will communicate with Stackstorm's API and Authenticate end points.

###Authentication
The errbot plugin must have valid credentials to use Stackstorm's API.  The credentials may be username/password, user token or api key.  See https://docs.stackstorm.com/authentication.html for more details.

####Username/Password
Using a username and password will allow errbot to renew the user token when it expires.  Do not enter a _User Token_ when you want to use username/password authentication.
####User Token
If using a username and password doesn't meet the requirements for the environment errbot is operating inside, it's possible to supply a pre-generated _User Token_ as supplied by StackStorm.  Note when the token expires, a new one must be generated and updated in `config.py`.
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
    'timer_update': 60 # Unit: second.  Interval for errbot to refresh to list of available action aliases.
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

API Key support has been provisioned but hasn't been implmented to date.


##Send message from stackstorm to errbot

As of writing, this feature hasn't been implemented.  The original author of errbot left this feature to be implemented by others with the follow message:

> If you want to send a message from Stackstorm to errbot, you should write a simple httpserver in your backend, and post message to your backend just like `hubot.post_message` does in stackstorm.

If time permits, this will be implemented in the near future.

