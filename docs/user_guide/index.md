---
title: User Guide
description: >
    Detailed guides on using each component of TitleCardMaker.
---

# User Guide

!!! warning "Under Construction"

    This documentation is actively being developed.

!!! warning "Not for New Users"

    The User Guide __is not__ intended to be an introduction to TitleCardMaker
    for new users - it is a detailed reference for those already familiar with
    the basics. New users should follow the
    [Getting Started](../getting_started/index.md) tutorial.

## Pages

The TitleCardMaker interface is separated into various pages which can be
navigated to via the sidebar or buttons on the header. Each page is detailed
below:

- [Series](./series.md)
- [Adding Series](./new_series.md)
- [Recently Added](./recent.md)
- [Missing Summary](./missing.md)
- [Templates](./templates.md)
- [Fonts](./fonts.md)
- [Sync](./syncs.md)
- [Settings](./settings.md)
- [Connections](./connections.md)
- [Scheduler](./scheduler.md)
- [Importer](./importer.md)
- [System Summary](./system.md)
- [Logs](./logs.md)
- [Graphs](./graphs.md)
- [Changelog](./changelog.md)

## Selecting a Branch / Tag

TitleCardMaker follows the typical design pattern of lots of software packages,
separating changes which are "in development" and "finalized". As a result, you
have the option of selecting between either of these branches (or _tags_) for
your version of TCM.

!!! warning "Develop Branches / Tags"

    If using the `develop` version of TCM, expect to encounter bugs which may
    require frequently updating. If this sounds cumbersome, stick to the `main`
    branch.

!!! warning "Backwards Compatibility"

    If there are changes to the TCM database schema, these are often
    __irreversible__ - meaning swapping from `develop` to `main` is not
    possible.

### Docker

| Tag Name        | Description                                               | Recommended For..                        |
| :-------------: | :-------------------------------------------------------: | :--------------------------------------- |
| `latest`        | The most up-to-date (stable) release                      | Most users[^1]                           |
| `main`          | _Same as `latest`_                                        | It's recommended to use `latest`         |
| `develop`       | The most feature-rich (unstable) release                  | Those wanting to try the latest features |
| `main-armv7`    | Same as `latest`, but for those on an ARMv7 architecture  | _See `latest`_                           |
| `develop-armv7` | Same as `develop`, but for those on an ARMv7 architecture | _See `develop`_                          |

### Non-Docker

| Branch Name | Description                              | Recommended For..                        |
| :---------: | :--------------------------------------: | :--------------------------------------- |
| `main`      | The most up-to-date (stable) release     | Most users[^1]                           |
| `develop`   | The most feature-rich (unstable) release | Those wanting to try the latest features |

## Environment Variables

??? tip "Specifying an Environment Variable"

    === ":material-docker: :fontawesome-solid-file-code: Docker Compose"

        Add all environment variables under the `environment` section of your
        compose file, like so:

        ```yaml title="docker-compose.yml" hl_lines="5-6"
        name: titlecardmaker
        services:
          tcm:
            # etc.
            environment:
              - TZ=America/Los_Angeles
              - TCM_CONSOLE_LOG_LEVEL=WARNING
            # etc.
        ```

    === ":material-docker: Docker"

        Specify the environment variable with the `-e` commands in your Docker
        run command, like so:

        ```bash
        -e TZ=America/Los_Angeles -e TCM_CONSOLE_LOG_LEVEL=WARNING
        ```

    === ":material-language-python: Non-Docker"

        The easiest method is to create a file named `.env` in the main TCM
        installation directory (where you type your `python` command) - like so:

        ```ini title=".env"
        TZ=America/Los_Angeles
        TCM_CONSOLE_LOG_LEVEL=WARNING
        ```

All configuration that can be set via environment variables uses the `TCM_` prefix.
Variables are read from the process environment and, when present, from a `.env` file
in the application root. The following reference documents every available variable.

### Application & runtime

`TCM_IS_DOCKER`

:   Set to `TRUE` when TCM is running inside Docker (e.g. for paths and behavior).
    Usually set by the image; you typically do not need to set this yourself.

