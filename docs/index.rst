.. err-stackstorm documentation master file, created by
   sphinx-quickstart on Fri Jun 14 09:32:01 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to err-stackstorm's documentation!
==========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Introduction
============

err-stackstorm is an unofficial community project to bring StackStorm ChatOps to Errbot.  The goals of the
project are:

 1. Emulate hubot-stackstorm features.
 2. Provide a Python friendly ChatOps solution.
 3. Respect StackStorm's enterprise offering.
 4. Maintain the same high quality as the StackStorm project.
 5. Collaborate with the StackStorm community to evolve ChatOps features.

Features
========

err-stackstorm communicates directly with the StackStorm API from with an errbot instance.

 - List action-alias help dynamically.  When StackStorm action-aliases are updated, they are immediately
   available in the err-stackstorm output.  Filtering by pack name and keyword can be used when look for help.
 - Access-Control Lists based on any combination of chat username, command and room.  ACLs are
   defined in the errbot configuration file.
 - Associate StackStorm user credentials with chat usernames.  Client-Side authenticate lets err-stackstorm
   dynamically map chat user accounts with StackStorm authenicated users via an authenticationn web page.
 - Trigger action-aliases directly from
 - Support for multiple chat services, as provided by errbot.
 - Docker image available to get up and running quickly and easily.
 - Python based using modern 3.6 features.
