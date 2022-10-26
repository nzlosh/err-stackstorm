.. _action_aliases:

****************
Action Aliases
****************

.. note:: This section assumes you have little to no familiarity with StackStorm.  If that's not the case, you may skip it.

Overview
---------

`Action Aliases <https://docs.stackstorm.com/chatops/aliases.html>`_ are a StackStorm feature that helps *exposing actions to the bot*.  Their main purpose is to provide a *simple human readable* representation of actions, very useful in text-based interfaces, notable ChatOps.

Generally speaking, you can expose any action to the bot.  You can list them using `st2 action-alias list`.

Creating a simple action alias
-------------------------------

Let's create a simple action alias to demonstrate `err-stackstorm`.  Aliases are deployed via packs so let's create one quickly::

  mkdir -p /<st2path>/packs/errtest/aliases


Create a file inside the ``aliases`` folder named ``run_remote.yaml`` and paste the yaml defined below:

.. code-block:: yaml

    ---
    name: "local_shell_cmd"
    action_ref: "core.local"
    description: "Execute a command on a remote host via SSH."
    formats:
      - "run {{cmd}}"
    result:
      format: "operation completed {~} {{ execution.result }}"

After that, ask StackStorm to reload its configuration::

  st2ctl reload --register-all

.. note:: Errbot will automatically refresh its action alias list when you add or remove aliases on StackStorm.  Type ``!st2help`` to your bot on the chat to list available StackStorm commands.

In this example ``local_shell_cmd`` is an alias for the ``core.local`` action.  If you want to run a command against a remote host, you could have used the ``core.remote`` action.

The supported format for the alias is specified in the formats field.  A single alias can support multiple formats for the same action.  The result will then be returned to `err-stackstorm` and Errbot will propagate that back to your chat backend.

Usage
------

Once the alias is setup, talk to your bot and type::

  !st2 run date

The bot will answer your request using the ``result.format`` definition::

  operation completed {~} Sun Jul  7 02:08:58 PDT 2019


Formatting
----------

Jinja Template
==============

.. seealso:: Don't forget to check St2 official documentation on `Action Aliases <https://docs.stackstorm.com/chatops/aliases.html>`_.

Here's an example of an action-alias that runs a command on a list of remote hosts and outputs the results nicely formatted on **Slack**.


.. code-block:: yaml

    ---
    name: "remote_shell_cmd"
    action_ref: "core.remote"
    description: "Execute a command on a remote host via SSH."
    formats:
      - "run {{cmd}} on {{hosts}}"
    result:
       format: |
          Ran command *{{execution.parameters.cmd}}* on *{{ execution.result | length }}* hosts.

          {% for host in execution.result %}
          \*Host\*: {{host}} {{ ":white_check_mark:" if execution.result[host].stdout else ":x:" }}
          \`\`\`{{ execution.result[host].stdout or execution.result[host].stderr or "No result"}}\`\`\`
          {% endfor %}

The alias above will format the execution output per host once it gathers the results.  The sheer amount backticks and escaping are due to particularities between Errbot and Slack - this may not work in another chat backend.

This is how the bot will answer you on Slack:

.. image:: images/remote_shell.jpg

Slack Attachments
=================

.. note:: Slack considers attachments as legacy formatting.  Use block formatting whenever possible.  Support for attachments in this form of dictionary may be removed from err-stackstorm in the future.

Slack's Markdown can get you a long way, but there are some occasions a richer message format is preferable.

Attachments were the first form of advanced message formatting provided by Slack.  StackStorm ChatOps pack allows you to
supply a `slack` key inside the `extra` parameter.  The `slack` key can hold the set of attributes related to sending an attachment.
Information on the available attachment fields can be found here.  https://api.slack.com/reference/messaging/attachments#legacy_fields

.. code-block:: bash
    st2 run chatops.post_message route=errbot_slack channel='<#CL8HNNTFY>' message='Attachments Test' extra='
    {
        "slack": {
            "color": "#f48527",
            "pretext": "Hey <!channel>, Ready for ChatOps?",
            "title": "SaltStack and ChatOps.  Get started :rocket:",
            "title_link": "https://stackstorm.com/2015/07/29/getting-started-with-stackstorm-and-saltstack/",
            "author_name": "by Jurnell Cockhren, CTO and Founder of SophicWare",
            "author_link": "http://sophicware.com/",
            "author_icon": "https://stackstorm.com/wp/wp-content/uploads/2015/01/favicon.png",
            "image_url": "https://i.imgur.com/vOU2SC0.png",
            "fields": [{
                "title": "Documentation",
                "value": "https://docs.stackstorm.com/chatops/",
                "short": true
            }]
        }
    }'



Slack Blocks
============

Blocks have replaced Attachments as Slack's preferred method of advanced message formatting.  Blocks allow interaction as well as formatting.
Attachments can be used inside blocks to provide secondary information to the primary message but their display is not guaranteed by Slack.

.. code-block:: bash
    st2 run chatops.post_message route=errbot_slack channel='<#CL8HNNTFY>' message='Blocks' extra='{
        "slack": {
            "blocks": [{
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "This is a plain text section block with jinja template interpolation {{ execution.id }}.",
                    "emoji": true
                }
            }, {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "This is a *section* block with an ~image~ text _formatting_."
                }
            }, {
                "type": "image",
                "title": {
                    "type": "plain_text",
                    "text": "Slack Errbot StackStorm SaltStack",
                    "emoji": true
                },
                "image_url": "https://i.imgur.com/vOU2SC0.png",
                "alt_text": "SESS"
            }]
        }
    }'


.. important:: Advanced formatting may not be available to all chat backends since each backend requires specific code to translate St2 `extra` parameter.
