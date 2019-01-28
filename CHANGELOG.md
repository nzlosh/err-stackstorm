
# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [2.0.0-rc1] 2019-01-28
### Added
 - setup.py to be able to install plugin from the command line.
 - Dockerfile to build an image and run err-stackstorm from within a Docker container. (alpine linux based)
 - Support for Out-of-Bands authentication.
 - Support for formatting with XMMP backend.

### Changed
 - Updated err-stacksotorm python module requirements.

### Removed

## [1.4.0] - 2018-04-07
### Added


### Changed
 - Readme spelling corrections.
 - Aligned `api_url`, `auth_url` and `stream_url` with the [StackStorm API](https://api.stackstorm.com/)


### Removed
 - remove `base_url` and `api_version`, they're now calculated from the `api_url`, `auth_url` or `stream_url`.
