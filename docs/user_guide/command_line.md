---
title: Command Line Image Creation
description: >
    Create Title Cards and posters from the command line for testing,
    debugging, and one-off image generation.
---

# Command Line Image Creation

TitleCardMaker can create **Title Cards** and **posters** outside the Web UI.
Each built-in card type and poster type exposes its own small command-line
interface (CLI). This is useful when you want to:

- Prototype a look before saving settings in the UI
- Debug ImageMagick commands for a specific card or poster
- Generate a single image without adding the Series to TCM

This guide explains the shared CLI behavior. It does **not** list every option
for every card type — instead, it shows how to run commands and discover the
parameters for the type you are working with.

!!! note "Not the same as TCM v1"

    TitleCardMaker v1 was a standalone command-line application. The v2 Web UI
    is the primary interface. These CLIs only create individual images; they do
    not sync libraries, manage Series, or replace the Web UI.

## Prerequisites

Run commands from the **`backend`** directory of your TitleCardMaker
installation, using the same Python environment as the main application.

=== ":material-language-python: Non-Docker"

    If you followed the [local installation guide](../getting_started/index.md#non-docker-install),
    run commands with `uv` from the `backend` directory:

    ```bash
    cd backend
    uv run python -m app.cards.types.Standard --help
    ```

=== ":material-docker: Docker"

    Exec into your running container and use the application Python from the
    install path (commonly `/app`):

    ```bash
    docker exec -it titlecardmaker bash
    cd /app/backend
    python -m app.cards.types.Standard --help
    ```

ImageMagick must be available the same way it is for normal TitleCardMaker
operation. If the Web UI can create cards, the CLI should work as well.

Optional: place a `.env` file in the application root if you rely on custom
ImageMagick or container settings — the CLI loads the same
[environment variables](./environment_variables.md) as the Web UI.

## How the CLI is organized

Every card and poster module registers a command group. When you run the module
directly, you choose a **subcommand**:

| Image type | Subcommand | Example module |
| :--------- | :--------- | :------------- |
| Title Card | `card`     | `app.cards.types.Standard` |
| Poster     | `create`   | `app.magick.posters.genre` |

The general pattern is:

```bash
python -m <module> <subcommand> [arguments...]
```

## Passing arguments

Arguments are passed as **`--flag value`** pairs. Flag names use hyphens on the
command line; they are converted to Python keyword names automatically
(`--source-file` → `source_file`).

```bash
python -m app.cards.types.Standard card \
    --source-file ./source.jpg \
    --card-file ./output.webp \
    --title-text "The One Where It Works" \
    --season-text "SEASON 1" \
    --episode-text "EPISODE 1"
```

### Boolean flags

Boolean options can be passed with an explicit value **or** as a standalone flag
(treated as `true`):

```bash
--blur true
--blur          # same as --blur true
--borderless    # same as --borderless true
```

### Quoting values

Quote values that contain spaces or special characters:

```bash
--title-text "Better Call Saul"
--genre "Science Fiction"
```

### Validation errors

Arguments are validated with the same Pydantic models used internally. If a
required field is missing or a value is invalid, the command exits with a
**ValidationError** that names the problem field. Fix the argument and re-run.

## Discovering available parameters

You do not need to memorize options for each card type. Use these tools:

### 1. The `params` subcommand

Every card and poster module provides a `params` command that lists accepted
arguments, whether each is required, its type, and default values:

```bash
python -m app.cards.types.Standard params
python -m app.magick.posters.movie params
```

For machine-readable output (JSON Schema), add `--json`:

```bash
python -m app.cards.types.Logo params --json
```

### 2. `--help` on each subcommand

```bash
python -m app.cards.types.Standard --help
python -m app.cards.types.Standard card --help
python -m app.magick.posters.season create --help
```

### 3. Card type documentation

Built-in card types are documented under [Card Types](../../card_types/index.md).
Those pages describe what each option **does** visually (colors, layout, extras).
Cross-reference option names with the `params` output — UI labels often map to
snake_case CLI flags (for example, _Font Color_ → `--font-color`).

## Title Cards

### Choosing a module

Each built-in card type lives in `backend/app/cards/types/` as a Python file.
The module path matches the filename:

| Card type (examples) | CLI module |
| :------------------- | :--------- |
| Standard             | `app.cards.types.Standard` |
| Logo                 | `app.cards.types.Logo` |
| Anime                | `app.cards.types.Anime` |
| Poster               | `app.cards.types.Poster` |

See the full list in the [Card Types](../../card_types/index.md) section of the
docs. Local card types placed in your `config/card_types/` directory can also
expose a CLI if they call `add_cli()` — see
[Local Card Types](../../card_types/local.md).

### Creating a card

```bash
python -m app.cards.types.Standard card \
    --source-file ./source.jpg \
    --card-file ./card.webp \
    --title-text "Full Measure" \
    --season-text "SEASON 5" \
    --episode-text "EPISODE 9"
```

Most card types require at minimum:

- `--source-file` — background or Source Image
- `--card-file` — output path
- Text fields required by that card type (commonly `--title-text`,
  `--season-text`, and `--episode-text`)

Run `params` on the specific module to see the full list for that card.

### ImageMagick command history

After a successful run, the CLI prints the ImageMagick commands that were
executed. Use this output to debug rendering issues or reproduce a result
manually.

## Posters

Poster CLIs create **genre**, **movie**, and **season** poster images used by
TitleCardMaker's poster tooling. Each poster type is its own module:

| Poster type | CLI module |
| :---------- | :--------- |
| Genre       | `app.magick.posters.genre` |
| Movie       | `app.magick.posters.movie` |
| Season      | `app.magick.posters.season` |

### Creating a poster

All poster modules use the **`create`** subcommand:

=== "Genre"

    ```bash
    python -m app.magick.posters.genre create \
        --source ./background.jpg \
        --genre "Action" \
        --output ./genre.jpg
    ```

=== "Movie"

    ```bash
    python -m app.magick.posters.movie create \
        --source ./background.jpg \
        --title "THE FILM" \
        --subtitle "A SUBTITLE" \
        --output ./movie.jpg
    ```

=== "Season"

    ```bash
    python -m app.magick.posters.season create \
        --source ./background.jpg \
        --season-text "SEASON 2" \
        --destination ./season.jpg \
        --logo ./logo.png
    ```

Run `params` on the relevant module for optional fields such as `--borderless`,
`--omit-gradient`, font sizing, and logo placement.

!!! tip "Season poster output path"

    Season posters write to `--destination`, while genre and movie posters use
    `--output`. The `params` command for each module shows the exact field names.

## Quick reference

```bash
# List subcommands
python -m app.cards.types.Standard --help

# List parameters for a card type
python -m app.cards.types.Standard params

# Create a card
python -m app.cards.types.Standard card --source-file ... --card-file ...

# List parameters for a poster type
python -m app.magick.posters.genre params

# Create a poster
python -m app.magick.posters.genre create --source ... --genre ... --output ...
```

## Troubleshooting

**`No such option: --some-flag`**

Make sure the flag belongs to the `card` or `create` subcommand, not the top-level
group. The flag list comes from `params`, not from `card --help` (creation flags
are passed through as extra arguments).

**Source file does not exist**

`--source-file` / `--source` paths are validated before rendering. Use an
absolute or correct relative path from your current working directory.

**ImageMagick errors after validation passes**

The CLI reached ImageMagick but a reference asset or font may be missing, or
ImageMagick may not be configured the same as in Docker. Compare the printed
command history with a working Web UI render and check
[Environment Variables](./environment_variables.md) for ImageMagick settings.

**Module not found**

Run from the `backend` directory and use the `-m` module form shown above. The
module path is not the same as the Web UI URL or card identifier string.
