.. _getting_started:

****************
Getting Started
****************

.. contents:: :local:

Overview
=========

`err-stackstorm` is an unofficial community project to bring StackStorm ChatOps to Errbot. Using `err-stackstorm` you will be able to leverage `Errbot <http://errbot.io/en/latest/index.html>`_ as the `ChatOps <https://docs.stackstorm.com/chatops/index.html>`_ of your choice for controlling Stackstorm using **conversation-driven development** by using Stackstorm's `Action Aliases <https://docs.stackstorm.com/chatops/aliases.html>`_.

 1. Emulate hubot-stackstorm features.
 2. Provide a Python friendly ChatOps solution.
 3. Respect StackStorm's enterprise offering.
 4. Maintain the same high quality as the StackStorm project.
 5. Collaborate with the StackStorm community to evolve ChatOps features.

.. important:: `st2chatops` does not have to be running on your StackStorm instance. This plugin *replaces* `st2chatops`.

Features
========

err-stackstorm communicates directly with the StackStorm API from with an errbot instance.

     - List action-alias help dynamically. When StackStorm action-aliases are updated, they are immediately available in the err-stackstorm output. Filtering by pack name and keyword can be used when look for help.
     - Access-Control Lists based on any combination of chat username, command and room. ACLs are defined in the errbot configuration file.
     - Associate StackStorm user credentials with chat usernames.  Client-Side authenticate lets err-stackstorm dynamically map chat user accounts with StackStorm authenicated users via an authenticationn web page.
     - Trigger action-aliases directly from the bot.
     - Support for multiple chat backends, as provided by errbot.
     - Docker image available to get up and running quickly and easily.
     - Python based using modern 3.6 features.

Compatibility
==============

The plugin has been developed and tested against the below software combinations. Because you might be running different Python or Errbot versions, we provide here the combinations to achieve optimal operation:


   .. csv-table:: Ideal Combination of Versions
      :header: "err-stackstorm", "Python", "Errbot", "Stackstorm Client"
      :widths: 15, 10, 10, 20

      "2.1", "3.6+", "6.0.0", "not used"
      "2.0", "3.4", "5.2.0", "2.10"
      "1.4", "3.4", "5.1.2", "2.5"
      "1.3", "3.4", "5.1.2", "2.5"
      "1.2", "3.4", "5.0", "2.2"
      "1.1", "3.4", "4.3", "2.2"
      "1.0", "2.7", "3.x", "2.1"


Supported Chat Backends
=========================

Errbot provides official support for most major chat back-ends and many more chat back-ends are available through unofficial plugins.


   .. csv-table:: Supported Chat Backends
         :header: "Backend", "Mode value", "Support Type"
         :widths: 10, 10, 10

         "Slack", "slack", "Integrated"
         "Text", "text", "Integrated"
         "XMPP", "xmpp", "Integrated"
         "Mattermost", "mattermost", "Plugin"
         "Rocket Chat", "aoikrocketchaterrbot", "Plugin"
         "Gitter", "gitter", "Plugin"
         "Discord", "discord", "Plugin"

Backend support provides a minimum set of operations such as `connect` and `authentication` methods along with ways to `identify` and `send messages` to users/rooms.

Advanced formatting may not be available on all backends since additional code would be required in `err-stackstorm` to translate Stackstorm's Action Aliases `extra` parameter.


Backends that currently support nice (extra) formatting:

   * Slack
   * XMPP

