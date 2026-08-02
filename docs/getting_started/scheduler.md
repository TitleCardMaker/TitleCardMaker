---
title: The Scheduler
description: >
    The basics of the schedulable Tasks which perform the primary duties of
    TitleCardMaker.
tags:
    - Tutorial
    - Scheduler
---

# Rescheduling Tasks

TitleCardMaker runs all core tasks on schedulable intervals using
[cron](https://crontab.guru/) expressions. The default schedules are typically
sufficient for most use-cases, but TCM allows these to be adjusted.

For this part of the tutorial, we'll adjust how often all Syncs are run.

1. Navigate to the Scheduler page by clicking Settings, then
:fontawesome-solid-stopwatch: `Scheduler` from the side navigation bar.

    ![Basic Scheduler Page](../user_guide/assets/scheduler_basic-light.webp#only-light){.no-lightbox}
    ![Basic Scheduler Page](../user_guide/assets/scheduler_basic-dark.webp#only-dark){.no-lightbox}

2. Find the task description that reads "Sync and add any new Series".

3. In the "Schedule" column, replace the existing cron expression with
`0 */4 * * *` (every 4 hours, on the hour).

    The next column shows a live human-readable description of the expression
    so you can confirm it matches what you intended.

    ??? tip "Cron help"

        [crontab.guru](https://crontab.guru/) is linked on the Scheduler page
        and is a helpful resource for building expressions.

4. Click the <span class="example md-button">Save Changes</span> button.

5. Restart TitleCardMaker if you want these changes to take effect. For the
purposes of Getting Started this is not strictly necessary, but is required for
any "real" changes.

!!! success "Success"

    You have now successfully changed the schedule for a Task within TCM. This
    exact procedure can be followed to change _any_ Task schedule. See the
    [User Guide](../user_guide/scheduler.md) for details on each Task and
    Basic vs Advanced mode.
