---
title: White Border Card Type
description: >
    An overview of the built-in White Border card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# White Border Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and is designed to match TPDb user
[Musikmann2000](https://theposterdb.com/user/Musikmann2000)'s style of posters.
The overall style is also very similiar to the [Standard](./standard.md) type,
but features a white border and a different default font.

<figure markdown="span" style="max-width: 70%">
  ![Example White Border Card](./assets/white_border.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled White Border Card Elements](./assets/white_border-labeled.webp)

## Border Color

The color of the border itself can be recolored with the _Border Color_ extra.
This can be any color, but should not[^1] contain transparency.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="rgb(220,180,98)"
        data-right-label="white">
        <img src="../assets/white_border/border_color.webp"/>
        <img src="../assets/white_border.webp"/>
    </div>

## Episode Text

Unless explicitly stated otherwise, all of the following extras will refer to
both the season _and_ episode text. "Episode text" is used for brevity.

### Coloring

The color of the season and episode text can be adjusted with the _Episode Text
Color_ extra.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="rgb(220,180,98)"
        data-right-label="white">
        <img src="../assets/white_border/episode_text_color.webp"/>
        <img src="../assets/white_border.webp"/>
    </div>

### Size

The size of the season and episode text can be adjusted with the _Episode Text
Font Size_ extra. Like all font sizes, values greater than `#!yaml 1.0` will
increase the size of the text, and values less than `#!yaml 1.0` will decrease
it.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="1.2"
        data-right-label="1.0">
        <img src="../assets/white_border/episode_text_font_size.webp"/>
        <img src="../assets/white_border.webp"/>
    </div>

## Separator Character

If both the season and episode text are displayed on the Card, then a separator
character is added between them. This character can be adjusted with the
_Separator Character_ extra.

The color of this character will be controlled by the [_Episode Text
Color_](#coloring) extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="56"
        data-left-label="//"
        data-right-label="•">
        <img src="../assets/white_border/separator.webp"/>
        <img src="../assets/white_border.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../assets/white_border/mask-raw.webp"/>
        <img src="../assets/white_border/mask.webp"/>
    </div>

[^1]:
    This is because the default white frame static image will still be drawn on
    the image in order to add the edge shadow effect, and any transparency will
    just reveal the image.
