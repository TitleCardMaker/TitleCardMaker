from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from huey import crontab
from sqlalchemy.orm import Session

from app.core.schedule import TaskID, get_task_details, RecurringTasks
from app.db.users import get_current_user
from app.dependencies import get_database, get_logger, get_preferences
from app.logging.logger import Logger
from app.schemas.schedule import TaskDetails
from modules.preferences import Preferences


# Create sub router for all /scheduler API requests
scheduler_router = APIRouter(
    prefix='/scheduler',
    tags=['Scheduler'],
    dependencies=[Depends(get_current_user)],
)


@scheduler_router.post('/type/toggle')
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


@scheduler_router.put('/type/{mode}')
def set_the_scheduler_type(
        mode: Literal['advanced', 'basic'],
        log: Logger = Depends(get_logger),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Set the scheduler to the given mode.
    
    - mode: Which mode to set.
    """

    # Toggle scheduling method
    if mode == 'advanced':
        log.info('Enabling advanced Task scheduling')
    else:
        log.info('Disabling advanced Task scheduling')
    preferences.advanced_scheduling = mode == 'advanced'
    preferences.commit()


@scheduler_router.get('/scheduled')
def get_scheduled_tasks(
        show_internal: bool = Query(default=False),
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> list[TaskDetails]:
    """
    Get scheduling details for all defined Tasks.

    - show_internal: Whether to show internal tasks.
    """

    return [
        get_task_details(db, task_id)
        for task_id in RecurringTasks
        if (
            show_internal or preferences.advanced_scheduling
            or not RecurringTasks[task_id].internal
        )
    ]


@scheduler_router.get('/{task_id}', deprecated=True)
def get_scheduled_task_deprecated(
        task_id: TaskID,
        db: Session = Depends(get_database),
    ) -> TaskDetails:
    """
    Get the schedule details for the indicated Task.

    - task_id: ID of the Task to get the details of.
    """

    if task_id not in RecurringTasks:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    return get_task_details(db, task_id)


@scheduler_router.get('/task/{task_id}')
def get_scheduled_task(
        task_id: TaskID,
        db: Session = Depends(get_database),
    ) -> TaskDetails:
    """
    Get the schedule details for the indicated Task.

    - task_id: ID of the Task to get the details of.
    """

    if task_id not in RecurringTasks:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    return get_task_details(db, task_id)


@scheduler_router.put('/update/{task_id}', deprecated=True)
def reschedule_task_deprecated(
        task_id: TaskID,
        update_crontab: str = Query(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
        preferences: Preferences = Depends(get_preferences),
    ) -> TaskDetails:
    """
    Reschedule the given Task with a new interval.

    - task_id: ID of the Task being rescheduled.
    - update_crontab: New crontab schedule to reschedule this Task with.
    """

    # Verify job exists, raise 404 if DNE
    if task_id not in RecurringTasks:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    # Verify schedule is valid
    try:
        crontab(update_crontab)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail='Invalid cron schedule',
        ) from exc

    # Reschedule with modified interval
    log.info(f'Task[{task_id}] rescheduling to "{update_crontab}"')
    preferences.task_schedules[task_id] = update_crontab
    preferences.commit()

    return get_task_details(db, task_id)


@scheduler_router.patch('/task/{task_id}')
def reschedule_task(
        task_id: TaskID,
        update_crontab: str = Query(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
        preferences: Preferences = Depends(get_preferences),
    ) -> TaskDetails:
    """
    Reschedule the given Task with a new interval.

    - task_id: ID of the Task being rescheduled.
    - update_crontab: New crontab schedule to reschedule this Task with.
    """

    # Verify job exists, raise 404 if DNE
    if task_id not in RecurringTasks:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    # Verify schedule is valid
    try:
        crontab(update_crontab)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail='Invalid cron schedule',
        ) from exc

    # Reschedule with modified interval
    log.info(f'Task[{task_id}] rescheduling to "{update_crontab}"')
    preferences.task_schedules[task_id] = update_crontab
    preferences.commit()

    return get_task_details(db, task_id)


@scheduler_router.put('/{task_id}', deprecated=True)
def run_task_deprecated(
        task_id: TaskID,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> TaskDetails:
    """
    Run the given Task immediately. This __does not__ reschedule or
    modify the Task's next scheduled run.

    - task_id: ID of the Task to run.
    """

    # Verify Task exists, raise 404 if DNE
    if task_id not in RecurringTasks:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    try:
        RecurringTasks[task_id].wrapped_func(log=log)
    except Exception as e:
        log.error(f'Failed to run Task {task_id}: {e}')

    # Return updated task info
    return get_task_details(db, task_id)


@scheduler_router.put('/task/{task_id}')
def run_task(
        task_id: TaskID,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> TaskDetails:
    """
    Run the given Task immediately. This __does not__ reschedule or
    modify the Task's next scheduled run.

    - task_id: ID of the Task to run.
    """

    # Verify Task exists, raise 404 if DNE
    if task_id not in RecurringTasks:
        raise HTTPException(
            status_code=404,
            detail=f'Task {task_id} not found',
        )

    try:
        RecurringTasks[task_id].wrapped_func(log=log)
    except Exception as e:
        log.error(f'Failed to run Task {task_id}: {e}')

    # Return updated task info
    return get_task_details(db, task_id)
