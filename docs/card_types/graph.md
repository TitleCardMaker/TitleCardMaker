---
title: Graph Card Type
description: >
    An overview of the built-in Graph card type.
---

<link rel="stylesheet" type="text/css" href="https://unpkg.com/image-compare-viewer/dist/image-compare-viewer.min.css">
<script src="../../javascripts/imageCompare.js" defer></script>

# Graph Card Type

This card design was created by
[CollinHeist](https://github.com/CollinHeist).

This card type features a circular progress bar or "graph" which can be used to
indicate total series progress. The "progress" is parsed from the Episode Text,
(from the _Episode Text Format_ setting) which defaults to
`{episode_number} / {season_episode_max}` to display the progress within each
season. The graph displays as a circular ring with a fraction
(numerator/denominator) shown inside, and the title text is positioned next to
the graph.

<figure markdown="span" style="max-width: 70%">
  ![Example Graph Card](../assets/graph.webp)
</figure>

??? note "Labeled Card Elements"

    ![Labeled Graph Card Elements](./assets/graph/labeled.webp)

## Episode Text

Unlike most other card types, this card __does not__ feature separate season
and episode text. Instead, the inside of the graph is only customized via the
_Episode Text Format_ card setting. This defaults to:

```py
{episode_number} / {season_episode_max}
```

Which means that TCM will put the episode number on top (as the numerator), and
the maximum episode number in that given season on the bottom (as the
denominator).

!!! note "Expected Format"

    As a [format string](../user_guide/variables.md), this setting offers a lot
    of flexibility for how text is displayed on the card. However, since the
    graph's filled percentage is also derived from this setting, TCM expects the
    text in a specific format - namely with some `(top text) / (bottom text)`.
    If you provide text which is __not__ in this format, TCM will "force" it
    into this format.

    For example, typing `1 / 5` is completely valid and will result in the graph
    being drawn as one fifth full; but specifying `2` by itself will result in
    the text being displayed as `- / 2`, with TCM adding the `- /` part of the
    text.

!!! tip "Special Filled Formatting"

    When the text indicates that the "percentage" filled is 100% (typically on
    the last episode of the season), the coloring of both the numerator and
    denomitor is set.

    ![Custom Fill Formatting](./assets/graph/color-filled.webp)

### Font Size

By default, the size of the episode (graph) text is scaled dynamically with the
[Graph Radius](#radius) extra. However, if you would like to adjust the size of
this text separately, this can be adjusted with the _Graph Text Font Size_
extra.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="7.6"
        data-left-label="1.0"
        data-right-label="1.2">
        <img src="../assets/graph.webp"/>
        <img src="../assets/graph/v2/graph_text_font_size.webp"/>
    </div>

## Graph Customization

### Background Color

The background color of the graph element can be customized with the _Graph
Background Color_ extra. This color supports transparency.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="7.46"
        data-left-label="rgba(140,140,140,0.5)"
        data-right-label="rgba(37, 43, 39, 0.75)">
        <img src="../assets/graph.webp"/>
        <img src="../assets/graph/v2/graph_background_color.webp"/>
    </div>

### Fill Color

The color of the filled portion of the graph can be adjusted with the _Graph
Color_ extra. Adjusting this extra _also_ adjusts the color of the numerator
(the top part of the [Episode Text](#episode-text)). This color also supports
transparency.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="7.6"
        data-left-label="rgb(99,184,255)"
        data-right-label="gold">
        <img src="../assets/graph.webp"/>
        <img src="../assets/graph/v2/graph_color.webp"/>
    </div>

### Fill Scale

How full the active part of the graph appears can be adjusted with the _Fill
Scale_ extra. This is a number between 0 and 1.0, where 0 means no fill will
be drawn, and 1.0 means the entire [width](#width) of the graph will be colored,
and none of the background will be visible.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="10.5"
        data-left-label="0.6"
        data-right-label="0.4">
        <img src="../assets/graph.webp"/>
        <img src="../assets/graph/v2/fill_scale.webp"/>
    </div>

### Inset

How far inset from the edges of the image the graph element (and associated
text) appear can be adjusted with the _Graph Inset_ extra. This adjusts both the
horizontal and vertical inset towards the center of the image.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="7.46"
        data-left-label="75"
        data-right-label="25">
        <img src="../assets/graph.webp"/>
        <img src="../assets/graph/v2/graph_inset.webp"/>
    </div>

### Radius

The radius (size) of the graph can be adjusted with the _Graph Radius_ extra.
Adjusting this value will also dynamically adjust the size of the contained
[Episode Text](#episode-text) __unless__ the [Graph Text Font Size](#font-size)
is explicity specified.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="8.75"
        data-left-label="175"
        data-right-label="125">
        <img src="../assets/graph.webp"/>
        <img src="../assets/graph/v2/graph_radius.webp"/>
    </div>

### Width

The width of the graph (i.e. how thick the circle part is) can be adjusted with
the _Graph Width_ extra. This value serves as the base width of the
[Fill Scale](#fill-scale) setting.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="8.75"
        data-left-label="25"
        data-right-label="40">
        <img src="../assets/graph.webp"/>
        <img src="../assets/graph/v2/graph_width.webp"/>
    </div>

## Gradient Overlay

By default, TCM applies a subtle gradient overlay on top of the source image so
that the (default) white text appears more legible. If you would like to remove
this gradient overlay, set the _Gradient Omission_ extra to `True`.

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="22.83"
        data-left-label="False"
        data-right-label="True">
        <img src="../assets/graph.webp"/>
        <img src="../assets/graph/v2/omit_gradient.webp"/>
    </div>

## Position

The position of the graph and all text elements on the card can be adjusted
with the _Text Position_ extra. Available options are:

- **`lower left`** (default): Graph and text positioned in the lower left
- **`lower right`**: Graph and text positioned in the lower right
- **`upper left`**: Graph and text positioned in the upper left
- **`upper right`**: Graph and text positioned in the upper right
- **`left`**: Graph and text positioned on the left side (vertically centered)
- **`right`**: Graph and text positioned on the right side (vertically centered)

??? example "Example"

    <div class="image-compare example-card"
        data-starting-point="91.6"
        data-left-label="lower right"
        data-right-label="lower left">
        <img src="../assets/graph/v2/text_position.webp"/>
        <img src="../assets/graph.webp"/>
    </div>

## Mask Images

This card also natively supports [mask images](../user_guide/mask_images.md).
Like all mask images, TCM will automatically search for alongside the input
Source Image in the Series' source directory, and apply this atop all other Card
effects.

...
