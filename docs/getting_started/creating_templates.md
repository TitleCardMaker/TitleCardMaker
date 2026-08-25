---
title: Creating Templates
description: >
    An introduction to how Templates can be used to adjust the settings of
    multiple Series at once.
tags:
    - Tutorial
    - Templates
---

# Creating a Template

Templates are a critical component of quickly customizing your TitleCardMaker
setup. A Template contains a set of customized settings, and any number of
Templates can be assigned to a Sync, Series, or Episode.

For example, a common use of Templates is to create separate distict Card styles
for Series of different genres/mediums. The most popular Template by far is an
"Anime" one which applies the [Anime card type](../card_types/anime.md), adds
Kanji translations, and may overwrite some card extras (settings).

For this tutorial we'll be creating a Template, and in a later step we'll apply
this automatically with a [Sync](./first_sync/index.md).

!!! note "Setting Priority"
        
    Template settings always take priority over any global settings, __unless__
    the Template value is _unset_ (left blank).

1. Navigate to the Template page by clicking :fontawesome-regular-clone:
`Templates` from the side navigation bar.

    ![Templates Page](../user_guide/assets/templates-light.webp#only-light){.no-lightbox}
    ![Templates Page](../user_guide/assets/templates-dark.webp#only-dark){.no-lightbox}

2. Create a new Template by clicking the
<span class="example md-button">New Template</span> button.

3. Expand the new Template by clicking the item called "Blank Template".

4. Rename the Template "Tinted Frame"

5. Under "Card Settings" change the card type to "Tinted Frame". 

    ??? question "Don't see Tinted Frame?"

        If you added this card type to your global list of
        [excluded card types](../user_guide/settings.md#excluded-card-types)
        then it will not appear. I recommend removing it and continuing with
        the tutorial.

6. Scroll down to "Extras" and select the "Tinted Frame" card type from the
dropdown menu on the right. Notice there is an item for each card type within
TCM.

7. Find the input labeled "Bottom Element" and select the `logo` entry.

    ??? question "What are Extras?"

        Extras are a way of overriding or customizing specific components of a
        Title Card. Extras are typically card type specific - and in this case
        the Tinted Frame card allows changing the bottom element from the
        season/episode text to a Logo image.

        Below most extras is a tooltip which often describes the available
        options and default value for that extra. If you want more detail, or
        a specific example, refer to the card's
        [documentation](https://titlecardmaker.com/card_types/).

8. Hit `Save Changes`.

!!! success "Template Created"

    You have now successfully created a Template. When applied, this will set
    the card type to the Tinted Frame card, and use a logo in the bottom
    element.

    We'll use this later in the tutorial.
