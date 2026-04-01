---
title: Custom Variables
description: >
    Using internal Title Card variables in TitleCardMaker.
---

# Custom Variables

Throughout TCM, all Card variables, inputs, and extras may take advantage of any
of the internally defined variables can be used, allowing for more fine-tuned
customization. Accessing these variables is done by specifying the variable name
in curly brackets (`{}`), such as `{episode_number}`.

This page documents all the available variables.

## Variable Reference

For reference, each variable example is shown for the same
[Episode](https://www.imdb.com/title/tt1232253/) of Breaking Bad with some
hypothetical TCM customizations.

=== ":material-information-outline: Inherent Metadata"

    | Variable Name             | Description             | Example                |
    | ------------------------- | ----------------------- | ---------------------- |
    | `series_name`             | Name of the Series      | `Breaking Bad`         |
    | `series_full_name`        | Full name of the Series | `Breaking Bad (2008)`  |
    | `year`                    | Series Release year     | `2008`                 |
    | `season_number`           | Season number           | `2`                    |
    | `episode_number`          | Episode number          | `6`                    |
    | `absolute_number`         | Absolute episode number | `13`                   |
    | `absolute_episode_number` | Absolute number (if available), otherwise the episode number | `13` |
    | `number_of_seasons`       | Number of seasons in the Series | `5`        |
    | `airdate`                 | Episode airdate[^3]     | `2009-04-12`           |
    | `watched`                 | Whether the Episode is watched or not | `true`   |

=== ":material-format-title: Text Variables"

    | Variable Name       | Description                          | Example     |
    | ------------------- | ------------------------------------ | ----------- |
    | `title`             | Original title of the Episode        | `Peekaboo`  |
    | `title_text`        | Formatted title text of the Card[^1] | `PEEKABOO`  |
    | `hide_season_text`  | Whether to hide season text          | `False`     |
    | `hide_episode_text` | Whether to hide episode text         | `False`     |
    | `season_text`       | The season text of the Card          | `Season 2`  |
    | `episode_text`      | The episode text of the Card         | `Episode 6` |

=== ":material-alert-outline: Cardinal and Ordinal Numbers"

    !!! warning "Deprecated Variables"

        Previously, cardinal and ordinal spelling of numbers (e.g. `Two`,
        `Second`) were available as direct variables (`season_number_cardinal`).
        These are now accessed by the `to_cardinal()` and `to_ordinal()`
        functions. See [here](#function-reference).

=== ":material-calculator-variant: Calculated Metadata"

    | Variable Name          | Description                                   | Example |
    | ---------------------- | --------------------------------------------- | ------- |
    | `season_episode_count` | Number of Episodes in the season              | `13`    |
    | `season_episode_max`   | Maximum episode number in the season          | `13`    |
    | `season_absolute_max`  | Maximum absolute episode number in the season | `20`    |
    | `series_episode_count` | Total number of Episodes in the Series        | `62`    |
    | `series_episode_max`   | Maximum episode number in the Series          | `16`    |
    | `series_absolute_max`  | Maximum absolute episode number in the Series | `62`    |

    !!! question "How do these differ?"

        At first glance, the maximum and count variables (like
        `season_episode_count` and `season_episode_max`) might appear the same
        (and in most cases they are), but for Series where Episodes are missing
        these two would differ.

        For example, if I had Episodes 3-10 of Breaking Bad in TCM,
        `season_episode_count` would be `8`, while `season_episode_max` would be
        10.

        The same logic is true for their absolute-number equivalents.

=== ":material-format-font-size-increase: Fonts"

    | Variable Name            | Description                | Example  |
    | ------------------------ | -------------------------- | -------- |
    | `font_color`             | Font color                 | `yellow` |
    | `font_file`              | File path to the font file | `/config/assets/fonts/0/Breaking Bad.ttf`   |
    | `font_size`              | Font size                  | `1.2`    |
    | `font_kerning`           | Font kerning               | `2.3`    |
    | `font_stroke_width`      | Font stroke width          | `1.0`    |
    | `font_interline_spacing` | Font interline spacing     | `0`      |
    | `font_interword_spacing` | Font interword spacing     | `20`     |
    | `font_vertical_shift`    | Font vertical shift        | `20`     |

=== ":material-folder-open: Files"

    For more information on the logo color attributes, see `get_image_color`
    under [Function Reference](#function-reference) > Date & Color for details.

    | Variable Name         | Description                           | Example |
    | --------------------- | ------------------------------------- | --------|
    | `source_file`         | Path to the Source Image              | `/config/source/Breaking Bad (2008)/s2e6.jpg` |
    | `card_file`           | Path to the Title Card                | `/config/cards/Breaking Bad (2008)/Season 2/Breaking Bad (2008) - S02E06.jpg` |
    | `source_directory`    | Path to the Series' source directory  | `/config/source/Breaking Bad (2008)/` |
    | `backdrop_file`       | Path to the backdrop file[^5]         | `/config/source/Breaking Bad (2008)/backdrop.jpg` |
    | `logo_file`           | Path to the logo file[^5]             | `/config/source/Breaking Bad (2008)/logo.png` |
    | `poster_file`         | Path to the poster file               | `/config/source/Breaking Bad (2008)/poster.jpg` |
    | `logo_color`          | Primary color of the logo             | `green` |
    | `logo_color_no_white` | Primary (non-white) color of the logo | `green` |

=== ":material-database-outline: Database IDs"

    | Variable Name        | Description               | Example             |
    | -------------------- |-------------------------- | ------------------- |
    | `series_emby_id`     | Emby ID of the Series     | `0:TV Shows:abcdef` |
    | `series_imdb_id`     | IMDb ID of the Series     | `tt0903747`         |
    | `series_jellyfin_id` | Jellyfin ID of the Series | `1:TV:def0123`      |
    | `series_sonarr_id`   | Sonarr ID of the Series   | `3:25`              |
    | `series_tmdb_id`     | TMDb ID of the Series     | `1396`              |
    | `series_tvdb_id`     | TVDb ID of the Series     | `81189`             |
    | `series_tvrage_id`   | TV Rage ID of the Series  | `18164`             |
    | `episode_emby_id`    | Emby ID of the Episode    | `0:TV Shows:993981` |
    | `episode_imdb_id`    | IMDb ID of the Episode    | `tt1232253`         |
    | `episode_jellyfin_id`| Emby ID of the Episode    | `1:TV:9d9da`        |
    | `episode_tmdb_id`    | TMDb ID of the Episode    | `62097`             |
    | `episode_tvdb_id`    | TVDb ID of the Episode    | `438917`            |
    | `episode_tvrage_id`  | TV Rage ID of the Episode | `710919`            |

    !!! note "Emby, Jellyfin, and Sonarr IDs"

        The IDs of Emby, Jellyfin, and Sonarr are all unique to your server(s)
        and libraries.

=== ":material-code-braces: Internal Data"

    | Variable Name | Description                            | Example     |
    | ------------- | -------------------------------------- | ----------- |
    | `extras`      | Any assigned extras                    | _See below_ |
    | `NEWLINE`     | A character to move text to a new line | `\n`        |
    | `BACKSLASH`   | The ++backslash++ character            | `\`         |
    | `BLANK`       | Blank text[^6]                         |             |

    Any assigned extras are added as their variable name. For example, if I
    specify the "Episode Text Color" extra for the Series, then the variable
    `episode_text_color` would provided. This can be used to add arbitrary extra
    data to a Card.

## Function Reference

In addition to defining many variables which can be used, TCM also implements
many functions which allow for more customization. Examples below use the same
[Breaking Bad episode](https://www.imdb.com/title/tt1232253/) as the variable
reference: Season 2, Episode 6, airdate `2009-04-12`, title "Peekaboo".

For more details on the available functions, see the following sections of 

=== ":material-format-letter-case: Text Capitalization"

    === "`titlecase`"

        Converts the given text to title case (capitalize the principal words).
        Useful for capitalizing cardinal or ordinal words, or episode titles.

        | Example Format string                     | Output             |
        | ----------------------------------------- | ------------------ |
        | `{titlecase(to_cardinal(season_number))}` | `Two`              |
        | `{titlecase(to_ordinal(episode_number))}` | `Sixth`            |
        | `{titlecase(title)}`                      | `Peekaboo`         |
        | `{titlecase("the great escape")}`         | `The Great Escape` |

    === "`to_lowercase`"

        Converts the given text to lowercase.

        | Example Format string         | Output         |
        | ----------------------------- | -------------- |
        | `{to_lowercase(title)}`       | `peekaboo`     |
        | `{to_lowercase(series_name)}` | `breaking bad` |
        | `{to_lowercase("UPPERCASE")}` | `uppercase`    |

    === "`to_uppercase`"

        Converts the given text to uppercase.

        | Example Format string                         | Output         |
        | --------------------------------------------- | -------------- |
        | `{to_uppercase(title)}`                       | `PEEKABOO`     |
        | `{to_uppercase(series_name)}`                 | `BREAKING BAD` |
        | `{to_uppercase(to_cardinal(episode_number))}` | `SIX`          |

=== ":material-numeric: Number wording"

    === "`to_cardinal`"

        Converts the given number to its cardinal spelling (one, two, three,
        ...)[^2].

        | Example Format string                 | Output         |
        | ------------------------------------- | -------------- |
        | `{to_cardinal(episode_number)}`       | `six`          |
        | `{to_cardinal(season_number)}`        | `two`          |
        | `{to_cardinal(episode_number, 'fr')}` | `six` (French) |
        | `{to_cardinal(13, 'es')}`             | `trece`        |

    === "`to_ordinal`"

        Converts the given number to its ordinal spelling (first, second, third,
        ...)[^2].

        | Format string                        | Output       |
        | ------------------------------------ | ------------ |
        | `{to_ordinal(episode_number)}`       | `sixth`      |
        | `{to_ordinal(season_number)}`        | `second`     |
        | `{to_ordinal(episode_number, 'es')}` | `sexto`      |
        | `{to_ordinal(absolute_number)}`      | `thirteenth` |

    === "`to_short_ordinal`"

        Converts the given number to a shorthand ordinal (1st, 2nd, 3rd,
        ...)[^2].

        | Format string                             | Output |
        | ----------------------------------------- | ------ |
        | `{to_short_ordinal(season_number)}`       | `2nd`  |
        | `{to_short_ordinal(episode_number)}`      | `6th`  |
        | `{to_short_ordinal(season_number, 'ja')}` | `2番目` |
        | `{to_short_ordinal(13)}`                  | `13th` |

    === "`to_roman_numeral`"

        Converts the given number to a Roman numeral (I, II, III, ...). Only
        supports numbers from 1 to 3999[^4].

        | Format string                        | Output   |
        | ------------------------------------ | -------- |
        | `{to_roman_numeral(episode_number)}` | `VI`     |
        | `{to_roman_numeral(season_number)}`  | `II`     |
        | `{to_roman_numeral(13)}`             | `XIII`   |
        | `{to_roman_numeral(2024)}`           | `MMXXIV` |

    ??? note "Supported Language Codes"

        | Code    | Language             |
        | ------- | -------------------- |
        | `am`    | Amharic              |
        | `ar`    | Arabic               |
        | `cz`    | Czech                |
        | `da`    | Danish               |
        | `de`    | German               |
        | `en`    | English (the default)|
        | `eo`    | Esperanto            |
        | `es`    | Spanish              |
        | `fa`    | Farsi                |
        | `fi`    | Finnish              |
        | `fr`    | French               |
        | `fr_BE` | French (Belgium)     |
        | `fr_CH` | French (Switzerland) |
        | `he`    | Hebrew               |
        | `hu`    | Hungarian            |
        | `id`    | Indonesian           |
        | `it`    | Italian              |
        | `ja`    | Japanese             |
        | `kn`    | Kannada              |
        | `ko`    | Korean               |
        | `kz`    | Kazakh               |
        | `lt`    | Lithuanian           |
        | `lv`    | Latvian              |
        | `nl`    | Dutch                |
        | `no`    | Norwegian            |
        | `pl`    | Polish               |
        | `pt`    | Portuguese           |
        | `pt_BR` | Portuguese (Brazil)  |
        | `ro`    | Romanian             |
        | `ru`    | Russian              |
        | `sl`    | Slovenian            |
        | `sr`    | Serbian              |
        | `sv`    | Swedish              |
        | `te`    | Telugu               |
        | `tg`    | Tajik                |
        | `th`    | Thai                 |
        | `tr`    | Turkish              |
        | `uk`    | Ukrainian            |
        | `vi`    | Vietnamese           |

    !!! tip "Cardinal vs. Ordinal Mnemonic"

        An easy way to remember whether you want the cardinal or ordinal text is
        that ++c++ardinal starts with a ++c++ like ++c++ount - so one, two, three,
        etc.; while ++o++ordinal starts with ++o++ like ++o++rder - so first,
        second, third, etc.

=== ":material-calendar-clock: Date & color"

    === "`format_date`"

        Formats the given date using a [strftime](https://strftime.org/)-style
        format string[^3]. Optional `timezone` can be `'local'` or a timezone
        name (e.g. `'America/New_York'`).

        | Format string                              | Output           |
        | ------------------------------------------ | ---------------- |
        | `{format_date(airdate, '%B %d, %Y')}`      | `April 12, 2009` |
        | `{format_date(airdate, 'Week %-U of 52')}` | `Week 15 of 52`  |
        | `{format_date(airdate, '%Y-%m-%d')}`       | `2009-04-12`     |
        | `{format_date(airdate, '%A')}`             | `Sunday`         |

    === "`get_image_color`"

        TCM can parse images for primary colors and use those in place of
        variables— similar to the in-UI **Analyze Palette** button. This
        function returns a color from any given image (e.g. logo or poster). See
        below for full details and arguments.

        !!! example "Examples"

            === "Simple Example"

                The following usage will get the single most prominent color of
                the logo and fallback to `red` if one is not available.

                ```python
                get_image_color(logo_file, fallback="red")
                ```

            === "Secondary Color"

                The following usage will get the second most common color of the
                logo. This is useful if you want to automatically utilize an
                accent color.

                ```python
                get_image_color(logo_file, fallback="blue", index=1)
                ```

            === "Ignore White Colors"

                The following usage will get the primary color of the poster,
                ignoring predominately white images.

                ```python
                get_image_color(poster_file, fallback="white", white_threshold=210)
                ```

        The complete function signature is: 

        ```python
        get_image_color(
            image: Path,
            /,
            fallback: str,
            index: int = 0,
            *,
            colors: int = 8,
            alpha_threshold: int = 70,
            black_threshold: int = 40,
            white_threshold: int = 256,
        )
        ```

        If the above text does not make sense to you, see the provided examples
        for detail; or use the simplified `{logo_color}` or
        `{logo_color_no_white}` variables to avoid the function call altogether.

        **Arguments**

        `image`
        :   The file to analyze. See the **Files** tab in the
            [Variable Reference](#variable-reference) above for options;
            generally use `logo_file` to match the logo color.

        `fallback`
        :   The fallback color if analysis yields no meaningful results (e.g.
            file missing or no color at the given `index`).

        `index`
        :   Which color to return, zero-indexed. `0` = first (most primary)
            color, `1` = second, etc. Default: `0`.

        `colors`
        :   Number of colors to group the image into. Higher = finer gradations
            (more pixel-accurate but possibly similar shades); lower = similar
            colors bucketed together. Default: `8`.

        `alpha_threshold`
        :   Transparency threshold; pixels _more_ transparent than this are
            ignored (e.g. `75` ignores pixels &gt;25% transparent). Range:
            `0`–`100`. Default: `70`.

        `black_threshold`
        :   RGB threshold below which a color is treated as black and ignored
            (e.g. `40` ignores `rgb(30,30,30)`). Range: `0`–`255`. Default:
            `40`.

        `white_threshold`
        :   RGB threshold above which a color is treated as white and ignored
            (e.g. `210` ignores `rgb(220,220,220)`). Range: `0`–`255`.
            Default: `256` (no white filtering).

### Built-in Functions

!!! info "Python built-ins"

    Beyond the TCM-defined functions above, you can use methods of built-in
    Python types (strings, lists, datetime, etc.). See
    [the Python docs](https://docs.python.org/3/library/stdtypes.html) for a
    complete reference, or ask on [the Discord](https://discord.gg/bJ3bHtw8wH).

[^1]: This is _after_ any Font replacements, font case functions, and line
splitting.

[^2]: The second argument to the function is the _language code_. Not all
languages support cardinal and ordinal numbering. These will raise an error
during Card creation.

[^3]: To write the airdate in any format _other_ than the default, the
`format_date` function must be used. A reference of all date variables is
available [here](https://strftime.org/).

[^4]: Roman numerals are not defined for values greater than `3999` (blame the
Romans). These will raise an error during Card creation.

[^5]: If per-season assets are [enabled](...) for the Series __and__ exist,
these will be used. Otherwise these are the Series-wide assets.

[^6]: This is generally used if you want to _not_ display any text in a
particular field. This can also be done by specifying `{""}`.
