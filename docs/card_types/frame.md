---
title: Frame Card Type
description: >
    An overview of the built-in Frame card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Frame Card Type

This card design was created by
[CollinHeist](https://github.com/CollinHeist), and is inspired by the
official Adventure Time title cards from Season 8.

This card type features a Polaroid photo frame layout, with the Source
Image displayed within a white frame border. The title text is centered
within the frame, and the season and episode text can be positioned
around the title in various ways.

<figure markdown="span" style="max-width: 70%">
  ![Example Frame Card](../assets/frame.webp)
</figure>

## Episode Text Position

The position of the season and episode text relative to the title text can be
adjusted with the _Episode Text Position_ extra. This controls where the index
text appears:

- **`surround`** (default): Season text appears to the left of the title, and
episode text appears to the right of the title
- **`left`**: Both season and episode text appear to the left of the title,
stacked vertically
- **`right`**: Both season and episode text appear to the right of the title,
stacked vertically

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="25.75"
        data-left-label="left"
        data-right-label="surround">
        <img src="../assets/frame/episode_text_position.webp"/>
        <img src="../assets/frame.webp"/>
    </div>

## Episode Text Color

The color of the season and episode text can be adjusted with the _Episode Text
Color_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="crimson"
        data-right-label="rgb(80, 80, 80)">
        <img src="../assets/frame/episode_text_color.webp"/>
        <img src="../assets/frame.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

!!! example "Example"

    <figure markdown="span" style="max-width: 70%">
      ![Example Card with Mask](../assets/frame/mask.webp)
    </figure>
