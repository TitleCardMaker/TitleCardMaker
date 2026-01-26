---
title: Inset Card Type
description: >
    An overview of the built-in Inset card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Inset Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist).

This card type shows the season and episode text **inset into** the title text:
the index text appears to "cut out" of the title, with a window of the source
image (styled to match the card) visible behind it. The title sits at the
bottom with a drop shadow, and supports custom fonts and custom season titles.

<figure markdown="span" style="max-width: 70%">
  ![Example Inset Card](./assets/inset.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Inset Card Elements](./assets/inset/labeled.webp)

## Episode Text

Unless _explicitly_ stated otherwise, "episode text" here refers to both the
season and episode text (the inset index).

This card will position the episode text in the middle of the title text. If
there are multiple lines of title text, it will be positioned in the middle of
the bottom line.

### Color

The color of the inset index text can be adjusted with the _Episode Text Color_
extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="gold"
        data-right-label="crimson">
        <img src="../assets/inset/episode_text_color.webp"/>
        <img src="../assets/inset.webp"/>
    </div>

### Font Size

The size of the inset text can be adjusted with the _Episode Text Font Size_
extra. Values greater than `#!yaml 1.0` increase the size; values less than
`#!yaml 1.0` decrease it.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="41.85"
        data-left-label="1.2"
        data-right-label="1.0">
        <img src="../assets/inset/episode_text_font_size.webp"/>
        <img src="../assets/inset.webp"/>
    </div>

## Separator Character

When both season and episode text are shown, a separator is placed between them.
The _Separator Character_ extra controls this character. The default is a dash.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="//"
        data-right-label="-">
        <img src="../assets/inset/separator.webp"/>
        <img src="../assets/inset.webp"/>
    </div>

## Inset Text Transparency

The _Inset Text Transparency_ extra controls how opaque the "cut-out" background
is—i.e. the patch of source image visible behind the index text. A value of
`#!yaml 1.0` (default) is fully opaque; `#!yaml 0.0` is fully transparent.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="51.95"
        data-left-label="0.5"
        data-right-label="1.0">
        <img src="../assets/inset/transparency.webp"/>
        <img src="../assets/inset.webp"/>
    </div>

## Gradient Overlay

A gradient is applied over the source image by default to improve legibility. It
can be removed by setting the _Gradient Omission_ extra to `True`. Removing
this gradient only affects the image gradient overlay - the dropshadow of the
text is not affected.

!!! warning "Text legibility"

    With the gradient omitted, text may be harder to read on bright images.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="True"
        data-right-label="False">
        <img src="../assets/inset/omit_gradient.webp"/>
        <img src="../assets/inset.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="34"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../assets/inset/mask-raw.webp"/>
        <img src="../assets/inset/mask.webp"/>
    </div>
