---
title: Syncing from Emby
description: >
    Creating a Sync to automatically add Series from Emby to TitleCardMaker.
tags:
    - Tutorial
    - Emby
    - Sync
---

# Syncing from Emby

!!! note "Example Series"

    This tutorial uses _Breaking Bad_. If you do not have it in your Emby
    server, add it temporarily (or pick a different Series) and apply the same
    steps.

For the purposes of this tutorial, we will Sync a subset of your Series by
using a filter tag within Emby.

1. Open Emby.

2. Open _Breaking Bad_, click the "more data" :material-dots-horizontal: button,
then click `Edit Metadata` for the Series.

3. At the very bottom click the `+` button next to Tags, type `tcm-test` and hit
++enter++ - click `Save`.

4. Back within TitleCardMaker, navigate to the Sync page by clicking
:fontawesome-solid-arrows-rotate: `Sync` from the side navigation bar.

5. Under the Emby section of the page, click the
<span class="example md-button">+ Add Sync</span> button.

6. In the launched dialog, fill out the following information:

    1. Enter the Sync Name as `Test Sync`
    2. In the "Templates to Apply", select the `Tinted Frame` Template from
    [earlier](../creating_templates.md) in the tutorial.

        !!! tip "Template Order Matters"

            When adding multiple Templates, the order in which they are listed
            is critical. TCM will apply the first Template whose Filter
            conditions are all satisfied.

    3. Under the Filters section, enter the tag `tcm-test` and hit ++enter++.
    4. Hit the `Create` button.

    !!! success "Sync Created"

        You have successfully created a Sync that automatically adds all Series
        in Emby that are tagged with `tcm-test`, and assigns our Template to
        them.

7. At the top of the page is an indication of when all your Syncs will next
run. To run a Sync immediately, click the small
:fontawesome-solid-arrows-rotate: Sync icon.

8. TCM will then query Emby for all your Series, filter the results by our
indicated filters (in our case the `tcm-test` tag), and then filter out any
exclusions (none). The added Series will be listed in a message. You should
see "Synced 1 Series", with _Breaking Bad_ listed below.

!!! success "Synced from Emby"

    You have successfully Synced from Emby. This exact structure can be used
    to create and run any number of Syncs. Next, continue to
    [Creating Title Cards](../creating_cards.md).