`TCM_TESTING`

:   Set to `TRUE` to enable testing mode. Default is `FALSE`.

### Authentication

`TCM_DISABLE_AUTH`

:   When set to `TRUE`, authentication is disabled and existing users are removed.
    Only read at startup. For details, see [Connections — Forgotten login](./connections.md#forgotten-login).
    Default is `FALSE`.

`TCM_AUTH_EXPIRATION_DAYS`

:   Number of days authentication tokens remain valid. Integer between 1 and 120.
    Default is `7`.

`TCM_CRYPTO_ALGORITHM`

:   Algorithm used for token signing. Default is `HS256`.

### Backups

`TCM_BACKUP_RETENTION_DAYS`

:   Number of days to keep backups before they are deleted. Integer ≥ 1.
    Default is `21`.

`TCM_BACKUP_DT_FORMAT`

:   Strftime-style format for backup folder names. Default is `%Y-%m-%d_%H-%M-%S`.

### Logging

`TCM_CONSOLE_LOG_LEVEL`

:   Minimum log level for console (stdout) output. One of: `TRACE`, `DEBUG`, `INFO`,
    `WARNING`, `ERROR`, `CRITICAL`. Default is `INFO`.

`TCM_DATABASE_LOG_LEVEL`

:   Minimum log level for messages stored in the logging database. Same level
    options as above. Default is `TRACE`; changing this can make debugging harder.

`TCM_WEBSOCKET_LOG_LEVEL`

:   Minimum log level for live log messages in the UI (see
    [Settings — Display live log messages](./settings.md#display-live-log-messages)).
    Same level options as above. Default is `INFO`.

`TCM_CONSOLE_LOG_WIDTH`

:   Width of console log output in characters. Integer ≥ 40, or leave unset for
    automatic width.

`TCM_INTERCEPT_PLEX_LOGS`

:   Set to `TRUE` to send Plex API log messages through TCM’s logging. Default is
    `FALSE`. For more Plex options, see [Plex variables](#plex-variables).

`TCM_PACKAGE_LOGGING`

:   Comma-separated list of package names whose loggers should be intercepted by
    TCM’s logging. Empty by default.

`TCM_LOG_RETENTION_DAYS`

:   Number of days to keep log files before deletion. Integer ≥ 1. Default is `7`.

### Data retention

`TCM_UNSYNCED_SERIES_RETENTION_DAYS`

:   Number of days to keep series that have not been synced. Integer ≥ 1.
    Default is `10`.

### Integrations & card types

`TCM_SONARR_REQUEST_TIMEOUT`

:   Sonarr request timeout in seconds. Integer between 10 and 10000. Default is `500`.

`TCM_CARD_TYPE_REPOSITORY`

:   Base URL of the card type repository (e.g. GitHub raw URL). Default points to
    the official TitleCardMaker/CardTypes repository branch for your version.

`TCM_IMAGEMAGICK_CONTAINER`

:   Name or ID of a Docker container used to run ImageMagick commands. Use when
    TCM runs on the host but ImageMagick runs in a container. Unset by default.

### ImageMagick (optional)

`TCM_IM_PATH`

:   Path to the ImageMagick executable (e.g. `convert` or `magick`) when not
    using the default on `PATH` or a Docker container. Can also be set via
    [Settings](./settings.md). Unset by default.

### Timezone

`TZ`

:   Timezone used for local time (e.g. in logs and UI). Standard timezone name
    (e.g. `America/Los_Angeles`). A list is available
    [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). If unset,
    the system local timezone is used, or `UTC` as fallback.

### Plex Variables

TCM uses the [plexapi](https://github.com/pkkid/python-plexapi) module to
communicate with Plex, and as such can be configured by configuring their
assigned environment variables - these are all detailed
[here](https://python-plexapi.readthedocs.io/en/stable/configuration.html).

The most popular one is the API timeout - `PLEXAPI_PLEXAPI_TIMEOUT`.

[^1]:
    Unless you've encountered a bug which you personally _require_ and is only
    available on `develop`.
