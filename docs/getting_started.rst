.. _getting_started:

****************
Getting Started
****************

.. contents:: :local:

Overview
=========

`err-stackstorm` is a community project to bring StackStorm `ChatOps <https://docs.stackstorm.com/chatops/index.html>`_ to `Errbot <http://errbot.io/en/latest/index.html>`_.  `err-stackstorm` exposes StackStorm's `Action Aliases <https://docs.stackstorm.com/chatops/aliases.html>`_ to your chat environment, where you and your team can manage aspects of infrastructure and code.

The objectives for err-stackstorm project are:
 1. Provide a Python friendly ChatOps solution.
 2. Maintain the same high quality as the StackStorm project.
 3. Collaborate with the StackStorm community to evolve ChatOps features.

Features
========

err-stackstorm communicates directly with the StackStorm API from with an errbot instance.

     - List action-alias help dynamically.  When StackStorm action-aliases are updated, they are immediately available in the err-stackstorm output.  Filtering by pack name and keyword can be used when looking for help.
     - Access-Control Lists based on any combination of chat username, command and room.  ACLs are defined in the errbot configuration file.
     - Associate StackStorm user credentials with chat usernames.  Client-Side authenticate lets err-stackstorm dynamically map chat user accounts with StackStorm authenticated users.  Credentials are passed via an out of band authentication web page.
     - Trigger action-aliases directly from the bot.
     - Support for multiple chat backends, as provided by errbot.
     - Customise plugin prefix to allow more than one bot to occupy the same chat channel.
     - Customise StackStorm route key to allow more than one bot to be connected to a single StackStorm instance.
     - Docker build file available to get up and running quickly and easily.
     - Python based using modern 3.x features.

Compatibility
==============

err-stackstorm v2.2 is compatible with Python 3.7+ and operates with StackStorm v3.0.0 and newer


Supported Chat Backends
=========================

Errbot provides official support for most major chat back-ends and many more chat back-ends are available through unofficial plugins.


   .. csv-table:: Supported Chat Backends
         :header: "Backend", "Mode value", "Support Type"
         :widths: 10, 10, 10

         "Slack", "slackv3", "https://github.com/errbotio/err-backend-slackv3"
         "Mattermost", "mattermost", "`Plugin <https://github.com/errbotio/err-backend-mattermost>`_"
         "Discord", "discord", "`Plugin <https://github.com/errbotio/err-backend-discord>`_"
         "Rocket Chat", "aoikrocketchaterrbot", "`Plugin <https://github.com/AoiKuiyuyou/AoikRocketChatErrbot>`_"
         "Gitter", "gitter", "`Plugin <https://github.com/errbotio/err-backend-gitter>`_"
         "MS Teams", "BotFramework", "`Unsupported by err-stackstorm` <https://github.com/vasilcovsky/errbot-backend-botframework>`_"
         "XMPP", "xmpp", "Integrated"
         "IRC", "irc", "Integrated"

Backend support provides a minimum set of operations such as `connect` and `authentication` methods along with ways to `identify` and `send messages` to users/rooms.

Advanced formatting may not be available on all backends since additional code would be required in `err-stackstorm` to translate StackStorm's Action Aliases `extra` parameter.

.. warning:: Microsoft Teams is available in errbot but is not supported by err-stackstorm because the maintainer has no access to this service.  If you wish to help maintain support for Microsoft Teams in err-stackstorm contact nzlosh.

Backends that currently support nice (extra) formatting:

   * Slack
   * XMPP

