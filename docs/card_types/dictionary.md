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

## Background Color

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
        data-starting-point="42.9"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../assets/dictionary/mask-raw.webp"/>
        <img src="../assets/dictionary/mask.webp"/>
    </div>
