# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

##  [2.4.0] Unreleased

### Added

### Changed

### Removed

##  [2.3.2] 2025-09-28

### Added

### Changed
  - Fixed python path in systemd unit file.
  - Used correct user id/channel id with postMessage when using blocks in Slack chat adapter.
  - Updated dockerfile to use ubuntu22.04 and python3.10
  - Fixed version number in documentation.

### Removed

##  [2.3.1] 2025-07-11

### Added
  - Added Ubuntu 24 and Debian 12 to package build.

### Changed
  - Display ANSI colour correctly in makefile.
  - Removed redundant testing of the extra.slack key.
  - Used version.py as reference for building packages.

### Removed
  - Removed Ubuntu 18 and Debian 10 from package build.

##  [2.3.0] 2025-07-05
### Added
  - Proof of concept for enquiry support.
  - Add Python 3.12 to test matrix.
  - Option to use an empty plugin_prefix

### Changed
  - Restructured source layout for pypi packaging.
  - Restructured and updated documentation.
  - Switched from setup.py to pyproject.toml
  - Updated package build process to support Rocky linux and base on major version of OS.
  - Use plugin_prefix in help command hint

### Removed
  - Removed `check_latest_version` function.
  - Removed CircleCI from project in favour of using Github Actions.
  - Removed Python 3.7 & 3.8 from test matrix.
  - Removed detection of 'block' key from _post_block_message() which was causing messages to be silently ignored.

##  [2.2.0] 2021-11-27
### Added
  - support for slackv3 backend and passing action-alias extra parameters as Slack block or attachment.
  - documentation to use Slack blocks or attachments.
  - tests for Python from 3.6 to 3.10

### Changed
  -  hard coded notification_route to use user configured route when calling match_and_execute.

### Removed
  - logging sensitive api tokens in debug logs.
  - "<action-alias>" for action execution help text.

##  [2.1.4] 2020-08-14
### Added
  - Session are deleted automatically when a chat user fails to authenticate against St2 API.
  - Include Slack users "display name" in session list for easier identification.

### Changed
  - Update documentation with corrections and improved examples.
  - Corrected error of dynamic commands not registering correctly when the plugin was deactivated/activated.
  - Improved robustness of version check code to gracefully handle github.com being unavailable.

##  [2.1.3] 2020-01-10
### Added
  - Added err-stackstorm version in the st2help display.

### Changed
  - Fixed st2help function to have to correct number of positional arguments.

##  [2.1.2] 2019-11-24
### Added
  - Added CircleCI build badge to README.
  - Added route key to be defined by user to allow mutliple bots attached to a single StackStorm instance.
  - Added version check on start-up to log if newer version of the plugin are available.

### Changed
  - Updated curl example in troubleshooting section.
  - Changed all bot commands to be registered dynamically to allow user defined plugin prefix.

##  [2.1.1] 2019-07-19
### Added
  - Added configuration for mattermost, rocketchat, discord, gitter and slack to docker build.

### Changed
  - Improved Discord Chat Adapter formatting.
  - Corrected configuration name handling which caused exceptions to be raised.
  - Updated documentation to direct readers to readthedocs.

### Removed
  - Removed old readme file.

## [2.1.0] 2019-07-08
### Added
  - Added `deactivate` method to correctly handle errbot reload and stop process.
  - Added initial files for documentation to be served on readthedocs.
  - Added missing documentation for nginx configuration when using Client-side authentication.
  - Added support for IRC and Discord Chat Adapters.
  - Added source documentation for ReadTheDocs.

### Changed
  - Correctly detect when the `extra` attribute is passed to the Slack Chat Adapter.
  - Send web login form data as JSON to be compatible with errbot >=v6.0.

### Removed

## [2.1.0-rc2] 2019-05-29
### Added
  - Split unit tests in separate test files.
  - Added linting to CircleCI
  - Added try/except blocks around plugin configuration code to improve installation and startup
    experience when there are errors in the configuration.

### Changed
  - Fixed dictionary keys to reference 'apikey' consistently.
  - Switch CircleCI from calling pytest directly to using Makefile.
  - Dropped using sseclient-py in favour of btubbs sseclient.
  - Corrected references to apikey configuration.

### Removed

## [2.1.0-rc1] 2019-05-15
### Added
  - unit tests for more low level objects used by err-stackstorm.

### Changed
  - updated makefile to be better adapted to CircleCI's build process.  (Still a work in progress)
  - numerous documentation updates to improve installation process for new users.
  - documented errbot's ACL features.

### Removed
  - removed unused code for keyring and vault.

## [2.0.0-rc2] 2019-02-08
### Added
  - Correctly support action-alias acknowledge enabled flag in StackStorm API.
  - Support appending the execution `web_url` to action-alias acknowledgement message.

### Changed
  - Fixed exception raise in log message when err-stackstorm isn't able to fetch a valid StackStorm user token.

### Removed
  - removed dependency for st2client to be able to use requests>=2.20.  This avoid conflicts with popular chat backends.

## [2.0.0-rc1] 2019-01-28
### Added
 - setup.py to be able to install plugin from the command line.
 - Dockerfile to build an image and run err-stackstorm from within a Docker container. (alpine linux based)
 - Support for Out-of-Bands authentication.
 - Support for formatting with XMMP backend.

### Changed
 - Updated err-stackstorm python module requirements.

### Removed

## [1.4.0] - 2018-04-07
### Added


### Changed
 - Readme spelling corrections.
 - Aligned `api_url`, `auth_url` and `stream_url` with the [StackStorm API](https://api.stackstorm.com/)


### Removed
 - remove `base_url` and `api_version`, they're now calculated from the `api_url`, `auth_url` or `stream_url`.
