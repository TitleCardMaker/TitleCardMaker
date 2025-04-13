---
title: Marvel Card Type
description: >
    An overview of the built-in Marvel card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Marvel Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist)
and RedHeadJedi, and is styled to match RedHeadJedi's Marvel Cinematic Universe
poster set. These cards feature a white border on the left, top, and right
edges, with a black text box at the bottom containing all text.

<figure markdown="span" style="max-width: 70%">
  ![Example Marvel Card](./assets/marvel.webp)
</figure>

## Border Customization

The border elements can be customized in several ways.

### Border Color

The color of the left, top, and right borders can be adjusted with the
_Border Color_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="MediumSpringGreen"
        data-right-label="white">
        <img src="../assets/marvel/border_color.webp"/>
        <img src="../assets/marvel.webp"/>
    </div>

### Border Size 

The width of the borders can be adjusted with the _Border Size_ extra. The size
of the border also changes how far in from the edges the season and episode text
are positioned.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="25"
        data-right-label="55">
        <img src="../assets/marvel/border_size.webp"/>
        <img src="../assets/marvel.webp"/>
    </div>

### Border Toggle

The borders can be completely hidden by setting the _Hide Border_ extra to
`True`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="True"
        data-right-label="False">
        <img src="../assets/marvel/border_toggle.webp"/>
        <img src="../assets/marvel.webp"/>
    </div>

## Text Box

The bottom text box contains all text elements and can be customized.

### Text Box Color

The color of the text box itself can be changed with the _Text Box Color_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="rgb(139, 126, 102)"
        data-right-label="black">
        <img src="../assets/marvel/box_color.webp"/>
        <img src="../assets/marvel.webp"/>
    </div>

### Text Box Height

The height of the text box can be adjusted with the _Text Box Height_ extra.
This __does not__ adjust the positioning of the title or index text, so these
will need to be shifted accordingly if you want the text to stay centered.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="150"
        data-right-label="200">
        <img src="../assets/marvel/box_height.webp"/>
        <img src="../assets/marvel.webp"/>
    </div>

## Episode Text

The season and episode text can be customized independently of the title text.

### Color

The color of the episode text can be adjusted with the _Episode Text Color_
extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="orange"
        data-right-label="white">
        <img src="../assets/marvel/episode_text_color.webp"/>
        <img src="../assets/marvel.webp"/>
    </div>

### Position

The position of the episode text can be adjusted using the _Episode Text
Location_ extra. If set to `compact`, the season and episode text will be
positioned directly next to the title text; and if set to `fixed` then the text
will be fixed in place on the edge of the image.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="compact"
        data-right-label="fixed">
        <img src="../assets/marvel/episode_text_location.webp"/>
        <img src="../assets/marvel.webp"/>
    </div>

## Text Fitting

The _Fit Text_ extra controls whether the font size is dynamically adjusted to
fit within the text box bounds. When enabled (the default), text will
automatically scale to fit. When disabled, text may overflow if too long.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="False"
        data-right-label="True">
        <img src="../assets/marvel/text_fitting_disabled.webp"/>
        <img src="../assets/marvel/text_fitting_enabled.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="17.35"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../assets/marvel/mask-raw.webp"/>
        <img src="../assets/marvel/mask.webp"/>
    </div>
