---
title: Environment Variables
description: >
    Reference for TitleCardMaker environment variables configured at startup.
---

# Environment Variables

TitleCardMaker reads global, startup-only settings from environment variables
and from an optional `.env` file in the application root.

All TitleCardMaker-specific variables use the `TCM_` prefix (for example,
`TCM_CONSOLE_LOG_LEVEL` controls console logging verbosity).

!!! note "Runtime vs environment"

    Environment variables cannot be changed while TCM is running. User-facing
    options such as the ImageMagick executable path are stored in
    [Settings](./settings.md) instead.

## Setting variables

??? tip "Specifying an environment variable"

    === ":material-docker: :fontawesome-solid-file-code: Docker Compose"

        Add variables under the `environment` section of your compose file:

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

        Pass variables with `-e` in your `docker run` command:

        ```bash
        -e TZ=America/Los_Angeles -e TCM_CONSOLE_LOG_LEVEL=WARNING
        ```

    === ":material-language-python: Non-Docker"

        Create a `.env` file in the TitleCardMaker root directory (next to where
        you start TitleCardMaker):

        ```ini title=".env"
        TZ=America/Los_Angeles
        TCM_CONSOLE_LOG_LEVEL=WARNING
        ```

### Value formats

#### Booleans

Use `TRUE` or `FALSE`. Docker Compose examples often use uppercase. Some
variables (such as `TCM_IS_DOCKER`) require exactly `TRUE` to take effect.

#### Log levels

Log level variables accept **only** one of the following values (case-sensitive):

| Value | Typical use |
| :---- | :---------- |
| `TRACE` | Very detailed diagnostic output |
| `DEBUG` | Detailed information for troubleshooting |
| `INFO` | General operational messages (default for most logs) |
| `WARNING` | Something unexpected, but TCM can continue |
| `ERROR` | A failure that prevented an operation |
| `CRITICAL` | A serious failure |

Messages at or above the configured level are recorded. For example, with
`TCM_CONSOLE_LOG_LEVEL=WARNING`, `INFO` and `DEBUG` messages are not shown in
the console.

#### Integers

Use decimal digits. Minimum and maximum values are listed on each variable
below. Omit a variable entirely to use its default.

## Application and runtime

`TCM_IS_DOCKER`

:   Set to `TRUE` when TCM runs inside Docker. Affects config and log paths
    (`/config` vs a local `config/` directory). The official image sets this
    automatically; you usually do not need to set it yourself.

    **Allowed values:** `TRUE` only (must be uppercase `TRUE` to enable Docker
    paths). Any other value is treated as not running in Docker.

`TCM_TESTING`

:   Enable testing mode. Intended for development and troubleshooting only;
    leave unset in normal use.

    **Allowed values:** `TRUE`, `FALSE`. **Default:** `FALSE`.

## Authentication

`TCM_DISABLE_AUTH`

