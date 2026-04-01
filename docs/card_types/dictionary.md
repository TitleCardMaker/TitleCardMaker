---
title: Dictionary Card Type
description: >
    An overview of the built-in Dictionary card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Dictionary Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and was inspired by the text annotations in
[this video](https://www.youtube.com/watch?v=gcS1HIci4hQ) by _Any Austin_.

Cards of this design are intended to resemble a dictionary definition - and so
most extras resolve around manipulating the "word" (series name), "label"
(title), and "definition" (Episode description).

<figure markdown="span" style="max-width: 70%">
  ![Example Dictionary Card](./assets/dictionary.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Dictionary Card Elements](./assets/dictionary/labeled.webp)

## Background

The background element is the rectangle which is positioned behind the text
elements.

### Background Color

The color of the background box can be adjusted with the _Background Color_
extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="rgba(212,212,212,0.3)"
        data-right-label="rgba(12,12,12,0.8)">
        <img src="../assets/dictionary/background_color.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

### Rounding Radius

The roundness of the background rectangle can be adjusted with the _Background
Rounding Radius_ extra. The higher the radius/value, the more round the edges. A
value of 0 will result in square corners.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="0"
        data-right-label="35">
        <img src="../assets/dictionary/background_rounding_radius.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

## Definition Text

### Color

The color of the defintion text can be adjusted with the _Definition Color_
extra. If unspecified, this defaults to matching the color of the title text.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="skyblue"
        data-right-label="white">
        <img src="../assets/dictionary/definition_color.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

### Italicize Toggle

The definition text is italicized by default. This can be turned off by setting
_Italicize Definition Toggle_ to `False`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="18.3"
        data-left-label="False"
        data-right-label="True">
        <img src="../assets/dictionary/italicize_definition_text.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

### Line Limits

The definition text will be dynamically split into multiple lines in order to
fit the width of the rectangle. The maximum number of lines of displayed text
can be adjusted with the _Definition Line Limit_ extra.

If the number of lines is longer than this limit then the definition text will
be truncated and `[...]` will be added to the end.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="23.27"
        data-left-label="2"
        data-right-label="4">
        <img src="../assets/dictionary/definition_line_limit.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

### Quotes

By default, quotes are added around the definition text. This can be disabled by
setting the _Quote Definition Toggle_ extra to `False`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="False"
        data-right-label="True">
        <img src="../assets/dictionary/quote_toggle.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

### Size

The size of the definition text can be adjusted with the _Definition Font Size_
extra. Like all font sizes, values greater than `#!yaml 1.0` will increase the
size of the text, and values less than `#!yaml 1.0` will decrease it.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="0.8"
        data-right-label="1.0">
        <img src="../assets/dictionary/definition_size.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

### Text

The text itself can be adjusted with the _Defintion Text_ extra.

!!! tip "Automatically Pull Episode Descriptions"

    If left as the default (or any [Format String](../user_guide/variables.md)
    which includes the variable `{episode_description}`, e.g.
    `{episode_description.lower()}`), then TCM will automatically search
    [TMDb](../user_guide/connections.md#themoviedatabase) for an Episode
    description/overview.

    This can be disabled by either setting this Extra to the text you wish to
    display _or_ disabling the text altogether by specifying `""`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="example text"
        data-right-label="{episode_description}">
        <img src="../assets/dictionary/definition_text.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

### Language

The language of the text pulled from TMDb can be adjusted with the _Definition
Text Language_ extra. This __does not__ perform any actual translation, and only
adjusts which text is pulled from TMDb __if available__. If the indicated
language is not available, then English will be used instead.

This can be the English language name - i.e. `Chinese`, `Danish`, etc. - or the
international language code - i.e. `fr-FR`, `ko-KR`, etc. If you type an
unsupported language, take a look at the [logs](../user_guide/logs.md), as TCM
will log the names of the languages which are supported for the Episode.

!!! warning "Non-English Character Support"

    Because the font used for the definition text is a roman character based
    Font, there is no guarantee that languages with non-roman character sets
    (like Chinese, Arabic, etc.) will work.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="French"
        data-right-label="English">
        <img src="../assets/dictionary/definition_text_language.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

## Position

The overall position of the background and all text elements can be adjusted
with the _Position_ extra. This needs to be formatted like `+x+y`, where the `x`
and `y` values are how far from the bottom left corner of the image. Technically
you can specify negative x or y values (i.e. `-100-100`), but this will
partially obscure the content.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="+100+600"
        data-right-label="+100+100">
        <img src="../assets/dictionary/position.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

## Separator Character

The separator character is used to join the title and season/episode text. This
can be adjusted with the _Separator Character_ extra. To remove this character
completely, specify `""`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label=" -"
        data-right-label=",">
        <img src="../assets/dictionary/separator.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

## Word Text

??? tip "Completely Remove Word Text"

    The word text can be completely removed by setting the text to `{BLANK}`.
    See the [User Guide](../user_guide/variables.md) for more details.

### Color

The color of the word text can be adjusted with the _Word Text Color_ extra. If
unspecified, this color defaults to matching the color of the title text.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="skyblue"
        data-right-label="white">
        <img src="../assets/dictionary/word_color.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

### Shadow

#### Color

The color of the word text's drop shadow can be changed with the _Shadow Color_
extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="crimson"
        data-right-label="black">
        <img src="../assets/dictionary/shadow_color.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

#### Definition

The "definition" of the word text's drop shadow can be changed with the _Shadow
Definition_ extra. This is an ImageMagick [Shadow
Definition](https://imagemagick.org/script/command-line-options.php#shadow). See
the tip tooltip for more information. The default shadow is `95x2+7+7`.

??? tip "Shadow Customization"

    ImageMagick defines shows in the format of:

    ```
    {opacity}x{sigma}{+ or -}{x}{+ or -}{y}
    ```

    For example, `95x2+7+7`, `50x5+0+0`, and `80x4+0-10` are all valid shadow
    definitions.

    This can be interpreted like so (using the default shadow, for example):
    the shadow has 95% opacity, has a sigma/blurriness value of 2, and is
    positioned 7 pixels below, and 7 pixels to the right of the base text.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="27.07"
        data-left-label="80x8+0+12"
        data-right-label="95x2+7+7">
        <img src="../assets/dictionary/shadow_definition.webp"/>
        <img src="../assets/dictionary/shadow_color.webp"/>
    </div>

### Size

The size of the definition text can be adjusted with the _Word Text Font Size_
extra. Like all font sizes, values greater than `#!yaml 1.0` will increase the
size of the text, and values less than `#!yaml 1.0` will decrease it.

Be aware that decreasing the size of the word text may result in truncating more
of the definition text.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="32.1"
        data-left-label="0.6"
        data-right-label="1.0">
        <img src="../assets/dictionary/word_size.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

### Text

The text used in the "word" position itself can be adjusted with the _Word Text_
extra. This field supports [Format Strings](../user_guide/variables.md), and the
default value (`{series_name.lower()}`) will add the series name in lowercase
text.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="20"
        data-left-label="{series_name}"
        data-right-label="{series_name.lower()}">
        <img src="../assets/dictionary/word_text.webp"/>
        <img src="../assets/dictionary.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="26.2"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../assets/dictionary/mask-raw.webp"/>
        <img src="../assets/dictionary/mask.webp"/>
    </div>
