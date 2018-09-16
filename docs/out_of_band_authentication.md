# Out of Band Authentication

## Overview

Out of band authentication is the use of a distinct communication channel for authenticating a chat
backend user accounts with StackStorm.

StackStorm provides Role Based Access Control (RBAC) to control the privileges of StackStorm 
authenticated users.   StackStorm integrates with chat backends through the use of a bot.  The bot 
mediates between the StackStorm API and chat backend.  Historically, the bot authenticates with the
StackStorm API and exposes Workflows to the chat backend in the form of Action Aliases.

To take advantage of RBAC, the chat user must provide authentication credentials.  It may be undesirable
to send these credentials over the chat made.

When action aliases are called, Err-stackstorm will lookup the chat backend user in it's cached 
credentials store and provided the corresponding StackStorm user token to the StackStorm API.


## Setup

### nginx

### vault

### keyring

#### limitation
must unlock the keyring manually when the bot starts.

### security considerations

use ssl client certificates for auth page.
keyring should be considered a weak security mechanism.

