.. _authorisation:

***************
Authorisation
***************

.. contents:: :local:


Errbot Access Control List
==========================

Errbot comes with native Access Control List support.  It can be configured to constrain command execution by grouping ``command``, ``channel`` and ``user``.  Glob patterns can be used in each field to provide flexibility in ACL definitions.

As an example, a StackStorm instance has an automatic package upgrade workflow.  Its progress can be viewed by executing the action alias: ``apu stats <role>``, which is defined as shown below::

    | action_ref    | st2_apu.apu_status                                           |
    | formats       | [                                                            |
    |               |     {                                                        |
    |               |         "representation": [                                  |
    |               |             "apu status {{role}}"                            |
    |               |         ],                                                   |
    |               |         "display": "apu status <role>"                       |
    |               |     }                                                        |
    |               | ]                                                            |

The Errbot ACL configuration below allows ``@user1`` to view the status of the upgrade, but *not to start/stop* the upgrade process, which are other action-aliases that are triggered with ``st2 apu ...``)

.. code-block:: python

    ACL_SQUAD_INFRA = ["@admin1", "@admin2", "@admin3", "@admin4"]
    ACL_APU_USERS = ['@user1']
    ACL_EVERYONE = ["*"]
    ACCESS_CONTROLS = {
        'whoami': {
            'allowrooms': ['@bot_user'],
            'allowusers': ACL_EVERYONE
        },
        'st2 apu status*':{
            'allowrooms': ['#channel'],
            'allowusers': ACL_SQUAD_INFRA + ACL_APU_USERS
        },
        'st2 apu*':{
            'allowrooms': ['#channel'],
            'allowusers': ACL_SQUAD_INFRA
        },
    }

Getting the correct usernames to fill into ``allowusers`` or ``denyusers`` isn't always obvious.  Use errbot's ``!whoami`` command to get the correct username for use within ACL definitions.  The `nick` value is what should be used in the configuration in the case of Slack.

.. warning:: UI interface names do not always match with the internal nickname/username. ``!whoami`` is a surefire way of retrieving the correct username.

On a small scale it's possible to use the ``!whoami`` command to get the correct user account name but for large installations it'd make more sense to use pre-defined patterns.
