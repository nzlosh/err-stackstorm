# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

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
