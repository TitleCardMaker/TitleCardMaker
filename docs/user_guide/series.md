---
title: Series Page
description: >
    All Series-specific customizations and actions.
tags:
    - Series
---

# Series

When a Series is clicked on from the home page or the search bar, you will
access the "Series page" (at `/series/{series_id}`) where all Series-level
options, Title Card customizations, files, and actions can be viewed.

![Series Page](../assets/series_light.webp#only-light){.no-lightbox}
![Series Page](../assets/series_dark.webp#only-dark){.no-lightbox}

This page is organized into several main sections: the action bar at the top,
the poster and preview area, and multiple tabs containing different
configuration options.

## Action Bar

The action bar at the top of the page contains all the primary actions you can
perform on a Series.

### Navigation Arrows

On the far left and right of the action bar are arrows
(:material-arrow-left-circle: and :material-arrow-right-circle:). Clicking
either of these will navigate to the previous and next Series _alphabetically_
from the current Series.

If you click either arrow and the current page does not change _and_ the arrow
becomes greyed out, then there is no next or previous Series to navigate to.

### Monitored Status

Each Series can be _monitored_ and _unmonitored_. All Series start as monitored
unless explicitly unmonitored, which can be done by clicking the status button
in the action bar. The status is indicated by different colored icons:

- :material-eye: Green - Monitored
- :material-eye-off: Yellow - Unmonitored  
- :material-close-circle: Red - Disabled

Unmonitored Series do __not__ do the following actions _automatically_ (all
actions can still be done manually):

- Refresh Episode data - i.e. check for new Episodes, look for modified Episode
titles, etc.
- Add Episode translations
- Download missing Source Images

And disabled Series do not do __anything__ automatically.

The Tasks in [the scheduler](./scheduler.md) that are responsible for the
above actions will skip all unmonitored or disabled Series.

### Create Title Cards

!!! note "Scheduled Action"

    This action occurs automatically as part of the
    [Create Title Cards](./scheduler.md) Task.

<span class="example md-button">Create Title Cards</span> can be pressed to
prompt TCM to begin updating existing, _and_ create new Title Cards. This action
encompasses the following:

1. Refreshes all Episode data[^1]; then
2. Queries any assigned Libraries for updated Episode watched statuses; then
3. Looks for any missing Episode translations; then
4. Download any missing Source Images[^2]; and finally
5. Begins Title Card creation

!!! tip "Background Execution"

    Because Title Card creation can take a long time, Card creation is executed
    in a background thread. This also means that if you start Card creation,
    make a change which would prompt new Cards, and then restart Card creation;
    TCM will create, delete, then re-create the Cards.

### Library Actions

For every library which the currently selected Series is assigned to, a dropdown
menu will appear showing the library and Connection name (e.g. `TV Shows | Plex`).
This dropdown contains several actions specific to that library:

![Library Actions Dropdown](../assets/library_actions-light.webp#only-light){ .no-lightbox  }
![Library Actions Dropdown](../assets/library_actions-dark.webp#only-dark){ .no-lightbox }

#### Title Card Loading

!!! note "Scheduled Action"

    This action occurs automatically as part of the
    [Load Title Cards](./scheduler.md) Task. Title Cards are never automatically
    force-reloaded.

- **Load Cards** - Loads only _unloaded_ Title Cards into the associated Connection and library. This only affects Title Cards which were changed (and not re-loaded), or never loaded in the first place.

- **Force Reload Cards** - Reloads _all_ Title cards into the associated Connection and library. This is much slower than normal Card loading, but can be used as needed - most commonly when the metadata of a Media Server is reset and previously loaded Title Cards are removed.

- **Selectively Reload Season** - Open a dialog allowing you to choose specific
seasons to reload or force reload.

#### Remove Episode Labels

!!! note "Plex Servers Only"

    This option only appears for libraries associated with Plex servers.

TitleCardMaker looks for specific labels on Episodes within Plex to determine
whether it is able to download Source Images from that Episode. This is done to
avoid grabbing a "Source Image" which is actually a previously loaded Title
Card, or some image with a Kometa (PMM) overlay applied.

The **Remove Episode Labels** button removes the labels which TCM uses to track whether an Episode can provide a Source Image. This applies to all Episodes of this Series within Plex.

### Delete Actions

On the right side of the action bar is a red **Delete** dropdown menu with three options:

- **Source Images** - Deletes all Source Images associated with this Series
- **Title Cards** - Deletes all Title Card files and removes them from the database
- **Series** - Deletes the Series itself

!!! danger "Irreversible Actions"

    All delete actions are permanent and cannot be undone. The Series deletion
    will also remove all associated Source Images if you have enabled the
    [Delete Series Source Images](./settings.md#source-image-deletion) option.

## Progress Bar

Underneath the actions bar is a progress bar which displays the total number of
currently created and missing Title Cards.

This is updated periodically, but clicking the card text will force TCM to
refresh that information.

??? tip "Color Accessibility"

    If the default colors are hard to see, these can be changed to higher
    contrast options by toggling the global 
    [Color Impaired Mode](./settings.md#color-impaired-mode) setting.

??? question "More Cards than Episodes?"

    If the listed Card count is higher than the total number of Episodes, then
    most likely you have enabled [Multi-Library Filename
    Support](./settings.md#multi-library-file-naming), and TCM has created
    a separate Card for each library of the Series.

## Poster and Preview Area

### Series Poster

When a Series is added to TitleCardMaker, TCM looks for a poster in your media
servers (Plex, Emby, Jellyfin) - _if a library has been assigned_. If one cannot
be found, it searches TMDb, or TVDb.

This poster is purely visual and is not used for Title Card creation.

??? tip "Changing the Poster"

    If you would like to change the poster, hover over and click the poster.
    This will launch a popup where you can either:

    - Enter a URL which TCM will download the poster from
    - Query TMDb for a poster using the search icon
    - Upload a file from your machine
    - Pull the poster from any linked Media Servers

    After selecting any of these options, clicking the appropriate button will swap out
    the currently visible poster for the Series.

### Live Preview

On the top right side of the page is a Title Card live preview which can be used
to quickly observe changes to Cards.

This preview can be refreshed by selecting an Episode from the _Preview Episode_
dropdown (below the Series name), or clicking the preview Title Card directly.

The preview will reflect all changes in the Series and Episode __except__
changes to any assigned Templates (due to how these are handled in the
underlying database).

!!! tip "Save your changes"

    Remember that if you make any changes to the Series or Episode Card options,
    you __must__ click <span class="example md-button">Save</span> for these
    changes to become permanent. TCM will not warn you about unsaved changes.

## Tabs

The Series page is organized into several tabs, each containing different types of configuration and data:

### Options Tab

The Options tab contains the basic Series configuration settings.

#### Libraries

Which libraries this Series can be found in on your Media Servers. This setting
is __required__ for a Series' Title Cards to be loaded into the respective
server.

Any number of libraries can be added to a Series. However, if your effective
[Episode Data Source](#episode-data-source) is a Media Server, only the first
library associated with that Connection will be queried for Episode data.

!!! note "Updating Libraries"

    When adding or removing libraries to a Series, the various library-specific
    [actions](#library-actions) can be updated by refreshing the page.

!!! danger "Changing Library Names"

    TitleCardMaker stores a lot of data under the specific library name as it
    appears in your Media Servers. Because of this, changing the names of your
    libraries in your servers is __strongly discouraged__ if it can be avoided.

#### Episode Data Source

Where to get Episode data from. If left unspecified, this will fall back to the
assigned Template(s) or global
[Episode Data Source](./settings.md#episode-data-source) value.

If this is a Media Server, this Series _must_ have at least one
[Library](#libraries) associated with that Connection.

#### Image Source Priority

Order of Connections to try and get images from. This determines which media server TCM will query first when looking for source images, backdrops, and logos.

#### Series Options

Several checkboxes control Series behavior:

- **Match Titles** - Whether to update Episode titles if they differ from the
assigned Episode data source
- **Auto-Split Titles** - Whether to automatically split the title text into
separate lines
- **Use Per-Season Assets** - Whether to utilize manually added backdrops and
logos unique to each season

#### Specials and Localization

- **Enable Specials** - Whether to include Episodes from Season 0 (specials)
- **Ignore Localized Images** - Whether to ignore images with assigned Languages

#### File Management

- **Card Directory** - Directory to store this Series' Title Cards
- **Filename Format** - Format for naming this Series' Title Cards

### Card Configuration Tab

The Card Configuration tab contains all the visual and styling options for Title
Cards.

#### Templates

Templates are evaluated in order and can be used to apply complex styling rules.
Multiple Templates can be assigned to a Series - read more about using Templates
[here](./templates.md).

#### Card Type and Font

- **Card Type** - The visual style/type of Title Card to create
- **Font** - The named Font to use for text on the Title Cards

#### Episode Styles

- **Watched Episode Style** - How watched episodes should appear (Art, Unique, with blur/grayscale effects)
- **Unwatched Episode Style** - How unwatched episodes should appear

#### Font Overrides

Detailed font customization options:

- **Color** - Text color (supports ImageMagick color names)
- **Text Case** - How to pre-process title text
- **Size** - Font size (as a percentage)
- **Kerning** - Character spacing (as a percentage)
- **Stroke Width** - Text outline width (as a percentage)
- **Interline Spacing** - Spacing between separate lines of text
- **Interword Spacing** - Spacing between individual words
- **Vertical Shift** - Vertical positioning adjustment

#### Season and Episode Text

- **Hide Season Titles** - Remove season text (e.g. "Season 1")
- **Season Titles** - Custom titles for specific season ranges. The specific
format of how to enter season titles can be viewed by hovering over the question
icon.
- **Hide Episode Text** - Remove episode text (e.g. "Episode 1")
- **Episode Text Format** - Custom format for episode text

#### Translations and Extras

- **Translations** - Add translations for episode titles in different languages
- **Extras** - Additional custom data fields that can be used in templates

### Blueprints Tab

Blueprints are pre-made Card configurations which can be imported and applied to
a Series. You can read more about these [here](../blueprints.md).

This tab allows you to search for and import any currently available Blueprints
for this Series.

You can begin submitting your own by clicking the **Export** button.

### Episode Data Tab

The Episode Data tab provides a comprehensive table for managing data of and
Cards for individual Eepisodes.

#### Mass Actions

Several buttons allow bulk operations:

- **Refresh** - Refresh Episode Data from the configured data source
- **Add** - Add a new Episode manually
- **Save All Changes** - Save all pending changes to Episodes
- **Delete All** - Delete all Episodes
- **Toggle Advanced Mode** - Show/hide advanced Episode configuration
options - this adjusts the
[global setting](./settings.md#simplified-episode-data-tables).

#### Advanced Mode

When enabled, Advanced Mode shows additional configuration options for each
Episode, allowing for very granular control over individual Episode settings.

You can read more about this setting
[here](./settings.md#simplified-episode-data-tables).

### Files Tab

The Files tab manages all the image files associated with the Series.

#### Title Cards Section

- **Refresh** - Refresh the preview of created Title Cards
- **Upload** - Open a dialog for manually uploading Title Card files
- **MediUX Import** - Import Title Cards from MediUX (or any Kometa-formatted
YAML)

The Title Cards section includes:

- A collapsible image viewer showing all created Title Cards
- Individual Card actions (delete, download, recreate, reload, selective reload)
which can be viewed by clicking the Card image

#### Source Images Section

Source Images are the original images used to create Title Cards.

- **Refresh** - Refresh the list of source images
- **Upload** - Upload Source Images manually

!!! warning "Source Image Naming"

    When uploading Source Images via the upload dialog, TCM __does not__
    perform any renaming or image validation on your behalf.

The Source Images section includes:

- A table showing image details (season, episode, dimensions, file size)
- Action buttons for each image (browse, upload, mirror, download, delete)
- A collapsible image viewer

!!! note "Automatic Download"

    Source Images are downloaded automatically when Title Cards are created, but
    only for monitored Series.

#### Logo Section

Manage the Series logo and per-season logos (if enabled).

- **Browse** - Browse available logos from TMDb
- **Upload** - Upload a logo file
- **Analyze Palette** - Extract color palette from the logo
- **Delete** - Remove the current logo

If "Use Per-Season Assets" is enabled, separate logos can be managed for each
season. This can be toggled on the [Options tab](#options-tab).

#### Backdrop Section

Manage the Series backdrop and per-season backdrops (if enabled).

- **Browse** - Browse available backdrops from TMDb
- **Upload** - Upload a backdrop file
- **Analyze Palette** - Extract color palette from the backdrop

The backdrop is automatically used as the source image for any "Art" styles.

If "Use Per-Season Assets" is enabled, separate backdrops can be managed for
each season.  This can be toggled on the [Options tab](#options-tab).

### External Tab

The External tab manages all the external service IDs associated with the Series.

Depending on your configuration, the following ID fields may be available:

- **Emby ID** - Format: `{Interface ID}:{Library Name}:{ID}`
- **IMDb ID** - Direct IMDb identifier
- **Jellyfin ID** - Format: `{Interface ID}:{Library Name}:{ID}`
- **Sonarr ID** - Format: `{Interface ID}:{ID}`
- **TMDb ID** - The Movie Database identifier
- **TVDb ID** - The TV Database identifier
- **TVRage ID** - For series from before 2017
- **Set URL** - Custom URL for the series - this is currently for convenience
only.

### Logs Tab

The Logs tab displays a chronological feed of all actions and events related to this Series, including:

- Card creation events
- File uploads/downloads
- Configuration changes
- Error messages
- System notifications

The logs are automatically updated and provide detailed information for
troubleshooting and monitoring Series activity. For a more comprehensive look at
your server logs, see the [Logs page](./logs.md).

[^1]: During this, TCM queries the effective [Episode data source](...) for any
_new_ Episodes and adds them to the Series; and updates the titles of all
_existing_ Episodes to match what is currently present in the Episode data
source __if__ [title matching](...) is enabled.

[^2]: During this, TCM will __not__ replace any existing images, nor will it
download any backdrops or logos. TCM will search for images in the order
specified in your global
[image source priority](./settings.md#image-source-priority). If the Series does
not have any libraries assigned for a given media server Connection (e.g. a Plex
Connection being in your source priority, but this Series having no Plex
library) then it will be skipped.