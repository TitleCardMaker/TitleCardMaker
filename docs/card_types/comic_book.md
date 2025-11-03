---
title: Comic Book Card Type
description: >
    An overview of the built-in Comic Book card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Comic Book Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and is stylized after classic Comic Book pages. These cards feature two
prominent banners at the top and bottom of the card. The top banner is for the
index (season and episode) text, and the bottom one is for the title text.

<figure markdown="span" style="max-width: 70%">
  ![Example Comic Book Card](./assets/comic_book.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Comic Book Card Elements](./assets/comic_book/labeled.webp)

## Banner Fill Color

The fill color of both the title and index banners can be adjusted with the
_Banner Fill Color_ extra. This affects the semi-transparent background
rectangle behind the text boxes on both banners.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="60.74"
        data-left-label="rgba(235,73,69,0.6)"
        data-right-label="rgba(40,40,80,0.7)">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/banner_fill_color.webp"/>
    </div>

## Title Banner

The title banner appears at the bottom of the card and contains the title text.

### Edge Color

The edge/stroke color of the title text box can be adjusted with the _Text Box
Edge Color_ extra. If unspecified, this defaults to matching the Font color.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="43.76"
        data-left-label="black"
        data-right-label="white">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/textbox_edge_color.webp"/>
    </div>

### Fill Color

The fill color of the text box containing the title text can be adjusted with
the _Title Textbox Fill Color_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="60.74"
        data-left-label="white"
        data-right-label="rgba(190,190,190)">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/title_textbox_fill_color.webp"/>
    </div>

### Rotation Angle

The angle at which the title text and banner are rotated can be adjusted with
the _Title Text Rotation Angle_ extra. Positive angles tilt the text clockwise
and negative angles tilt it counterclockwise. The default is `-4.0` degrees.

This can be an explicit angle (i.e. `#!yaml -10`), or TCM can dynamically select
a random angle in some random bounds using the format `random[lower, upper]`,
where `lower` and `upper` are the minimum and maximum angle values in degrees.
For example, `#!yaml random[-10, 10]` will randomly select an angle between -10 and
10 degrees.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50.0"
        data-right-label="-4.0"
        data-left-label="4.0">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/title_text_rotation_angle.webp"/>
    </div>

### Vertical Shift

The vertical position of the title banner (relative to the text box) can be
adjusted with the _Title Banner Vertical Shift_ extra. Negative values shift
the banner up, and positive values shift it down.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="85.0"
        data-left-label="0"
        data-right-label="-72">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/title_banner_vertical_shift.webp"/>
    </div>

### Toggle

The title banner can be completely hidden by setting the _Hide Title Banner_
extra to `True`. When hidden, only the title text box (if enabled) will be
displayed, without the banner background.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="60.74"
        data-left-label="True"
        data-right-label="False">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/hide_title_banner.webp"/>
    </div>

## Index Banner

The index banner appears at the bottom of the card and contains the index
(season and episode) text.

### Position

The horizontal position of the index text (and banner) can be adjusted with the
_Index Text Position_ extra. This can be set to `left`, `middle`, or `right`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="31.2"
        data-left-label="left"
        data-right-label="middle">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/index_text_position.webp"/>
    </div>

### Edge Color

The edge/stroke color of the title text box can be adjusted with the _Text Box
Edge Color_ extra. If unspecified, this defaults to matching the Font color.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="43.76"
        data-left-label="black"
        data-right-label="white">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/textbox_edge_color.webp"/>
    </div>

### Fill Color

The fill color of the text box containing the index text can be adjusted with
the _Index Textbox Fill Color_ extra. If unspecified, this defaults to matching
the Title Textbox Fill Color.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="10.1"
        data-left-label="white"
        data-right-label="gold1">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/index_textbox_fill_color.webp"/>
    </div>

### Rotation Angle

The angle at which the index text and banner are rotated can be adjusted with
the _Index Text Rotation Angle_ extra. Positive angles tilt the text down, and
negative angles tilt it up. The default is `-4.0` degrees.

This can be an explicit angle (i.e. `#!yaml -10`), or TCM can dynamically select
a random angle in some random bounds using the format `random[lower, upper]`,
where `lower` and `upper` are the minimum and maximum angle values in degrees.
For example, `#!yaml random[-10, 10]` will randomly select an angle between -10 and
10 degrees.

!!! warning "Zero Degree Angle"

    Because of the coordinate calculations used in this Card's logic, an angle
    of `#!yaml 0.0` degrees cannot be specified - to use no rotation (flat
    banner), specify a very small number like `#!yaml 0.01`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="10.1"
        data-left-label="-4.0"
        data-right-label="0.01">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/index_text_rotation_angle.webp"/>
    </div>

### Vertical Shift

The vertical position of the index banner can be adjusted with the _Index Banner
Vertical Shift_ extra. Negative values shift the banner up, and positive values
shift it down.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="10.1"
        data-left-label="0"
        data-right-label="72">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/index_banner_vertical_shift.webp"/>
    </div>

### Toggle

The title banner can be completely hidden by setting the _Hide Index Banner_
extra to `True`. When hidden, only the index text box (if enabled) will be
displayed, without the banner background.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="10.1"
        data-left-label="False"
        data-right-label="True">
        <img src="../assets/comic_book/hide_index_banner.webp"/>
        <img src="../assets/comic_book.webp"/>
    </div>

## Episode Text Color

The color of the index text (season and episode) can be adjusted with the
_Episode Text Color_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="10.1"
        data-left-label="black"
        data-right-label="SaddleBrown">
        <img src="../assets/comic_book.webp"/>
        <img src="../assets/comic_book/episode_text_color.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="28.4"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../assets/comic_book/mask-raw.webp"/>
        <img src="../assets/comic_book/mask.webp"/>
    </div>
