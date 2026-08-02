---
title: Global Settings
description: >
    Recommended global settings for new users.
tags:
    - Tutorial
    - Global Settings
---

# Settings

Most default Settings can be left as-is. Two settings __must__ be set before
TitleCardMaker can gather Episode data and Source Images automatically:
_Episode Data Source_ and _Image Source Priority_.

![Settings Page](../user_guide/assets/settings-light.webp#only-light){.no-lightbox}
![Settings Page](../user_guide/assets/settings-dark.webp#only-dark){.no-lightbox}

1. Navigate to the Settings page by clicking `Settings`, then
:fontawesome-solid-gear: `Settings` from the side navigation bar (or open the
`/settings` URL).

2. Set __Episode Data Source__ to match a Connection you enabled. Prefer
__Sonarr__ if you connected it; otherwise use your media server (Plex,
Jellyfin, or Emby), or TMDb.

3. Set __Image Source Priority__ so TMDb is first, followed by your media
server(s). For example: `TMDb`, then `Plex` (or Emby / Jellyfin).

    ??? tip "Why TMDb first?"

        TMDb usually has a wider variety of higher-quality images than
        auto-scraped media server artwork. Your media server remains a useful
        fallback.

4. Optionally open the __Default Card Type__ dropdown and pick a style you like.
The most popular choices are Tinted Frame and Standard. For this tutorial we
will override the card type with a Template in the next steps, so this choice
is not critical yet.

5. Click <span class="example md-button">Save</span>.

For a full table of recommended values and details on every setting, see the
[User Guide](../user_guide/settings.md#recommended-settings).
