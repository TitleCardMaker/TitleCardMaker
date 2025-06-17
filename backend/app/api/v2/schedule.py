from typing import Literal

from apscheduler.job import Job
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Body, Depends, HTTPException, Query

from app.core.schedule import BaseJobs, TaskID, initialize_scheduler
from app.dependencies import (
    get_logger,
    get_preferences,
    get_scheduler,
)
from app.db.users import get_current_user
from app.schemas.schedule import (
    Minutes,
    ScheduledTask,
    UpdateSchedule
)
from app.logging.logger import Logger
from modules.preferences import Preferences

# Do not allow tasks to be scheduled faster than this interval
MINIMUM_TASK_INTERVAL = Minutes(10)


# Create sub router for all /schedule API requests
schedule_router = APIRouter(
    prefix='/schedule',
    tags=['Scheduler'],
    dependencies=[Depends(get_current_user)],
)


def _scheduled_task_from_job(job: Job,) -> ScheduledTask:
    """
    Create a ScheduledTask object for the given apscheduler.job.

    Args:
        job: APScheduler Job object to create a ScheduledTask of.

    Returns:
        ScheduledTask describing the given Job.
    """

    # Calculate previous Task duration if possible
    base_job = BaseJobs.get(job.id)
    previous_duration = None
    if (base_job.previous_start_time is not None
        and base_job.previous_end_time is not None):
        previous_duration = \
            base_job.previous_end_time - base_job.previous_start_time

    # Get the frequency string or crontab
    frequency, crontab = None, None
    if (preferences := get_preferences()).advanced_scheduling:
        crontab = preferences.task_crontabs.get(job.id, base_job.crontab)
    else:
        try:
            frequency = job.trigger.interval.total_seconds()
        except AttributeError:
            # Using basic scheduling, but job was created in advanced mode
            crontab = preferences.task_crontabs.get(job.id, base_job.crontab)

    return ScheduledTask(
        id=str(job.id),
        frequency=frequency,
        crontab=crontab,
        next_run=str(job.next_run_time),
        description=base_job.description,
        previous_duration=previous_duration,
        running=base_job.running,
    )


@schedule_router.post('/type/toggle')
def toggle_schedule_type(
        log: Logger = Depends(get_logger),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Toggle the global scheduling between basic and advanced. Basic
    scheduling mode using standard intervals, while advanced scheduling
    uses Cron schedule expressions.
    """

    # Toggle scheduling method
    if preferences.advanced_scheduling:
        log.info('Disabling advanced Task scheduling')
    else:
        log.info('Enabling advanced Task scheduling')
    preferences.advanced_scheduling = not preferences.advanced_scheduling
    preferences.commit()

    # Reset Scheduler
    initialize_scheduler(override=True, log=log)


@schedule_router.put('/type/{mode}')
def set_the_scheduler_type(
        mode: Literal['advanced', 'basic'],
        log: Logger = Depends(get_logger),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Set the scheduler mode to the given mode.
    
    - mode: Which mode to set.
    """

    # Toggle scheduling method
    if mode == 'advanced':
        log.info('Enabling advanced Task scheduling')
    else:
        log.info('Disabling advanced Task scheduling')
    preferences.advanced_scheduling = mode == 'advanced'
    preferences.commit()

    # Reset Scheduler
    initialize_scheduler(override=True, log=log)


@schedule_router.get('/scheduled')
def get_scheduled_tasks(
        show_internal: bool = Query(default=False),
        preferences: Preferences = Depends(get_preferences),
        scheduler: BackgroundScheduler = Depends(get_scheduler),
    ) -> list[ScheduledTask]:
    """
    Get scheduling details for all defined Tasks.

    - show_internal: Whether to show internal tasks.
    """

    show_internal |= preferences.advanced_scheduling

    return [
        _scheduled_task_from_job(job)
        for job in scheduler.get_jobs()
        if job.id in BaseJobs and (show_internal or not BaseJobs[job.id].internal)
    ]


@schedule_router.get('/{task_id}')
def get_scheduled_task(
        task_id: TaskID,
        scheduler: BackgroundScheduler = Depends(get_scheduler),
    ) -> ScheduledTask:
    """
    Get the schedule details for the indicated Task.

    - task_id: ID of the Task to get the details of.
    """

    if (job := scheduler.get_job(task_id)) is None:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    return _scheduled_task_from_job(job)


@schedule_router.put('/update/{task_id}')
def reschedule_task(
        task_id: TaskID,
        update_schedule: UpdateSchedule = Body(...),
        log: Logger = Depends(get_logger),
        preferences: Preferences = Depends(get_preferences),
        scheduler: BackgroundScheduler = Depends(get_scheduler),
    ) -> ScheduledTask:
    """
    Reschedule the given Task with a new interval.

    - task_id: ID of the Task being rescheduled.
    - update_schedule: New interval/schedule to reschedule this Task.
    """

    # Verify job exists, raise 404 if DNE
    if (job := scheduler.get_job(task_id)) is None:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    # Advanced scheduling
    if preferences.advanced_scheduling:
        # Interval unchanged skip
        if update_schedule.crontab == preferences.task_crontabs[task_id]:
            log.debug(f'Task[{job.id}] Not rescheduling, interval unchanged')
            return _scheduled_task_from_job(job)

        # Verify schedule is valid
        try:
            new_trigger = CronTrigger.from_crontab(update_schedule.crontab)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=f'Invalid Cron schedule',
            ) from exc

        # Reschedule with modified interval
        log.info(f'Task[{job.id}] rescheduling to "{update_schedule.crontab}"')
        BaseJobs[task_id].crontab = update_schedule.crontab
        job = scheduler.reschedule_job(task_id, trigger=new_trigger)

        # Write are updated crontab to preferences, commit
        preferences.task_crontabs[task_id] = update_schedule.crontab
        preferences.commit()
    # Basic scheduling
    else:
        # If new interval is the same as old interval, skip
        new_interval = (
            update_schedule.seconds
            + (update_schedule.minutes * 60)
            + (update_schedule.hours * 60 * 60)
            + (update_schedule.days * 60 * 60 * 24)
            + (update_schedule.weeks * 60 * 60 * 24 * 7)
        )
        if new_interval == job.trigger.interval.total_seconds():
            log.debug(f'Task[{job.id}] Not rescheduling, interval unchanged')
            return _scheduled_task_from_job(job)

        # Ensure interval is not below minimum
        if new_interval < MINIMUM_TASK_INTERVAL:
            log.warning(
                f'Task[{job.id}] Cannot schedule Task more frequently than '
                f'{MINIMUM_TASK_INTERVAL} seconds'
            )
            update_schedule.seconds = 0
            update_schedule.minutes = 10

        # Reschedule with modified interval
        update_dict = update_schedule.dict()
        update_dict.pop('crontab', None) # Remove crontab arg
        log.debug(f'Task[{job.id}] rescheduled via {update_dict}')
        job = scheduler.reschedule_job(
            task_id,
            trigger='interval',
            **update_dict,
        )

    return _scheduled_task_from_job(job)


@schedule_router.put('/{task_id}')
def run_task(
        task_id: TaskID,
        scheduler: BackgroundScheduler = Depends(get_scheduler),
        log: Logger = Depends(get_logger),
    ) -> ScheduledTask:
    """
    Run the given Task immediately. This __does not__ reschedule or
    modify the Task's next scheduled run.

    - task_id: ID of the Task to run.
    """

    # Verify Task exists, raise 404 if DNE
    if (job := BaseJobs.get(task_id, None)) is None:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    # Run this Task's function
    job.function(log)

    return _scheduled_task_from_job(scheduler.get_job(task_id))
