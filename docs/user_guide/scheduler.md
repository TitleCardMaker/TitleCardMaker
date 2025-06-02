---
title: The Scheduler
description: >
    The schedulable Tasks which automatically perform all major operations.
---

# The Scheduler

TitleCardMaker runs all core tasks on schedulable intervals. These can be
adjusted by accessing the Scheduler page under `Settings` > `Scheduler` (or at
the `/scheduler` URL).

The Scheduler can be in one of two modes: basic (the default) mode, and advanced
mode. These two modes can be switched between at any point by clicking the green
button at the bottom of the page. All intervals are reset when switching from
basic to advanced mode.

!!! tip "Minimum Task Frequency"

    In both modes, the fastest a single Task can be scheduled is once every 10
    minutes.
    
    TCM will also not start a Task while it is already running, so if a given
    Task takes longer than its assigned frequency, the second run will be
    skipped.

## Modes

### Basic Mode

While in basic mode, all scheduled Tasks happen on fixed intervals. These
intervals are relative to whenever you first launch TCM (i.e. they are not
guaranteed to start at the top of the hour). In addition to this, only a subset
of the total available Tasks (the most commonly adjusted ones) are displayed.

![](../assets/scheduler_basic_light.webp#only-light){.no-lightbox}
![](../assets/scheduler_basic_dark.webp#only-dark){.no-lightbox}

How often these Tasks occur can be changed by editing the text in the
_Frequency_ column of the table. This information can be entered as text, and
any combination of "seconds", "minutes", "hours", "days", and "weeks" are
supported. 

!!! example "Example Frequency"

    A frequency string can be as simple as `4 hours`, or as complex as
    `1 day 4 hours 12 minutes 23 seconds`. 

### Advanced Mode

In advanced mode, scheduled Tasks happen according to a "cron" expression. These
are expressions which allow for succinctly describing when something can occur,
and can be as simple as `*/30 * * * *` - meaning "every 30 minutes" - to as
complex as `0 2 * * 1-5` - meaning "at 02:00 AM, Monday through Friday".

Advanced mode also make all Tasks available to be rescheduled.

![](../assets/scheduler_advanced_light.webp#only-light){.no-lightbox}
![](../assets/scheduler_advanced_dark.webp#only-dark){.no-lightbox}

When Tasks run can be adjusted by editing the cron expression in the _Schedule_
column of the table. A live human-readable description of the expression is
given in the next column. There are many online resources to creating cron
expressions, but a [helpful resource](https://crontab.guru/) is linked at the
bottom of the page.

## Tasks

Below is a table which provides a bit more detail on each Task defined in The
Scheduler.

| Task Description                           | Advanced Only                              | Recommended Interval | Details                        |
| :----------------------------------------: | :----------------------------------------: | :------------------: | :----------------------------: |
| Backup the database and global settings    | :fontawesome-regular-circle-xmark:{.red}   | Once a day           | [Details](#database-backup)    |
| Check for a new release of TitleCardMaker  | :fontawesome-regular-circle-check:{.green} | Once a week[^1]      | [Details](#new-release)        |
| Create all missing or outdated Title Cards | :fontawesome-regular-circle-xmark:{.red}   | Once a day[^2][^3]   | [Details](#create-title-cards) |
| Clean the database                         | :fontawesome-regular-circle-check:{.green} | Once a week          | [Details](#clean-database)     |
| Download logos for all Series              | :fontawesome-regular-circle-xmark:{.red}   | Twice a week         | [Details](#download-logos)     |
| Download posters for all Series            | :fontawesome-regular-circle-xmark:{.red}   | Twice a week         | [Details](#download-posters)   |
| Load all Title Cards into media servers    | :fontawesome-regular-circle-xmark:{.red}   | Once a day[^2]       | [Details](#load-title-cards)   |
| Refresh all non-built-in card types        | :fontawesome-regular-circle-check:{.green} | Once a week          | [Details](#refresh-card-types) |
| Set Series IDs                             | :fontawesome-regular-circle-check:{.green} | Once a week          | [Details](#set-series-ids)     |
| Sync and add any new Series                | :fontawesome-regular-circle-xmark:{.red}   | Once a day           | [Details](#sync-series)        |
| Take a database snapshot                   | :fontawesome-regular-circle-check:{.green} | Every few hours      | [Details](#database-snapshot)  |

### Database Backup

Perform a backup of the system database and settings. This __does not__ backup
any image files, and so cannot be used to truly restore TCM from a data failure.

These backups are stored in `config/backups`.

### New Release

Check GitHub for a new version of TCM. This does not affect those on the
`develop` branch.

### Create Title Cards

Perform all the individual steps required to create Title Cards. This actually
does the following, in order:

1. Refresh Episode data - i.e. look for new Episodes (if the Series is monitored)
2. Update the watched status of all Episodes
3. Add Episode translations (if the Series is monitored)
4. Download Source Images (if the Series is monitored)
5. Create or update all Title Cards

It is important to note that Title Card _loading_ is performed in a separate
[Task](#load-title-cards).

### Clean Database

Remove any "outdated" data/objects from the database. Specifically, this does
the following:

1. Remove the loaded records for any outdated Cards
2. Delete Card records (and files) which are not associated to with a Series or
Episode
3. Delete Episodes which do not have an associated Series
4. Delete duplicate Episodes - i.e. Episodes of the same Series which have the
same season and episode number.
5. Delete duplicate Cards (if [Multi-Library File
Naming](./settings.md#multi-library-file-naming) mode is disabled)

### Download Logos

Attempt to download any missing Series logos. This does not attempt to
download season logos if a Series has per-season assets enabled.

### Download Posters

Attempt to download any missing Series posters. TCM prioritizes posters from
media servers (i.e. Plex, Sonarr, etc.) over those from "generic" sources like
TMDb, or TVDb.

### Load Title Cards

Load Title Cards into all media servers for Series which have assigned
libraries.

This will not "reload" Cards which have disappeared from the server if they were
removed in a way which TCM cannot detect - for example selecting a different
image manually in Plex, or if the Episode metadata was reset (typically from a
file upgrade). In order to do this, you need to select the 'force reload' option
for the Series/Card.

### Refresh Card Types

Pull updated card type data from
[GitHub](https://github.com/CollinHeist/TitleCardMaker-CardTypes) and re-parse
any [local](../card_types/local.md) card files.

### Set Series IDs

Look for database IDs (e.g. TMDb, TVDb, Sonarr, etc.) for all Series. This is
done to aid in matching content across all Connections.

### Sync Series

Run all defined [Syncs](./syncs.md) and add any new Series to TCM. Once a new
Series is added, database IDs are queried, posters and logos are downloaded, and
Episode data is refreshed. It is important to note that Title Cards __are not__
created until the [Create Title Cards](#create-title-cards) Task is run - this
is so you have time to edit the Series as desired.

This also adds any undefined libraries to the Series; such as those defined in
the Sonarr [Library Path](./connections.md#library-paths) setting. It __does
not__ remove invalid libraries from those Series.

If the global [Delete Unsynced Series](./settings.md#delete-un-synced-series)
setting is enabled, any Series which was not found on any defined Syncs will
be deleted (including any associated Title Cards).

### Database Snapshot

Take a "snapshot" of the database. This is a count of all Series, Episodes,
Fonts, etc., as well as a file size summation for all Cards. These snapshots
can be graphically displayed on the [Graphs](../graphs.md) page, but serve no
_functional_ purpose within TCM.

[^1]: This Task does nothing while the UI is only available to sponsors.
[^2]:
    If you are not using any of the "fast" [integrations](./integrations.md) -
    such as the Tautulli or Plex Webhook - then it might be benefitical to run
    this twice a day.
[^3]:
    For those with very large (or small) servers, I recommend having this Task
    run ~1/10th the time. So if you see this Task _typically_ takes about 2
    hours, try and run it roughly every 20 hours; if it only takes 20 minutes
    then you can increase the frequency to about every 200 minutes (~3-4 hours).