:   When `TRUE`, authentication is disabled and existing users are removed at
    startup. See
    [Connections — Forgotten login](./connections.md#forgotten-login).

    **Allowed values:** `TRUE`, `FALSE`. **Default:** `FALSE`.

`TCM_AUTH_EXPIRATION_DAYS`

:   Days that authentication tokens remain valid.

    **Allowed values:** Integer from `1` to `120`. **Default:** `7`.

`TCM_CRYPTO_ALGORITHM`

:   Algorithm used to sign login tokens.

    **Default:** `HS256`.

## Backups

`TCM_BACKUP_RETENTION_DAYS`

:   Days to keep backups before deletion.

    **Allowed values:** Integer `1` or greater. **Default:** `21`.

`TCM_BACKUP_DT_FORMAT`

:   Date and time format for backup subfolder names. Uses standard format codes
    such as `%Y` (four-digit year), `%m` (month), `%d` (day), `%H` (hour), and
    `%M` (minute).

    **Default:** `%Y-%m-%d_%H-%M-%S`.

## Logging

`TCM_CONSOLE_LOG_LEVEL`

:   Minimum level for console output.

    **Allowed values:** `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
    **Default:** `INFO`.

`TCM_DATABASE_LOG_LEVEL`

:   Minimum level for messages stored in the logging database.

    **Allowed values:** `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
    **Default:** `DEBUG`.

`TCM_WEBSOCKET_LOG_LEVEL`

:   Minimum level for live log messages in the UI. See
    [Settings — Display live log messages](./settings.md#display-live-log-messages).

    **Allowed values:** `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
    **Default:** `INFO`.

`TCM_CONSOLE_LOG_WIDTH`

:   Console log width in characters.

    **Allowed values:** Integer `40` or greater, or leave unset for automatic
    width.

`TCM_INTERCEPT_PLEX_LOGS`

:   Route Plex API log messages through TCM logging.

    **Allowed values:** `TRUE`, `FALSE`. **Default:** `FALSE`.

`TCM_PACKAGE_LOGGING`

:   Comma-separated list of software component names whose log output TCM should
    capture (for example `httpx,urllib3`).

    **Default:** empty (no extra components).

`TCM_LOG_RETENTION_DAYS`

:   Days to keep log files.

    **Allowed values:** Integer `1` or greater. **Default:** `7`.

## Data retention

`TCM_UNSYNCED_SERIES_RETENTION_DAYS`

:   Days to keep series that have not been synced.

    **Allowed values:** Integer `1` or greater. **Default:** `10`.

## Request timeouts

All timeouts are in seconds.

`TCM_EMBY_REQUEST_TIMEOUT`

:   Emby API timeout.

    **Allowed values:** Integer from `10` to `10000` (seconds). **Default:** `30`.

`TCM_JELLYFIN_REQUEST_TIMEOUT`

:   Jellyfin API timeout.

    **Allowed values:** Integer from `10` to `10000` (seconds). **Default:** `30`.

`TCM_PLEX_REQUEST_TIMEOUT`

:   Plex API timeout for TitleCardMaker.

    **Allowed values:** Integer from `10` to `10000` (seconds). **Default:** `30`.

    Additional Plex client settings use separate `PLEXAPI_*` variables; see
    [Plex-related variables](#plex-related-variables) below.

`TCM_SONARR_REQUEST_TIMEOUT`

:   Sonarr API timeout.

    **Allowed values:** Integer from `10` to `10000` (seconds). **Default:** `500`.

`TCM_IMAGEMAGICK_REQUEST_TIMEOUT`

:   ImageMagick command timeout.

    **Allowed values:** Integer from `1` to `600` (seconds). **Default:** `60`.

## Card types and ImageMagick

`TCM_CARD_TYPE_REPOSITORY`

:   Base URL of the remote card type repository. By default, TitleCardMaker
    downloads card types from the official
    [TitleCardMaker/CardTypes](https://github.com/TitleCardMaker/CardTypes)
    repository for your installed version.

    **Allowed values:** Any valid URL. Leave unset to use the built-in default
    for your version.

`TCM_IMAGEMAGICK_CONTAINER`

:   Docker container name or ID used to run ImageMagick commands when TCM runs
    on the host but ImageMagick runs in a container.

    **Allowed values:** Any Docker container name or ID, or leave unset.

## Timezone

`TZ`

:   Timezone used for local time in logs and the UI. Not a `TCM_` variable, but
    TitleCardMaker reads it at startup.

    **Allowed values:** A
    [timezone identifier](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
    from the _TZ Identifier_ column (for example `America/Los_Angeles`,
    `Europe/London`, `UTC`). If unset, the system local timezone is used, with
    `UTC` as a fallback.

## Plex-related variables

TitleCardMaker's Plex connection also respects environment variables documented
by the [Plex API client](https://python-plexapi.readthedocs.io/en/stable/configuration.html).

A commonly used option is `PLEXAPI_PLEXAPI_TIMEOUT` (Plex API timeout in
seconds). This is separate from `TCM_PLEX_REQUEST_TIMEOUT`.
