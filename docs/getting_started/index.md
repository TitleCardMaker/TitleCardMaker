---
title: Getting Started
description: >
    Acquaint yourself with the basics of TitleCardMaker - from installation to
    Title Card creation.
---

# Getting Started

??? "Migrating from an existing installation?"

    If you have previously used TitleCardMaker version 1 and are simply
    migrating to version 2, see the [Migration Guide](./migrating.md) for help
    with what steps to take.

## Installation

There are several ways to install TitleCardMaker - Docker Compose, Docker,
non-Docker, and Unraid. Docker Compose is generally recommended because it comes
with all the requirements (Python, ImageMagick, etc.), and does not require
copying any long commands.

Unraid users can directly add the container as a "template" within the UI.

=== ":material-docker: :fontawesome-solid-file-code: Docker Compose"

    1. Open a terminal[^1] of your choice, and go to your desired install
    location.

        ??? example "Example"

            === ":material-linux: Linux"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker"
                ```

            === ":material-apple: MacOS"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker"
                ```

            === ":material-powershell: Windows (Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker'
                ```

            === ":material-microsoft-windows: Windows (Non-Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker'
                ```

    2. Determine your timezone, a full list is available
    [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). You
    will want to take note of the text in the _TZ Identifier_ column - e.g.
    `America/Los_Angeles` - for the next step.

    3. Write the following contents to a file named `docker-compose.yml` in your
    desired install directory (from Step 1):

        ```yaml title="docker-compose.yml" hl_lines="11 12 14"
        name: titlecardmaker
        services:
          tcm:
            image: "ghcr.io/titlecardmaker/titlecardmaker:latest" # (4)!
            container_name: titlecardmaker
            restart: unless-stopped
            network_mode: bridge
            ports:
              - 4242:4242
            environment:
              - TZ=America/Los_Angeles # (1)!
              # (3)
            volumes:
              - ~/Your/Install/Directory/TitleCardMaker/config:/config # (2)!
        ```

        1. Replace this with your timezone.
        2. Replace this with your install directory.
        3. You may also add add `PGID`, `PUID`, and `UMASK` here as environment
        variables if you want to control the permissions of TCM.
        4. To use the 'experimental' branch, change `:latest` to `:develop`

    4. Create (and launch) the Docker container by executing the following
    command.

        ```bash
        docker compose up -d
        ```

    7. Verify your volumes are mapped correctly by looking for a `db.sqlite`
    file inside the `config` directory. If you do not see one, then correct the
    volumes specified in Step 3 (double check your quotes are in the correct
    position).

=== ":material-docker: Docker"

    1. Open a terminal[^1] of your choice, and go to your desired install
    location.

        ??? example "Example"

            === ":material-linux: Linux"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker"
                ```

            === ":material-apple: MacOS"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker"
                ```

            === ":material-powershell: Windows (Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker'
                ```

            === ":material-microsoft-windows: Windows (Non-Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker'
                ```

    2. Determine your timezone, a full list is available
    [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). You
    will want to take note of the text in the _TZ Identifier_ column - e.g.
    `America/Los_Angeles` - for the next step.

    3. Create (and launch) the Docker container by executing the following
    command - make sure to replace the install directory and timezone with
    _your_ directory (from Step 1) and timezone (from Step 2).

        === ":material-linux: Linux"

            ```bash
            docker run -itd --net="bridge" -v "~/Your/Install/Directory/TitleCardMaker/config/":"/config/" -e TZ="America/Los_Angeles" -p 4242:4242 --name "TitleCardMaker" "ghcr.io/titlecardmaker/titlecardmaker:latest"
            ```

        === ":material-apple: MacOS"

            ```bash
            docker run -itd --net="bridge" -v "~/Your/Install/Directory/TitleCardMaker/config/":"/config/" -e TZ="America/Los_Angeles" -p 4242:4242 --name "TitleCardMaker" "ghcr.io/titlecardmaker/titlecardmaker:latest"
            ```

        === ":material-powershell: Windows (Powershell)"

            ```bash
            docker run -itd --net="bridge" -v "C:/Your/Install/Directory/TitleCardMaker/config":"/config/" -e TZ="America/Los_Angeles" -p 4242:4242 --name "TitleCardMaker" "ghcr.io/titlecardmaker/titlecardmaker:latest"
            ```

        === ":material-microsoft-windows: Windows (Non-Powershell)"

            ```bash
            docker run -itd --net="bridge" -v "C:/Your/Install/Directory/TitleCardMaker/config":"/config/" -e TZ="America/Los_Angeles" -p 4242:4242 --name "TitleCardMaker" "ghcr.io/titlecardmaker/titlecardmaker:latest"
            ```

        ??? tip "User ID, Group ID, and UMASK"

            If you want to set the user and group which TCM is running under,
            then you may define the `PUID`, `PGID`, and `UMASK` environment
            variables as needed.

    4. Verify your volumes are mapped correctly by looking for a `db.sqlite`
    file inside the `config` directory. If you do not see one, then correct the
    volumes specified in Step 5 (double check your quotes are in the correct
    position).

