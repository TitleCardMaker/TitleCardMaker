---
title: Calligraphy Card Type
description: >
    An overview of the built-in Calligraphy card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Calligraphy Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and the design was inspired by
[this](https://www.reddit.com/r/PlexTitleCards/comments/1699653/) set of title
cards for One Piece from
[/u/Recker_Man](https://www.reddit.com/user/Recker_Man).

These cards feature a prominent logo, with the index and title text above and
below. A calligraphy font is utilized for all text, and a grain / paper texture
is added (by default) to the image. It is recommended to use this with some
blurred or grayscale styling.

<figure markdown="span" style="max-width: 70%">
  ![Example Calligraphy Card](./assets/calligraphy.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Calligraphy Card Elements](./assets/calligraphy/labeled.webp)

## Texture Customization

By default, TCM adds a "texture" overlay image to all Cards of this type. This
is done to enhance the calligraphic-effect.

### Randomization

To add a slight variation between cards, TCM optionally varies the texture
overlay before it is applied. This can be disabled by setting the _Texture
Randomization Toggle_ extra to `False`.

### Toggle

Whether the texture is added at all can be configured with the _Texture Toggle_
extra. If this is specified as `False`, then the texture overlay will not be
applied.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="False"
        data-right-label="True">
        <img src="../assets/calligraphy/texture_toggle.webp"/>
        <img src="../assets/calligraphy.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <div class="image-compare example-card"
        data-starting-point="42.9"
        data-left-label="Mask Image"
        data-right-label="Resulting Title Card">
        <img src="../assets/calligraphy/mask-raw.webp"/>
        <img src="../assets/calligraphy/mask.webp"/>
    </div>
