---
title: Missing Summary
description: >
    Summary of missing Title Cards, missing Logos, and unloaded Title Cards.
---

# Missing Summary

The Missing page helps you find gaps in your TitleCardMaker library — Episodes
without Title Cards, Series without Logos, and Title Cards that have not yet
been loaded to your media server. Access it from the sidebar via the `Missing`
item, or at the `/missing` URL.

![Missing Page](./assets/missing-light.webp#only-light){.no-lightbox}
![Missing Page](./assets/missing-dark.webp#only-dark){.no-lightbox}

The page is split into three panels. Each panel header shows a count badge when
there are results to review.

## Missing Title Cards

This panel lists Episodes that do not have an associated Title Card. Results
are grouped by Series and sorted by episode order within each Series.

Each Series row shows:

- The Series poster;
- The Series name;
- A badge with how many Episodes are missing Cards; and
- An expand button to show or hide the Episode list.

Expand a row to see each missing Episode as a pill with its season/episode code
(for example, `S01E03`) and title.

Click a Series row (outside the expand button) to open that Series' page on the
**Files** tab. Use the refresh button (↻) to reload the list.

## Missing Logos

This panel lists Series that do not have a `logo.png` file in their Source
folder. Each entry shows the Series poster and name.

Click a Series to open its Series page on the **Files** tab, where you can
upload or manage logo files.

## Unloaded Cards

!!! tip "Unloaded Card Mismatch"

    You _may_ encounter situations where TCM is reporting a Card as unloaded,
    but you see that Card in your server (and TCM seemingly does not 'reload'
    it). This is often because TCM may have recreated the Card (for various
    reasons), but has detected that it does not need to reload it into your
    server.

    If you would like to remove these from the list of unloaded cards on this
    page, the best solution is to perform a
    [Force Reload](./series.md#library-actions) on the Series page.

This panel lists Title Cards that exist in TitleCardMaker but have not been
loaded to your media server yet. Results are grouped by Series.

Each Series row shows:

- The Series poster;
- The Series name;
- A badge with how many Cards are unloaded;
- A **Load** button to load all unloaded Cards for that Series into its
  assigned library; and
- An expand button to preview the unloaded Cards.

Expand a row to see thumbnails of each unloaded Card with its season/episode
code.

Click a Series row (outside the buttons) to open that Series' page on the
**Files** tab. Use the refresh button (↻) to reload the list.

Unloaded Cards are also loaded automatically by the [Load Title
Cards](./scheduler.md#load-title-cards) scheduled Task, or manually from a
Series' library actions dropdown — see [Title Card
Loading](./series.md#title-card-loading) on the Series page.

## Pagination and Page Size

The **Missing Title Cards** and **Unloaded Cards** panels paginate their
results. By default, each shows **100** items per page. Use the **50**, **100**,
or **200** buttons in the panel header to change how many Episodes or Cards are
loaded at once.

Pagination controls appear below the list when there is more than one page.
The **Missing Logos** panel loads all results at once and has no pagination.

## Possible Causes

The most common reasons for an Episode to be missing a Title Card are:

- The Episode was recently added to TCM and your [Create Title
  Cards](./scheduler.md#create-title-cards) Task has not run; or
- There are no Source Images available — this is typically because the Episode
  is too new (and none are available on TMDb), or none which meet your
  [Resolution Criteria](./connections.md#minimum-image-resolution)

Title Cards may remain unloaded if their Series has no assigned library, the
[Load Title Cards](./scheduler.md#load-title-cards) Task has not run since they
were created, or a previous load attempt failed.

## Potential Solutions

Open a Series from any panel (rows link to the **Files** tab) and click
**Create Title Cards** to prompt TCM to create missing Cards. For unloaded
Cards, use the **Load** button on that Series row, or load them from the
Series page library actions dropdown.

If Title Cards are still missing after creation, check your [Logs](./logs.md)
for messages like `Unable to create Title Card for ...`.
