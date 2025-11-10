---
title: Fade Card Type
description: >
    An overview of the built-in Fade card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Fade Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and the base idea for this card comes from [Yozora](https://github.com/Yozora).

This card type is a modification of the Standard style that is intended to be
used for 4:3 aspect-ratio source images. It features a fade overlay showcasing
the source image, with text positioned on the left side of the card. A logo can
also be placed above the title text.

<figure markdown="span" style="max-width: 70%">
  ![Example Fade Card](./assets/fade.webp)
</figure>

## Episode Text

Unless _explicitly_ stated otherwise, all "episode text" customizations refer to
both the season and episode text.

### Color

The color of the episode text can be adjusted with the _Episode Text Color_
extra. This will change the color of both the season and episode text.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="22"
        data-left-label="rgb(233,20,35)"
        data-right-label="rgb(163, 163, 163)">
        <img src="../assets/fade/episode_text_color.webp"/>
        <img src="../assets/fade.webp"/>
    </div>

### Size

The size of the episode text can be adjusted with the _Episode Text Font Size_
extra. Like all font sizes, values greater than `#!yaml 1.0` will increase the
size of the text, and values less than `#!yaml 1.0` will decrease it.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="15"
        data-left-label="1.3"
        data-right-label="1.0">
        <img src="../assets/fade/episode_text_font_size.webp"/>
        <img src="../assets/fade.webp"/>
    </div>

## Logo

A logo file can optionally be added above the title text on the left side of the
card.

### Size

The size of the logo can be adjusted with the _Logo Size_ extra. Like all sizes,
values greater than `#!yaml 1.0` will increase the size of the logo, and values
less than `#!yaml 1.0` will decrease it.

!!! warning "Size Warning"

    This size extra works differently than the sizing extras on many other card
    types, as this extra only shrinks logos. This is to prevent extending beyond
    the bounds of the black overlay.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="14.5"
        data-left-label="0.3"
        data-right-label="1.0">
        <img src="../assets/fade/logo_size.webp"/>
        <img src="../assets/fade.webp"/>
    </div>

## Separator Character

If both the season and episode text are displayed on the Card, then a separator
character is added between them. This character can be adjusted with the
_Separator Character_ extra. The default separator is `•`.

The color of this character will be controlled by the
[_Episode Text Color_](#color) extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="90"
        data-left-label="-"
        data-right-label="•">
        <img src="../assets/fade/separator.webp"/>
        <img src="../assets/fade.webp"/>
    </div>

## Mask Images

Because of the image overlay, this card does not support
[mask images](../user_guide/mask_images.md).
