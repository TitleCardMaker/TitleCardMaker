---
title: Banner Card Type
description: >
    An overview of the built-in Banner card type.
---

# Banner Card Type

??? warning "Under Construction"

    This documentation is actively being developed.

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and the design was inspired by graphic designer and TPDb contributor
[Danny Beaton](www.DannyBeaton.com.au).

These cards feature a solid-color banner at the bottom of the image, with all
text directly on top of or within the banner. The banner and text can all be
recolored and resized.

<figure markdown="span" style="max-width: 70%">
  ![Example Banner Card](./assets/banner.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Banner Card Elements](./assets/banner-labeled.webp)

## Alternate Coloring

Text which is positioned above the banner will be colored according to the font
color, but text positioned inside the banner itself can be adjusted with the
_Alternate Color_ extra. This defaults to black so that there is sufficient
contrast against the default banner color of white.

This extra will also affect the coloring of the season and episode text.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="83"
        data-left-label="Mask Image" data-right-label="Resulting Title Card">
        <img src="../assets/notification-mask-raw.webp"/>
        <img src="../assets/notification-mask.webp"/>
    </div>

## Banner Customization

### Color

The color of the banner can be adjusted with the _Banner Color_ extra. By
default, this matches the title text / font color.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="83"
        data-left-label="Mask Image" data-right-label="Resulting Title Card">
        <img src="../assets/notification-mask-raw.webp"/>
        <img src="../assets/notification-mask.webp"/>
    </div>

### Height

The height of the banner can be adjusted with the _Banner Height_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="83"
        data-left-label="Mask Image" data-right-label="Resulting Title Card">
        <img src="../assets/notification-mask-raw.webp"/>
        <img src="../assets/notification-mask.webp"/>
    </div>

### Toggle

The banner can be completely disabled by setting the _Disable Banner_ extra to
`True`.

If disabled, all text will still be positioned as if the banner is present, so
this is _generally_ not advised.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="83"
        data-left-label="Mask Image" data-right-label="Resulting Title Card">
        <img src="../assets/notification-mask-raw.webp"/>
        <img src="../assets/notification-mask.webp"/>
    </div>

## Episode Text

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
        data-starting-point="83"
        data-left-label="Mask Image" data-right-label="Resulting Title Card">
        <img src="../assets/notification-mask-raw.webp"/>
        <img src="../assets/notification-mask.webp"/>
    </div>

## Horizontal Offset

The distance at which text is offset from the side of the card can be adjusted
with the _Horizontal Offset_ extra. Positive values _increase_ the spacing
between the text and the edge of the image, while negative values _decrease_ it.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="83"
        data-left-label="Mask Image" data-right-label="Resulting Title Card">
        <img src="../assets/notification-mask-raw.webp"/>
        <img src="../assets/notification-mask.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="83"
        data-left-label="Mask Image" data-right-label="Resulting Title Card">
        <img src="../assets/notification-mask-raw.webp"/>
        <img src="../assets/notification-mask.webp"/>
    </div>
