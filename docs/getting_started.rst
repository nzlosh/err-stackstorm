.. _getting_started:

****************
Getting Started
****************

.. contents:: :local:

Overview
=========

`err-stackstorm` is a community project to bring StackStorm `ChatOps <https://docs.stackstorm.com/chatops/index.html>`_ to `Errbot <http://errbot.io/en/latest/index.html>`_ and not officially supported by StackStorm or Errbot maintainers.  `err-stackstorm` enables StackStorm's `Action Aliases <https://docs.stackstorm.com/chatops/aliases.html>`_ in your chat environment, where you and your team can manage aspects of infrastructure, code and 3rd party services.

The objectives for err-stackstorm project are:
 1. Provide a Python friendly ChatOps solution.
 1. Maintain the same high quality as the StackStorm project.
 3. Collaborate with the StackStorm community to evolve ChatOps features.
 4. Match or exceed hubot-stackstorm features.

Features
========

err-stackstorm communicates directly with the StackStorm API from with an errbot instance.

     - List action-alias help dynamically.  When StackStorm action-aliases are updated, they are immediately available in the err-stackstorm output.  Filtering by pack name and keyword can be used when looking for help.
     - Access-Control Lists based on any combination of chat username, command and room.  ACLs are defined in the errbot configuration file.
     - Associate StackStorm user credentials with chat usernames.  Client-Side authenticate lets err-stackstorm dynamically map chat user accounts with StackStorm authenticated users.  Credentials are passed via an out of band authentication web page.
     - Trigger action-aliases directly from the bot.
     - Support for multiple chat backends, as provided by errbot.
     - Customise plugin prefix.
     - Customise StackStorm route key to allow more than one bot to be connected to a single StackStorm instance.
     - Docker image available to get up and running quickly and easily.
     - Python based using modern 3.6 features.

Compatibility
==============

The plugin has been developed and tested against the below software combinations. Because you might be running different Python or Errbot versions, the below are the optimal combinations:


   .. csv-table:: Ideal Combination of Versions
      :header: "err-stackstorm", "Python", "Errbot", "StackStorm Client"
      :widths: 15, 10, 10, 20

      "2.2", "3.7+", "6.1.9", "not used"
      "2.1", "3.6+", "6.0.0", "not used"
      "2.0", "3.4", "5.2.0", "2.10"
      "1.4", "3.4", "5.1.2", "2.5"
      "1.3", "3.4", "5.1.2", "2.5"
      "1.2", "3.4", "5.0", "2.2"
      "1.1", "3.4", "4.3", "2.2"
      "1.0", "2.7", "3.x", "2.1"

Platforms
=========

``err-stackstorm`` is developed and testing on the x86_64 platform for Linux.  No other platforms or operating systems have been tested.

    .. important:: ``err-stackstorm`` has  been reported by users to have issue running on Mac OSX.

Supported Chat Backends
=========================

Errbot provides official support for most major chat back-ends and many more chat back-ends are available through unofficial community plugins.


   .. csv-table:: Supported Chat Backends
         :header: "Backend", "Mode value", "Support Type"
         :widths: 10, 10, 10

         "Text", "text", "Integrated"
         "IRC", "irc", "Integrated"
         "XMPP", "xmpp", "Integrated"
         "Slack", "slack", "`Plugin <https://github.com/errbotio/err-backend-slackv3>`_"
         "Mattermost", "mattermost", "`Plugin <https://github.com/errbotio/err-backend-mattermost>`_"
         "Rocket Chat", "aoikrocketchaterrbot", "`Plugin <https://github.com/AoiKuiyuyou/AoikRocketChatErrbot>`_"
         "Gitter", "gitter", "`Plugin <https://github.com/errbotio/err-backend-gitter>`_"
         "Discord", "discord", "`Plugin <https://github.com/errbotio/err-backend-discord>`_"

    .. csv-table:: Unsupported Chat Backends
        :header: "Backend", "Mode value", "Support Type"
        :widths: 10, 10, 10

        "MSTeam", "BotFramework", "`Plugin <https://github.com/vasilcovsky/errbot-backend-botframework>`_"

.. important:: ``err-stackstorm`` doesn't support MSTeams due to lack of access by the developer, if you're intersted in adding and maintaining MSTeams support please contact nzlosh on slack/gitter or github.

Backend support provides a minimum set of operations such as `connect` and `authentication` methods along with ways to `identify` and `send messages` to users/rooms.

Advanced formatting may not be available on all backends since additional code would be required in `err-stackstorm` to translate StackStorm's Action Aliases `extra` parameter.


Backends that currently support nice (extra) formatting:

   * Slack
   * XMPP
