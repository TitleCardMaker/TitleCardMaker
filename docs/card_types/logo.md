---
title: Logo Card Type
description: >
    An overview of the built-in Logo card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Logo Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist).

The Logo card is a variation of the Standard title card built around a **central
logo**, with the episode title along the bottom edge and season or episode index
text near the lower center. It is intended for very spoiler-sensitive series
(for example, reality TV), where showing a traditional image may give away too
much.

The background can be a **solid color** or a **blurred/styled Source Image**. If
you use a background image, an Art Unwatched or Watched style is recommended.

<figure markdown="span" style="max-width: 70%">
  ![Example Logo Card](./assets/logo.webp)
</figure>

## Background

### Solid color

When [_Background Image Enabling_](#background-image) is off, the card is
drawn on a flat color. Set the _Background Color_ extra (`background`) to any
valid color string. It is ignored when a background image is used.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="DarkSlateGray4"
        data-right-label="black">
        <img src="../assets/logo/background_color.webp"/>
        <img src="../assets/logo.webp"/>
    </div>

### Background image

Set _Background Image Enabling_ to `True` to use the Series Source Image as the
background (resized like other cards).

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="True"
        data-right-label="False">
        <img src="../assets/logo/use_background_image.webp"/>
        <img src="../assets/logo.webp"/>
    </div>

### Blurring

If blurring is enabled (via the watched or unwatched style), then the background
image/color will be blurred. If the _Blur Image Only_ extra is set to `True`
then the logo will __not__ be blurred.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="True"
        data-right-label="False">
        <img src="../assets/logo/blur_only_image_true.webp"/>
        <img src="../assets/logo/blur_only_image_false.webp"/>
    </div>

## Logo File

Every Logo card requires a logo image. TCM composites it near the top center,
scaled to fit within maximum width and height bounds (then scaled again by
[_Logo Size_](#logo-size)).

### Logo size

The _Logo Size_ extra scales the logo relative to the card’s internal maximum
dimensions.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="0.8"
        data-right-label="1.0">
        <img src="../assets/logo/logo_size.webp"/>
        <img src="../assets/logo.webp"/>
    </div>

### Horizontal shift

The _Logo Horizontal Shift_ extra moves the logo horizontally. Positive values
shift the logo left; negative values shift it right.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="20"
        data-right-label="0">
        <img src="../assets/logo/logo_horizontal_shift.webp"/>
        <img src="../assets/logo.webp"/>
    </div>

### Vertical shift

The _Logo Vertical Shift_ extra moves the logo vertically. Positive values shift
the logo down; negative values shift it up.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="20"
        data-right-label="0">
        <img src="../assets/logo/logo_vertical_shift.webp"/>
        <img src="../assets/logo.webp"/>
    </div>

## Episode Text

Unless stated otherwise, “episode text” refers to **both** season and episode
strings and how they are composed together.

### Color

The _Episode Text Color_ extra sets the fill used for the visible season and
episode text (after the dark outline pass).

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="Gold2"
        data-right-label="#CFCFCF">
        <img src="../assets/logo/episode_text_color.webp"/>
        <img src="../assets/logo.webp"/>
    </div>

### Font Size

The _Episode Text Font Size_ extra scales the index text. Like other font size
extras, values greater than `#!yaml 1.0` increase size and values below
`#!yaml 1.0` decrease it.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="1.3"
        data-right-label="1.0">
        <img src="../assets/logo/episode_text_font_size.webp"/>
        <img src="../assets/logo.webp"/>
    </div>

### Vertical shift

The _Episode Text Vertical Shift_ extra nudges the combined index text up or
down.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="20"
        data-right-label="0">
        <img src="../assets/logo/episode_text_vertical_shift.webp"/>
        <img src="../assets/logo.webp"/>
    </div>

### Separator Character

When both season and episode text are shown, they are separated by the
_Separator Character_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="//"
        data-right-label="•">
        <img src="../assets/logo/separator.webp"/>
        <img src="../assets/logo.webp"/>
    </div>

## Title Text

Title text uses your configured Font settings. The _Stroke Text Color_ extra 
controls the color of the wide stroke drawn behind the title for contrast.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="red"
        data-right-label="black">
        <img src="../assets/logo/stroke_color.webp"/>
        <img src="../assets/logo.webp"/>
    </div>

## Gradient Overlay

A gradient image can be composited over the background (and logo) before text is
drawn to keep titles readable on bright frames. The _Gradient Omission_ extra
skips that overlay when `True`.

On **background images**, turning the gradient off can make text harder to read
on bright scenes.

!!! example "Example (gradient omitted)"

    ![Logo card with background image and gradient omitted](../assets/logo/omit_gradient.webp)

## Mask images

This card supports [mask images](../user_guide/mask_images.md). TCM searches next
to the `source_file` path for episode-specific or generic mask files and
composites them near the end of the pipeline.

!!! note "Blur and grayscale"

    Mask overlays are **not** applied when the card is created with blur or
    grayscale styling enabled (same behavior as other card types using the
    shared mask helper).
