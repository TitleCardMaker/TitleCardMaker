---
title: User Guide
description: >
    Detailed guides on using each component of TitleCardMaker.
---

# User Guide

!!! note "Not for New Users"

    The User Guide __is not__ intended to be an introduction to TitleCardMaker
    for new users - it is a detailed reference for those already familiar with
    the basics. New users should follow the
    [Getting Started](../getting_started/index.md) tutorial.

## Pages

The TitleCardMaker interface is separated into various pages which can be
navigated to via the sidebar or buttons on the header. Each page is detailed
below, grouped by how you are likely to use them.

### Library & Series

<div class="grid cards" markdown>

-   ![Series](../assets/series-light.webp#only-light){.no-lightbox href="./series.md"}
    ![Series](../assets/series-dark.webp#only-dark){.no-lightbox}

    **[Series](./series.md)**

    ---

    All Series-specific customizations and actions.

-   ![Adding Series](../assets/add_series-light.webp#only-light){.no-lightbox}
    ![Adding Series](../assets/add_series-dark.webp#only-dark){.no-lightbox}

    **[Adding Series](./new_series.md)**

    ---

    Manually adding a Series or Blueprint.

-   ![Recently Added](./assets/recent-light.webp#only-light){.no-lightbox}
    ![Recently Added](./assets/recent-dark.webp#only-dark){.no-lightbox}

    **[Recently Added](./recent.md)**

    ---

    Viewing recently created Title Cards and recently added Series.

-   ![Missing Summary](./assets/missing-light.webp#only-light){.no-lightbox}
    ![Missing Summary](./assets/missing-dark.webp#only-dark){.no-lightbox}

    **[Missing Summary](./missing.md)**

    ---

    Summary of missing Title Cards, missing Logos, and unloaded Title Cards.

</div>

### Design

<div class="grid cards" markdown>

-   ![Templates](./assets/templates-light.webp#only-light){.no-lightbox}
    ![Templates](./assets/templates-dark.webp#only-dark){.no-lightbox}

    **[Templates](./templates.md)**

    ---

    Create, customize, and view Templates for bulk-editing settings.

-   ![Fonts](../assets/fonts_light.webp#only-light){.no-lightbox}
    ![Fonts](../assets/fonts_dark.webp#only-dark){.no-lightbox}

    **[Fonts](./fonts.md)**

    ---

    Create, customize, and view custom Fonts.

</div>

### Automation

<div class="grid cards" markdown>

-   ![Sync](./assets/sync-light.webp#only-light){.no-lightbox}
    ![Sync](./assets/sync-dark.webp#only-dark){.no-lightbox}

    **[Sync](./syncs.md)**

    ---

    Creating and editing Syncs to automatically add Series to TCM.

-   ![Scheduler](./assets/scheduler_basic-light.webp#only-light){.no-lightbox}
    ![Scheduler](./assets/scheduler_basic-dark.webp#only-dark){.no-lightbox}

    **[Scheduler](./scheduler.md)**

    ---

    The schedulable Tasks which automatically perform all major operations.

</div>

### Configuration

<div class="grid cards" markdown>

-   ![Settings](./assets/settings-light.webp#only-light){.no-lightbox}
    ![Settings](./assets/settings-dark.webp#only-dark){.no-lightbox}

    **[Settings](./settings.md)**

    ---

    In-depth descriptions of all global settings.

-   ![Connections](./assets/connections-light.webp#only-light){.no-lightbox}
    ![Connections](./assets/connections-dark.webp#only-dark){.no-lightbox}

    **[Connections](./connections.md)**

    ---

    Add connections to external services like Plex, Sonarr, Tautulli, or TMDb.

</div>

### Monitoring

<div class="grid cards" markdown>

-   ![System Summary](./assets/system-light.webp#only-light){.no-lightbox}
    ![System Summary](./assets/system-dark.webp#only-dark){.no-lightbox}

    **[System Summary](./system.md)**

    ---

    Viewing the system details.

-   ![Logs](./assets/logs-light.webp#only-light){.no-lightbox}
    ![Logs](./assets/logs-dark.webp#only-dark){.no-lightbox}

    **[Logs](./logs.md)**

    ---

    Viewing and filtering logs within the UI.

-   ![Graphs](./assets/graphs-light.webp#only-light){.no-lightbox}
    ![Graphs](./assets/graphs-dark.webp#only-dark){.no-lightbox}

    **[Graphs](./graphs.md)**

    ---

    Visualizing database snapshots and scheduled task durations over time.

</div>

### Other

<div class="grid cards" markdown>

-   :material-history:{ .lg .middle } **[Changelog](./changelog.md)**

    ---

    Release notes and version history for TitleCardMaker.

-   :material-console:{ .lg .middle } **[Command Line Image Creation](./command_line/index.md)**

    ---

    Create Title Cards and posters from the command line for testing,
    debugging, and one-off image generation.

</div>

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
