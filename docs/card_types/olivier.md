---
title: Olivier Card Type
description: >
    An overview of the built-in Olivier card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Olivier Card Type

This card design was created by Reddit user
[/u/Olivier_286](https://www.reddit.com/user/Olivier_286), with additional
development by [CollinHeist](https://github.com/CollinHeist) and Yozora.

This card features left-aligned title and episode text over the source image.
It is structurally very similar to the Star Wars card, but does not include
the star-filled gradient overlay.

<figure markdown="span" style="max-width: 70%">
  ![Example Olivier Card](./assets/olivier.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Olivier Card Elements](./assets/olivier/labeled.webp)

## Episode Text

The episode text is split into a prefix (e.g. `EPISODE`) and a number (e.g.
`ONE`). By default, the episode text is formatted as:

```python
EPISODE {to_cardinal(episode_number)}
```

??? question "What does this mean?"

    If the above text looks like gibberish to you, you can read more about how
    format strings work in TCM [here](../user_guide/variables.md).

    In short - the above text translates to the text `EPISODE` with a cardinal-
    conversion of the episode number (cardinal being one, two, etc.). This means
    the default episode text comes out like `EPISODE ONE`, `EPISODE TWO`, etc.

The horizontal position of the number is adjusted automatically based on the
length of the prefix text.

### Color

The color of the episode text can be adjusted with the _Episode Text Color_
extra. If unspecified, it defaults to `white`.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="white"
        data-right-label="#AB8630">
        <img src="../assets/olivier.webp"/>
        <img src="../assets/olivier/episode_text_color.webp"/>
    </div>

### Size

The size of the episode text can be adjusted with the _Episode Text Font Size_
extra. Values above `#!yaml 1.0` increase the size of the text, and values below
`#!yaml 1.0` decrease it.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="1.0"
        data-right-label="0.8">
        <img src="../assets/olivier.webp"/>
        <img src="../assets/olivier/episode_text_font_size.webp"/>
    </div>

### Vertical Shift

The vertical position of the episode text can be adjusted with the _Episode
Text Vertical Shift_ extra. Positive values shift the episode text down, and
negative values shift it up.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="0"
        data-right-label="50">
        <img src="../assets/olivier.webp"/>
        <img src="../assets/olivier/episode_text_vertical_shift.webp"/>
    </div>

## Text Stroke Color

The color of the stroke applied to the title text can be adjusted with the _Text
Stroke Color_ extra. If unspecified, it defaults to `black`.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="black"
        data-right-label="crimson">
        <img src="../assets/olivier.webp"/>
        <img src="../assets/olivier/stroke_color.webp"/>
    </div>

## Gradient Overlay

Unlike most cards, the gradient overlay is **not** applied by default. To add a
gradient overlay, set the _Gradient Omission_ extra to `False`.

!!! warning "Text legibility"

    With the gradient omitted, text may be harder to read on bright images.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="True"
        data-right-label="False">
        <img src="../assets/olivier.webp"/>
        <img src="../assets/olivier/omit_gradient.webp"/>
    </div>

## Gradient Type

When a gradient overlay is enabled, the _Gradient Type_ extra controls which
gradient image is used. This can be set to `original` or `improved` (default).

The `original` gradient is the same asset used by the Overline card (rotated
90°), while the `improved` gradient is a custom gradient designed specifically
for this card type.

A custom gradient can also be provided as an ImageMagick command prefixed with
`custom:`.

??? example "Examples"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="original"
        data-right-label="improved">
        <img src="../assets/olivier/gradient_type.webp"/>
        <img src="../assets/olivier/omit_gradient.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="14.25"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../assets/olivier/mask-raw.webp"/>
        <img src="../assets/olivier/mask.webp"/>
    </div>
