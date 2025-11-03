---
title: Divider Card Type
description: >
    An overview of the built-in Divider card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Divider Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and was inspired by the title card interstitials in season 3 of  _Overlord_.

Cards of this design feature the title and index text separated by a vertical
divider bar, with text positioned at various points around the image. The design
is intended for shorter titles and unobtrusive text placement.

<figure markdown="span" style="max-width: 70%">
  ![Example Divider Card](./assets/divider.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Divider Card Elements](./assets/divider/labeled.webp)

## Text Position

The position of all text elements (title, divider, and index) on the image can
be adjusted with the _Text Position_ extra. This can be set to `upper left`,
`upper right`, `right`, `lower right`, `lower left`, or `left`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-right-label="left"
        data-left-label="lower right">
        <img src="../assets/divider/text_position.webp"/>
        <img src="../assets/divider.webp"/>
    </div>

## Title Text Side

Which side of the divider the title text compared to the index text appears on
can be adjusted with the _Title Text Side_ extra. This can be set to `left` or
`right`. When set to `left`, the title appears before the divider (left side
when viewing left-to-right), and when set to `right`, the title appears after
the divider (right side).

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="91.33"
        data-left-label="left"
        data-right-label="right">
        <img src="../assets/divider.webp"/>
        <img src="../assets/divider/title_text_side.webp"/>
    </div>

## Text Gravity

The alignment of the index text (relative to itself) can be adjusted with the
_Text Gravity_ extra. This can be set to `center`, `east`, or `west`.

If unspecified, this defaults based on the _Title Text Side_: `west` when
_Title Text Side_ is `left`, and `east` when _Title Text Side_ is `right`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="91.33"
        data-left-label="center"
        data-right-label="west">
        <img src="../assets/divider.webp"/>
        <img src="../assets/divider/text_gravity.webp"/>
    </div>

## Divider Color

The color of the vertical divider bar between the title and index text can be
adjusted with the _Divider Color_ extra. If unspecified, this defaults to
matching the Font color.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="77.2"
        data-left-label="white"
        data-right-label="crimson">
        <img src="../assets/divider.webp"/>
        <img src="../assets/divider/divider_color.webp"/>
    </div>

## Divider Width

The width of the vertical divider bar between the title and index text can be
adjusted with the _Divider Width_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="80.2"
        data-left-label="7"
        data-right-label="14">
        <img src="../assets/divider.webp"/>
        <img src="../assets/divider/divider_width.webp"/>
    </div>

## Text Stroke Color

The color of the text stroke (outline) can be adjusted with the _Text Stroke
Color_ extra. This stroke provides a blurred background effect behind the text
for improved readability. The default is `black`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="84.3"
        data-left-label="black"
        data-right-label="crimson">
        <img src="../assets/divider.webp"/>
        <img src="../assets/divider/stroke_color.webp"/>
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
        <img src="../assets/divider/mask-raw.webp"/>
        <img src="../assets/divider/mask.webp"/>
    </div>
