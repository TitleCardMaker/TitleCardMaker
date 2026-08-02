---
title: Manually Adding a Series
description: >
    An introduction to manually adding a Series to TitleCardMaker.
tags:
    - Tutorial
    - Series
---

# Adding a Series

!!! info "Optional Step"

    Manually adding Series is __not__ the typical day-to-day workflow — Syncs
    (covered [earlier](./first_sync/index.md)) are how most users add libraries.
    This page is practice for one-off Series, testing, or Series that should
    not come from a Sync.

!!! note "Example Series"

    This example uses _Breaking Bad_. If you do not have it in your server, pick
    any other Series and follow the same steps. If _Breaking Bad_ was already
    added by your tutorial Sync, pick a different Series (or delete it from TCM
    first) so you can practice the Add flow.

1. Navigate back to the TitleCardMaker homepage - this can be done by clicking
:fontawesome-solid-tv: `Series` from the side navigation bar, or hitting
++shift++ + ++h++ (when a text box is not selected).

2. On the left-hand side bar, a navigation menu labeled
:material-magnify-plus-outline: `Add` should appear. Click this to go to the
"Add Series" page where you can add both Series and Blueprints.

    ![Add Series Page](../assets/add_series-light.webp#only-light){.no-lightbox}
    ![Add Series Page](../assets/add_series-dark.webp#only-dark){.no-lightbox}

3. Under `Browse Series`, type _Breaking Bad_ in the search bar and click
<span class="example md-button">Search</span>.

    !!! note "Search Source"

        If your default search connection is Emby, Jellyfin, or Plex and you
        don't have the Series in your server, you can choose a different
        connection, or just search TMDb.

    ??? warning "Sonarr Posters Not Loading"

        If the posters in your search results are not loading (all black), this
        is a result of Sonarr rejecting TCM's API request to view the poster.
        You can either disable authentication for local addresses within Sonarr
        (if using TCM locally), or just ignore this.

4. TCM will now query your selected connection for all Series which match that
name. _Breaking Bad_ should be among the top results. Before you click anything,
you may select any media server libraries you want associated with this Series.

    !!! example "Example Libraries"

        If I had _Breaking Bad_ in a server under two libraries, then I
        could select either or both libraries in the dropdown so that TCM knows
        to load Cards into those libraries.

        If I did not have _Breaking Bad_ in any of my servers, then I can
        leave this blank. This can always be changed later.

5. Click the search result and TCM will begin processing it. While you are on
this page, scroll down to the `Browse Blueprints` section at the bottom of the
page.

6. Type _Breaking Bad_ in the Blueprint search field and click
<span class="example md-button">Browse Blueprints</span>. TCM will display all
available Blueprints for this Series. For the purposes of this tutorial we will
_not_ be importing these — instead we'll customize the Cards ourselves. Keep in
mind this is _one way_ to find Blueprints.

    ??? question "What are Blueprints?"

        Blueprints are described in greater detail [here](../blueprints.md), but
        in-short: they are pre-made Title Card configurations that include
        everything needed to make Cards in a given style. This includes Fonts,
        Templates, Series customizations, etc.

7. Once TCM has finished processing the Series, go to the Series page in one of
a few ways:

    1. Click the Search box in the top left corner, then search for and select
    the Series.

        !!! tip "Keyboard Shortcut"

            You can enter the Search box by typing ++f++ or ++s++ (for `f`ind
            and `s`earch) anywhere in TCM (when a textbox is not selected).

    2. Return to the home page by clicking the :fontawesome-solid-tv: `Series`
    button on the left navigation bar, find the Series and click either
    the <span class="example md-button">View</span> button or the Series name.

8. Click the `Card Configuration` tab. Assign a Font and/or Template as desired,
then scroll down and click <span class="example md-button">Save</span>.

!!! success "Success"

    You've now manually added a Series to TCM. Continue to
    [Creating Title Cards](./creating_cards.md) if you still need to build Cards
    for it, or to [Rescheduling Tasks](./scheduler.md) to adjust automation.
