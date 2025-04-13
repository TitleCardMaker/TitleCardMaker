---
title: Missing Summary
description: >
    Summary of all missing Title Cards and Logos.
---

# Missing Summary

The Missing page displays Episodes that are missing Title Cards, and Series
which are missing Logos. The purpose of this is to identify which Episodes which
are missing assets - such as Source Images, logos, etc. This page can be
accessed from the sidebar under `Series`, as well as at the `/missing` URL.

![Missing Page](./assets/missing-light.webp#only-light){.no-lightbox}
![Missing Page](./assets/missing-dark.webp#only-dark){.no-lightbox}

Episodes are grouped by Series and sorted by episode order. Each entry shows:

- The Series the Episode belongs to;
- The Episode's season and episode number; and
- The Episode's title

While the logo table just displays the series and the missing logo filename.

## Possible Causes

The most common reasons for an Episode to be missing a Title Card are:

- The Episode was recently added to TCM and your [Create Title
Cards](./scheduler.md#create-title-cards) Task has not run; or
- There are no Source Images available - this is typically because the Episode
is too new (and none are available on TMDb), or none which meet your [Resolution
Criteria](./connections.md#minimum-image-resolution)

## Potential Solutions

Clicking the Series within the table and then clicking the `Create Title Cards`
button will prompt TCM to attempt to create and missing Title Cards. If they
are still missing, the next step is typically look in your [Logs](./logs.md) for
messages like `Unable to create Title Card for ...`.
