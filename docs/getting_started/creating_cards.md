---
title: Creating Title Cards
description: >
    Wrapping up the tutorial with Title Card creation.
tags:
    - Tutorial
    - Title Cards
---

# Creating Title Cards

There has been a lot of preamble, but the core of TitleCardMaker is making
Title Cards. We'll create Cards to showcase the effects of our Template, apply
the custom Font, and show how Cards can be further customized - then load them
into your media server.

!!! example "Example Series"

    This part of the tutorial refers to _Breaking Bad_ as the example Series.
    Those who Synced a Series __other than__ _Breaking Bad_ can still follow
    these steps; just apply them to whatever Series you chose.

## Episode Data

In TCM, "Episode Data" is pulled from the relevant Episode Data Source, which
in this case is a [global setting](./settings.md). This data is typically
refreshed [automatically](../user_guide/scheduler.md) when TCM creates Title
Cards (unless the Series is unmonitored), but for this tutorial we'll be doing
it manually.

1. Go to the _Breaking Bad_ Series configuration page - you can quickly access
it by searching for the title in the top left search bar (next to the TCM logo).

2. At the top of the page is a set of buttons where many global actions can be
performed. Open the `Episode Data` tab in the middle of the page and click the
<span class="example md-button">Refresh</span> button. TCM will now query your
global Episode Data Source for any new Episodes (although this is also done
when you first add a Series to TCM).

## Assign the Custom Font

3. Open the `Card Config` tab. In the `Font` dropdown, select the
`Better Call Saul` font created [earlier](./custom_font.md). Click
<span class="example md-button">Save</span>.

## Source Images

A "Source Image" is the underlying blank/textless image which TCM uses to create
most Title Cards. These are generally[^1] required, and TCM will pull these from
your Image Source Priority [global setting](./settings.md). These are typically
downloaded [automatically](../user_guide/scheduler.md) when TCM creates Title
Cards (unless the Series is unmonitored), but for this tutorial we'll be doing
it manually.

4. Open the "Files" tab. This tab shows image information for all Source Images
for each Episode of the Series. Since we just added _Breaking Bad_, all images
should show as missing.

5. Under _Source Images_, for Season 1 Episode 1, click the browse
:material-grid-large: icon. This will launch a browser for all Source Images on
TMDb. Clicking any image will request TCM download it and store it inside the
Source Image directory. Download any image.

    ??? tip "Image Resolution"

        In the corner of each image is a small ribbon that indicates the
        resolution of the image.

        When manually browsing the images on TMDb, your global minimum
        resolution is ignored.

    ![](../assets/tmdb_browse_images.jpg)

6. Close the image browser. The file for that Episode should now be filled in
with Source Image information.

## Title Cards

7. At the top of the page, click
<span class="example md-button">Create Title Cards</span>.

8. After waiting a small while for TCM to have created a few Cards, go to the
_Title Cards_ section on the _Files_ tab and expand the _View Card Images_
section.

9. You should see that Title Cards have been created using the Tinted Frame card
type (from the Template) with the custom Font applied.

10. Back in the _Episode Data_ tab, click the :material-eye-outline: icon
under the _Extras & Translations_ column for Season 2 Episode 1. In that window,
change the _Bottom Element_ input to `omit`, hit
<span class="example md-button">Save</span> and close out the window.

11. Click <span class="example md-button">Create Title Cards</span> again.
This Card should be remade with no logo in the bottom position, overriding what
was placed in the Template.

    ??? question "Why did the Template not apply?"

        Any Episode-level customizations _override_ Series-level customizations.

        Because we entered this extra for the Episode, the extra from the
        Series' Template is completely ignored.

    ??? question "Recreating Cards?"

        TCM re-analyzes a Card's settings to determine if it should be remade.
        In this case, since we just changed a single settinf for a single Card,
        TCM did not recreate the Card for any Episodes _other_ than Season 2
        Episode 1.

## Load Cards into Your Media Server

Creating Cards stores image files on disk. To see them in Plex, Jellyfin, or
Emby, TCM also needs to __load__ those Cards into the Series' libraries.

12. From the Series page, open the library actions dropdown for your media
server library and click <span class="example md-button">Load Cards</span> so
TCM pushes the new Cards to that library.

    ![Library Actions Dropdown](../user_guide/assets/library_actions-light.webp#only-light){.no-lightbox}
    ![Library Actions Dropdown](../user_guide/assets/library_actions-dark.webp#only-dark){.no-lightbox}

    Alternatively, the Scheduler task "Load all Title Cards into media servers"
    does this automatically on its schedule — see
    [The Scheduler](../user_guide/scheduler.md#load-title-cards).

13. Open the Series in your media server and confirm the Episode thumbnails
reflect your new Title Cards.

## Cleanup

The substantive part of the tutorial is over, and I recommend cleaning up the
artifacts from the tutorial. These are:

- Delete the Template
- Delete (or edit) the Sync
- Remove the `tcm-test` tag/label from _Breaking Bad_ in your media server
  (or Sonarr)
- If you adjusted a Scheduler Task, set it back to something sensible (and
  restart TCM)
- If you want different Cards, the Series and Fonts can also be deleted

!!! success "Tutorial Completed"

    With that finished, you have successfully grabbed Episode data, downloaded
    Source Images (manually _and_ automatically), created Title Cards, seen how
    Templates and Fonts work, observed Episode-level overrides, and loaded Cards
    into your media server.

    These are all the major components of TCM, and mark the end of the core
    tutorial. If you have any other questions, you can browse this documentation
    or reach out for help on the [Discord](https://discord.gg/bJ3bHtw8wH).

!!! question "What's Next?"

    - Expand your Sync filters (or create new Syncs) so TCM covers more than
      the example Series — see [Creating the First Sync](./first_sync/index.md)
    - Optionally learn [manually adding a Series](./add_series.md)
    - Tweak automated Task schedules in [Rescheduling Tasks](./scheduler.md)
    - Browse [Card Types](../card_types/index.md) for an overview of the
      available card styles within TCM.
    - Import community [Blueprints](../blueprints.md) for pre-made styles
    - Set up [Integrations](../user_guide/integrations.md) (webhooks, Tautulli)
    - Review [Environment Variables](../user_guide/environment_variables.md) if
      you need to make more advanced changes to TCM
    - Read the [User Guide](../user_guide/index.md) for detailed page-by-page
      documentation

[^1]:
    There are very few instances of [card types](../card_types/index.md) which
    do not require Source Images, but this is uncommon.
