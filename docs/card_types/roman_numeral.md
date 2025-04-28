---
title: Roman Numeral Card Type
description: >
    An overview of the built-in Roman Numeral card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Roman Numeral Card Type

This card design was created by [CollinHeist](https://github.com/CollinHeist),
and is based off the official title cards from "Devilman Crybaby". These cards
feature large roman numerals indicating the episode number, just behind the
title text.

<figure markdown="span" style="max-width: 70%">
  ![Example Roman Numeral Card](./assets/roman_numeral.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Marvel Card Elements](./assets/roman_numeral/labeled.webp)

## Background Color

!!! tip "Background Transparency"

    This color __can__ contain transparency if the configured [card
    extension](../user_guide/settings.md#card-extension) supports transparency.

The background color of these Cards may be adjusted with the _Background Color_
extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="55.177"
        data-left-label="rgba(12, 12, 12, 0.3)"
        data-right-label="black">
        <img src="../assets/roman_numeral/background_color.webp"/>
        <img src="../assets/roman_numeral.webp"/>
    </div>

## Roman Numerals

### Color

The color of the roman numerals (episode text) can be adjusted with the _Roman
Numeral Color_ extra. The color of the title text is adjusted with the normal
_Font Color_ setting.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="42.444"
        data-left-label="DodgerBlue"
        data-right-label="#AE2317">
        <img src="../assets/roman_numeral/roman_numeral_color.webp"/>
        <img src="../assets/roman_numeral.webp"/>
    </div>

### Fitting

Because of how spacey roman numerals can become for some numbers (like
843 = `DCCCXLIII`), the Maker wraps very long numerals and adjusts their size to
fit the screen. This is done automatically, and is not adjustable via the font
size (or any) specification.

??? example "Example"

    ![Example Roman Numeral Scaling](../assets/roman_numeral/numeral_fitting.jpg)

### Text

The text of the roman numerals is determined by the _Episode Text Format_
setting. This defaults to `{episode_number}`; but if you want to set it to
the absolute numbers, can be changed to `{absolute_number}` or
`{absolute_episode_number}`[^1].

## Season Text

### Color

The color of the season text can be adjusted with the _Season Text Color_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-vertical-mode="true"
        data-left-label="yellow"
        data-right-label="rgb(200, 200, 200)">
        <img src="../assets/roman_numeral/season_text_color.webp"/>
        <img src="../assets/roman_numeral.webp"/>
    </div>

### Position

The position of the season text is randomly selected by TCM based on a pre-
defined set of positions around each letter in the roman numeral text.

This is done by selecting a random roman numeral, then randomly selecting a
position around that letter. TCM then runs some validation to ensure that the
season text does not overlap the title text.

??? note "All Possible Season Text Positions"

    ![Example I Positions](../assets/roman_numeral/position_i.jpg)
    ![Example V Positions](../assets/roman_numeral/position_v.jpg)
    ![Example X Positions](../assets/roman_numeral/position_x.jpg)
    ![Example L Positions](../assets/roman_numeral/position_l.jpg)
    ![Example C Positions](../assets/roman_numeral/position_c.jpg)
    ![Example D Positions](../assets/roman_numeral/position_d.jpg)
    ![Example M Positions](../assets/roman_numeral/position_m.jpg)

### Size

The size of the season text can be adjusted with the _Season Text Size_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-vertical-mode="true"
        data-left-label="1.4"
        data-right-label="1.0">
        <img src="../assets/roman_numeral/season_text_size.webp"/>
        <img src="../assets/roman_numeral.webp"/>
    </div>

## Mask Images

This card __does not__ support [mask images](../user_guide/mask_images.md). This
is primarily due to the fact that Source Images are not required for the Card,
so there is no matching associated mask image to search for.

[^1]: For a complete list of variables, see [here](../user_guide/variables.md).