=== ":material-language-python: Non-Docker"

    <a id="non-docker-install"></a>

    ### Downloading Python

    === ":material-linux: Linux"

        Depending on your Linux distro, Python may already be installed. If not,
        most likely you are able to install Python on your own.

    === ":material-apple: MacOS"

        Install a current Python 3 release from
        [python.org](https://www.python.org/downloads/) or via Homebrew
        (`brew install python`). The system Python that ships with macOS is not
        recommended for running TitleCardMaker.

    === ":material-powershell: Windows (Powershell)"

        Download the latest version of Python from
        [python.org](https://www.python.org/downloads/). Be sure to download
        the "latest version" listed at the top, not necessarily the latest one
        listed in the release table, as that table includes pre-release
        versions.

    === ":material-microsoft-windows: Windows (Non-Powershell)"

        Download the latest version of Python from
        [python.org](https://www.python.org/downloads/). Be sure to download
        the "latest version" listed at the top, not necessarily the latest one
        listed in the release table, as that table includes pre-release
        versions.

    ### Downloading ImageMagick

    === ":material-linux: Linux"

        Depending on your Linux distro, you might be able to use whatever package
        manager comes installed. Some of the common installations are detailed
        [here](https://www.xmodulo.com/install-imagemagick-linux.html). For
        example, the following command works on Debian and Ubuntu:

        ```bash
        sudo apt-get install imagemagick
        ```

        If this is not available, then you must use Docker.

    === ":material-apple: MacOS"

        Follow the ImageMagick installation and setup instructions listed
        [here](https://imagemagick.org/script/download.php).

    === ":material-powershell: Windows (Powershell)"

        Download the Windows Binary Release from the
        [ImageMagick website](https://imagemagick.org/script/download.php#windows).

        During the installation, be sure to check the _Add application directory
        to your system path_ and _Install legacy utilities (e.g. convert)
        boxes_. The other options are optional.

    === ":material-microsoft-windows: Windows (Non-Powershell)"

        Download the Windows Binary Release from the
        [ImageMagick website](https://imagemagick.org/script/download.php#windows).

        During the installation, be sure to check the _Add application directory
        to your system path_ and _Install legacy utilities (e.g. convert)
        boxes_. The other options are optional.

    ### Downloading the Code

    1. Open a terminal[^1] of your choice, and go to your desired install
    location.

        ??? example "Example"

            === ":material-linux: Linux"

                ```bash
                cd "~/Your/Install/Directory/"
                ```

            === ":material-apple: MacOS"

                ```bash
                cd "~/Your/Install/Directory/"
                ```

            === ":material-powershell: Windows (Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\'
                ```

            === ":material-microsoft-windows: Windows (Non-Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\'
                ```

    2. In your install directory from Step 1, clone the repository with the 
    following command - this will create a `TitleCardMaker` subdirectory.

        ```bash
        git clone https://github.com/TitleCardMaker/TitleCardMaker.git
        ```

    ### Running TitleCardMaker

    1. Enter the TCM installation directory that was _just_ created.

        ??? example "Example"

            === ":material-linux: Linux"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker"
                ```

            === ":material-apple: MacOS"

                ```bash
                cd "~/Your/Install/Directory/TitleCardMaker"
                ```

            === ":material-powershell: Windows (Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker'
                ```

            === ":material-microsoft-windows: Windows (Non-Powershell)"

                ```bash
                cd 'C:\Your\Install\Directory\TitleCardMaker'
                ```

    2. Create a subfolder named `config`.

        ```bash
        mkdir config
        ```

    3. Enter the `backend` directory.

        ```bash
        cd backend
        ```

    4. Run the following commands to install the required Python packages and
    launch the TCM interface.

        ```bash
        python -m pip install uv
        ```

        ```bash
        python -m uv run uvicorn server:app --host "0.0.0.0" --port 4242
        ```

    5. You should see an output _like_ this:
    
        ```log
        INFO:     Started server process [17385]
        INFO:     Waiting for application startup.
        INFO:     Application startup complete.
        INFO:     Uvicorn running on http://0.0.0.0:4242 (Press CTRL+C to quit)
        ```

    ??? failure "Interface not accessible?"

        If your log shows

        ```log
        INFO:     Application startup complete.
        ```
        
        And neither the `http://0.0.0.0:4242`, `http://localhost:4242`, or your
        local IP address URL load into the TCM UI, then replace the `0.0.0.0`
        part of the previous command with your _local_ IP address - e.g.
        `192.168.0.10`. If you still have issues, reach out on the Discord.

=== ":simple-unraid: Unraid"

    1. Determine your timezone from the
    [TZ Identifier](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
    column (e.g. `America/Los_Angeles`), and choose a host path for TCM's
    config directory (e.g. `/mnt/user/appdata/titlecardmaker`).

    2. At the bottom of the _Docker_ tab of the Unraid interface, click `Add
    Container`.

    3. Make sure _Advanced View_ is toggled in the top-right corner.

    4. Enter the following information - leaving all other options blank or
    default.

        | Option     | Value                                                                                     |
        | :--------: | :---------------------------------------------------------------------------------------- |
        | Name       | `TitleCardMaker`                                                                          |
        | Repository | `ghcr.io/titlecardmaker/titlecardmaker:latest`                                            |
        | Icon URL   | `https://raw.githubusercontent.com/TitleCardMaker/TitleCardMaker/web-ui/.github/logo.png` |
        | WebUI      | `http://[IP]:[PORT:4242]/`                                                                |

    5. At the bottom of the page, click `Add another Path, Port, Variable, Label
    or Device` and enter each of the following (hitting `Add` after each one):

        | Option         | Value                              |
        | -------------: | :--------------------------------- |
        | Config Type    | `Path`                             |
        | Name           | `Config`                           |
        | Container Path | `/config`                          |
        | Host Path      | _The config directory from Step 2_ |

        | Option         | Value   |
        | -------------: | :------ |
        | Config Type    | `Port`  |
        | Name           | `UI`    |
        | Container Port | `4242`  |
        | Host Port      | `4242`  |

        | Option      | Value                      |
        | ----------: | :------------------------- |
        | Config Type | `Variable`                 |
        | Name        | `Timezone`                 |
        | Key         | `TZ`                       |
        | Value       | _The timezone from Step 2_ |

    6. Hit `Apply`.

!!! success "Success"

    TitleCardMaker is now accessible at `http://localhost:4242/` (or
    `http://0.0.0.0:4242`). It may also be at your LAN IP.

    Next, configure at least one media server Connection (Plex, Jellyfin, or
    Emby) plus TMDb — see [Configuring Connections](./connections/index.md).

## The Tutorial

The following pages of the tutorial walk you through the basics of using
TitleCardMaker — from Connections through creating example Title Cards. The
tutorial uses _Breaking Bad_ as the example Series throughout.

It is designed for __completely new users__ of TCM, but is still helpful for
those migrating from TCM v1.0 (the command line tool). For more detailed
information about specific aspects of TitleCardMaker, look at the
[User Guide](../user_guide/index.md) (after you finish the tutorial!).


[^1]:
    - For Linux, I will assume you know what a Terminal is :wink:
    - For Mac users, this is `Terminal` and can be found via the Spotlight
    - For Windows users, this is `Command Prompt` or `PowerShell`. Both can be
    accessed from the search menu

*[PAT]: Personal Access Token
