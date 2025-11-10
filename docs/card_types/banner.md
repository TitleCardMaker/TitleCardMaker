---
title: Banner Card Type
description: >
    An overview of the built-in Banner card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Banner Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and the design was inspired by graphic designer and TPDb contributor
[Danny Beaton](https://www.dannybeaton.com.au/).

These cards feature a solid-color banner at the bottom of the image, with all
text directly on top of or within the banner. The banner and text can all be
recolored and resized.

<figure markdown="span" style="max-width: 70%">
  ![Example Banner Card](./assets/banner.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Banner Card Elements](./assets/banner/labeled.webp)

## Alternate Coloring

Text which is positioned above the banner will be colored according to the font
color, but text positioned inside the banner itself can be adjusted with the
_Alternate Color_ extra. This defaults to black so that there is sufficient
contrast against the default banner color of white.

This extra will also affect the coloring of the season and episode text.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="34.6"
        data-left-label="goldenrod2"
        data-right-label="black">
        <img src="../assets/banner/alternate_color.webp"/>
        <img src="../assets/banner.webp"/>
    </div>

## Banner Customization

### Color

The color of the banner can be adjusted with the _Banner Color_ extra. By
default, this matches the title text / font color.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="55.4"
        data-left-label="rgba(212, 212, 212, 0.7)"
        data-right-label="white">
        <img src="../assets/banner/banner_color.webp"/>
        <img src="../assets/banner.webp"/>
    </div>

### Height

The height of the banner can be adjusted with the _Banner Height_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="55.4"
        data-left-label="150"
        data-right-label="185">
        <img src="../assets/banner/banner_height.webp"/>
        <img src="../assets/banner.webp"/>
    </div>

### Toggle

The banner can be completely disabled by setting the _Disable Banner_ extra to
`True`.

If disabled, all text will still be positioned as if the banner is present, so
this is _generally_ not advised.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="37"
        data-left-label="True"
        data-right-label="False">
        <img src="../assets/banner/banner_toggle.webp"/>
        <img src="../assets/banner.webp"/>
    </div>

## Episode Text

Unless explicitly stated otherwise, all of the following extras will refer to
both the season _and_ episode text. "Episode text" is used for brevity.

### Color

The color of the season and episode text is controlled with the
[_Alternate Color_](#alternate-coloring) extra.

### Size

The size of the season and episode text can be adjusted with the
_Episode Text Font Size_ extra. Like all font sizes, values greater than
`#!yaml 1.0` will increase the size of the text, and values less than
`#!yaml 1.0` will decrease it.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="12.5"
        data-left-label="1.1"
        data-right-label="1.0">
        <img src="../assets/banner/episode_text_font_size.webp"/>
        <img src="../assets/banner.webp"/>
    </div>

## Horizontal Offset

The distance at which text is offset from the side of the card can be adjusted
with the _Horizontal Offset_ extra. Positive values _increase_ the spacing
between the text and the edge of the image, while negative values _decrease_ it.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="16.75"
        data-left-label="90"
        data-right-label="50">
        <img src="../assets/banner/horizontal_offset.webp"/>
        <img src="../assets/banner.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="48.6"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../assets/banner/mask-raw.webp"/>
        <img src="../assets/banner/mask.webp"/>
    </div>
