# Out of Band Authentication

## Overview

Out of band authentication is the use of a distinct communication channel for authenticating a chat
backend user accounts with StackStorm.

StackStorm provides Role Based Access Control (RBAC) to control the privileges of StackStorm 
authenticated users.   StackStorm integrates with chat backends through the use of a bot.  The bot 
mediates between the StackStorm API and chat backend.  The bot authenticates with the
StackStorm API and exposes Workflows to the chat backend in the form of Action Aliases. Historically, these
action aliases were executed using the bot's API credentials, but this approach masks StackStorm's RBAC
from chat users.

To take advantage of RBAC, the chat user must be able to provide authentication credentials.  In some cases it is undesirable
to send these credentials over the chat service itself.  For this reason Out of Bands Authentication support is added to err-stackstorm.
The user can trigger an authentication request.  Err-stackstorm will provide a one-time usable URL with a session (unique identification).  This is to limit access to the authentication page and prevent repeated connection attempts to the same session id.

The user may supply a username/password pair, user token or api token that will be associated with session id.  It is the session id that will
associate the chat service user identification with the StackStorm API credentials.

Once successfully authenticated, when an action aliases is called, Err-stackstorm will lookup the chat backend user identification in its cached 
credentials store and provide the corresponding StackStorm user token/api key to the StackStorm API.


## Setup

### nginx

Nginx is used as a reverse proxy to errbot's webserver.  Nginx should perform TLS and authentication.

#### limitation

Clear text in memory doesn't provides weak secret protection.

### security considerations

Use ssl client certificates for auth page.
