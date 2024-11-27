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

## Deep Blur Toggle

If the Card is being blurred as a result of an [unwatched
style](../user_guide/settings.md#watched-and-unwatched-episode-styles), TCM
automatically applies a stronger / more blurry effect to the Card to match the
'calligraphy on paper' aesthetic. This can be disabled by setting the _Deep
Blur Unwatched Toggle_ extra to `False`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="True"
        data-right-label="False">
        <img src="../assets/calligraphy/deep_blur_enabled.webp"/>
        <img src="../assets/calligraphy/deep_blur_disabled.webp"/>
    </div>

!!! note "Interaction with the Global Blur Profile Setting"

    If you have customized the blur profile of the Calligraphy card by adjusting
    the [global setting](../user_guide/settings.md#global-blur-profiles), then
    the custom blur profile will only take effect if this setting is _disabled_
    or if the Card is blurred for a _watched_ Episode.

## Episode Text

Unless explicitly stated otherwise, all of the following extras will refer to
both the season _and_ episode text. "Episode text" is used for brevity.

### Coloring

The color of the season and episode text can be adjusted with the _Episode Text
Color_ extra. If unspecified, this defaults to match the color of the title
text.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="rgb(81, 124, 102)"
        data-right-label="white">
        <img src="../assets/calligraphy/episode_text_color.webp"/>
        <img src="../assets/calligraphy.webp"/>
    </div>

### Size

The size of the season and episode text can be adjusted with the _Episode Text
Font Size_ extra. Like all font sizes, values greater than `#!yaml 1.0` will
increase the size of the text, and values less than `#!yaml 1.0` will decrease
it.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="1.5" data-right-label="1.0">
        <img src="../assets/calligraphy/episode_text_font_size.webp"/>
        <img src="../assets/calligraphy.webp"/>
    </div>

## Logo Size

If a logo file is supplied and available, that file will be added to the center
of the card. The size of this logo can be adjusted with the _Logo Size_ extra.
Like all sizes, values greater than `#!yaml 1.0` will increase the size of the
image, and values less than `#!yaml 1.0` will decrease it.

Adjusting this size will also change where the [Episode Text](#episode-text) is
positioned, as TCM moves that text just above the bounds of the logo.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="0.8" data-right-label="1.0">
        <img src="../assets/calligraphy/logo_size.webp"/>
        <img src="../assets/calligraphy.webp"/>
    </div>

## Separator Character

If both the season and episode text are displayed on the Card, then a separator
character is added between them. This character can be adjusted with the
_Separator Character_ extra.

The color of this character will be controlled by the
[_Episode Text Color_](#coloring) extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="56"
        data-left-label="/"
        data-right-label="-">
        <img src="../assets/calligraphy/separator.webp"/>
        <img src="../assets/calligraphy.webp"/>
    </div>

## Shadow Color

Rather than a stroke, TCM adds a drop shadow to all elements on this card in
order to improve legibility. The color of this shadow can be changed with the
_Shadow Color_ extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="50"
        data-left-label="rgb(81, 124, 102)"
        data-right-label="black">
        <img src="../assets/calligraphy/shadow_color.webp"/>
        <img src="../assets/calligraphy.webp"/>
    </div>

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
        data-starting-point="93.3"
        data-left-label="False"
        data-right-label="True">
        <img src="../assets/calligraphy/texture_toggle.webp"/>
        <img src="../assets/calligraphy.webp"/>
    </div>

## Title Offset

TCM automatically applies an "offset" to some multi-line titles to give the
stylized appearance of the two lines not being centered in the page. This can be
disabled by setting the _Offset Title Toggle_ extra to `False`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="30.5"
        data-left-label="False"
        data-right-label="True">
        <img src="../assets/calligraphy/title_offset_off.webp"/>
        <img src="../assets/calligraphy/title_offset_on.webp"/>
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
