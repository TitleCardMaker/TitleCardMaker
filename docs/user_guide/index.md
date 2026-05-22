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

All TitleCardMaker environment variables use the `TCM_` prefix. Variables are read
from the process environment and, when present, from a `.env` file in the
application root.

See the [Environment Variables](./environment_variables.md) reference for every
available variable, defaults, and constraints.

[^1]:
    Unless you've encountered a bug which you personally _require_ and is only
    available on `develop`.
