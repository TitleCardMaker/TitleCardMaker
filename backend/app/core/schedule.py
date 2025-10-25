from datetime import datetime, timedelta
from functools import wraps
from typing import Annotated, Callable, Literal

from croniter import croniter
from huey import crontab, SqliteHuey
from sqlalchemy.orm import Session

from app.core.availability import get_latest_version
from app.core.backup import backup_data
from app.core.cards import (
    clean_database,
    create_all_title_cards,
    refresh_all_card_types,
)
from app.core.logs import clear_log_data
from app.core.series import (
    download_all_series_posters,
    load_all_media_servers,
    set_all_series_ids
)
from app.core.sources import download_all_series_logos
from app.core.snapshot import add_task_duration, snapshot_database
from app.core.sync import sync_all
from app.dependencies import get_database
from app.logging.logger import Logger, contextualize
from app.models.duration import TaskDuration
from app.schemas.schedule import TaskDetails
from app.settings import CONFIG_ROOT, settings


"""How long a Task can be queued before it is removed."""
TASK_EXPIRATION_TIME = timedelta(minutes=10)

# Initialize Huey with SQLite backend
huey = SqliteHuey(filename=CONFIG_ROOT / 'huey.db')

# Job ID's for scheduled tasks
JOB_CREATE_TITLE_CARDS = 'CreateTitleCards'
JOB_DOWNLOAD_SERIES_LOGOS = 'DownloadSeriesLogos'
JOB_DOWNLOAD_SERIES_POSTERS = 'DownloadSeriesPosters'
JOB_LOAD_MEDIA_SERVERS = 'LoadMediaServers'
JOB_SYNC_INTERFACES = 'SyncInterfaces'
JOB_BACKUP_DATABASE = 'BackupDatabase'
# Internal Job ID's
INTERNAL_JOB_CHECK_FOR_NEW_RELEASE = 'CheckForNewRelease'
INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES = 'RefreshRemoteCardTypes'
INTERNAL_JOB_SET_SERIES_IDS = 'SetSeriesIDs'
INTERNAL_JOB_CLEAN_DATABASE = 'CleanDatabase'
INTERNAL_JOB_CLEAR_OLD_LOGS = 'ClearOldLogs'
INTERNAL_JOB_SNAPSHOT_DATABASE = 'SnapshotDatabase'

type TaskID = Literal[
    'CreateTitleCards',
    'SyncInterfaces',
    'LoadMediaServers',
    'DownloadSeriesLogos',
    'DownloadSeriesPosters',
    'BackupDatabase',
    # Internal jobs
    'CheckForNewRelease',
    'RefreshRemoteCardTypes',
    'SetSeriesIDs',
    'CleanDatabase',
    'ClearOldLogs',
    'SnapshotDatabase',
] # type: ignore

_task_running_state: Annotated[
    dict[TaskID, bool],
    'Global state to track running tasks. This only stores non-Huey Tasks.',
] = {}


def get_previous_run_details(
        db: Session,
        task_id: TaskID,
        /,
    ) -> tuple[datetime, datetime, float] | None:
    """
    Get the previous run details for the given Task.

    Args:
        db: Database session.
        task_id: ID of the task to get the previous run details for.

    Returns:
        Tuple containing the start time, end time, and duration of the
        previous run. None if there is no previous run to get the
        details of.
    """

    last_duration = (
        db.query(TaskDuration)
            .filter(TaskDuration.task_name == task_id)
            .order_by(TaskDuration.start_time.desc())
            .first()
    )
    if not last_duration:
        return None

    return (
        last_duration.start_time,
        last_duration.end_time,
        last_duration.duration,
    )


def is_task_running(task_id: TaskID, /) -> bool:
    """
    Check if the given Task is currently running. This checks both the
    current Huey Task queue and the global state of running tasks.

    Args:
        task_id: ID of the task to check if it is running.

    Returns:
        Whether the given Task is currently running.
    """

    return huey.is_locked(task_id) or _task_running_state.get(task_id, False)


class RecurringTask:
    """
    A class that combines the creation of wrapped core Task functions
    and huey Tasks.

    This class handles:
    1. Creating a wrapped version of the Task function with logging and
    error handling.
    2. Creating the huey periodic Task with proper scheduling and
    locking.
    3. Storing all the Task metadata.
    """

    task_func: Callable[[Logger | None], None]
    description: str
    task_id: TaskID
    default_cronstr: str
    cron: crontab
    error_message: str
    priority: int
    expires: timedelta
    internal: bool
    wrapped_func: Callable[[Logger | None], None]
    huey_task: Callable[[], None]


    def __init__(self,
        task_func: Callable[[Logger | None], None],
        description: str,
        task_id: TaskID,
        default_cronstr: str,
        error_message: str,
        priority: int = 0,
        expires: timedelta = timedelta(hours=4),
        internal: bool = False,
    ) -> None:
        """
        Initialize a recurring task.

        Args:
            task_func: The original task function that takes a logger
            description: Human-readable description of the task
            task_id: Unique identifier for the task.
            default_cronstr: Default crontab string.
            error_message: Error message to log if task fails.
            priority: Task priority.
            expires: How long the task can be queued before expiration.
            internal: Whether the task is internal.
        """

        self.task_func = task_func
        self.description = description
        self.task_id = task_id
        self.default_cronstr = default_cronstr
        self.cron = crontab(
            *settings.task_schedules.get(task_id, default_cronstr).split()
        )
        self.error_message = error_message
        self.priority = priority
        self.expires = expires
        self.internal = internal

        # Create the wrapped function with logging and error handling
        self.wrapped_func = self._create_wrapped_function()

        # Create the huey task with scheduling and locking
        self.huey_task = self._create_huey_task()


    def _create_wrapped_function(self) -> Callable[[Logger | None], None]:
        """
        Create a wrapped version of the Task function with logging and
        error handling.
        """

        @wraps(self.task_func)
        def wrapper(log: Logger | None = None) -> None:
            # Get/generate contextualized logger, log task start
            log_: Logger = log or contextualize()
            log_.info(f'Task[{self.task_id}] started execution')

            # Exit if the task is already running
            if _task_running_state.get(self.task_id, False):
                log_.info(
                    f'Task[{self.task_id}] finished execution - Task is already '
                    f'running'
                )
                return None

            # Mark task as running, log start time
            start_time = datetime.now(tz=settings.config.TIMEZONE)
            _task_running_state[self.task_id] = True

            # Run wrapped task
            try:
                self.task_func(log=log_)
            # Any high-level exceptions should be caught
            except Exception:
                log_.exception(self.error_message)

            # Log task finishing
            log_.info(f'Task[{self.task_id}] finished execution')
            end_time = datetime.now(tz=settings.config.TIMEZONE)
            _task_running_state[self.task_id] = False

            # Attempt to add TaskDuration record to database
            try:
                with next(get_database()) as db:
                    add_task_duration(db, self.task_id, start_time, end_time)
            except Exception:
                pass

            return None

        return wrapper


    def _create_huey_task(self) -> Callable[[], None]:
        """Create the huey periodic task with scheduling and locking."""

        return huey.periodic_task(
            self.cron,
            name=self.task_id,
            priority=self.priority,
            expires=self.expires,
        )(huey.lock_task(self.task_id)(self.wrapped_func))


RecurringTasks: dict[TaskID, RecurringTask] = {
    JOB_CREATE_TITLE_CARDS: RecurringTask(
        task_func=create_all_title_cards,
        description='Create all missing or outdated Title Cards',
        task_id=JOB_CREATE_TITLE_CARDS,
        default_cronstr='0 */12 * * *',
        error_message='Failed to create title cards',
        priority=90,
    ),
    JOB_DOWNLOAD_SERIES_LOGOS: RecurringTask(
        task_func=download_all_series_logos,
        description='Download logos for all Series',
        task_id=JOB_DOWNLOAD_SERIES_LOGOS,
        default_cronstr='0 0 */1 * *',
        error_message='Failed to download logos',
        priority=6,
    ),
    JOB_DOWNLOAD_SERIES_POSTERS: RecurringTask(
        task_func=download_all_series_posters,
        description='Download posters for all Series',
        task_id=JOB_DOWNLOAD_SERIES_POSTERS,
        default_cronstr='0 0 */1 * *',
        error_message='Failed to download posters',
        priority=5,
    ),
    JOB_LOAD_MEDIA_SERVERS: RecurringTask(
        task_func=load_all_media_servers,
        description='Load all Title Cards into media servers',
        task_id=JOB_LOAD_MEDIA_SERVERS,
        default_cronstr='0 */4 * * *',
        error_message='Failed to load Title Cards',
        priority=85,
    ),
    JOB_SYNC_INTERFACES: RecurringTask(
        task_func=sync_all,
        description='Sync and add any new Series',
        task_id=JOB_SYNC_INTERFACES,
        default_cronstr='0 */6 * * *',
        error_message='Failed to run all Syncs',
        priority=100,
    ),
    INTERNAL_JOB_CHECK_FOR_NEW_RELEASE: RecurringTask(
        task_func=get_latest_version,
        description='Check for a new release of TitleCardMaker',
        task_id=INTERNAL_JOB_CHECK_FOR_NEW_RELEASE,
        default_cronstr='0 0 */1 * *',
        error_message='Failed to get latest version',
        priority=0,
        internal=True,
    ),
    INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES: RecurringTask(
        task_func=refresh_all_card_types,
        description='Refresh all non-built-in card types',
        task_id=INTERNAL_JOB_REFRESH_REMOTE_CARD_TYPES,
        default_cronstr='0 0 */3 * *',
        error_message='Failed to refresh card types',
        priority=10,
        internal=True,
    ),
    INTERNAL_JOB_SET_SERIES_IDS: RecurringTask(
        task_func=set_all_series_ids,
        description='Set Series IDs',
        task_id=INTERNAL_JOB_SET_SERIES_IDS,
        default_cronstr='0 0 */2 * *',
        error_message='Failed to set Series IDs',
        priority=95,
        internal=True,
    ),
    JOB_BACKUP_DATABASE: RecurringTask(
        task_func=(
            lambda log: backup_data(settings.config.CURRENT_VERSION, log=log)
        ),
        description='Backup the database and global settings',
        task_id=JOB_BACKUP_DATABASE,
        default_cronstr='0 0 */1 * *',
        error_message='Failed to backup database',
        priority=50,
        internal=True,
    ),
    INTERNAL_JOB_CLEAN_DATABASE: RecurringTask(
        task_func=clean_database,
        description='Clean the database',
        task_id=INTERNAL_JOB_CLEAN_DATABASE,
        default_cronstr='0 12 */3 * *',
        error_message='Failed to clean the database',
        priority=15,
        internal=True,
    ),
    INTERNAL_JOB_CLEAR_OLD_LOGS: RecurringTask(
        task_func=clear_log_data,
        description='Clear old logs',
        task_id=INTERNAL_JOB_CLEAR_OLD_LOGS,
        default_cronstr='0 0 */1 * *',
        error_message='Failed to clear old logs',
        priority=0,
        internal=True,
    ),
    INTERNAL_JOB_SNAPSHOT_DATABASE: RecurringTask(
        task_func=snapshot_database,
        description='Take a database snapshot',
        task_id=INTERNAL_JOB_SNAPSHOT_DATABASE,
        default_cronstr='*/30 * * * *',
        error_message='Failed to snapshot database',
        priority=0,
        internal=True,
    ),
}


def get_task_details(db: Session, task_id: TaskID, /) -> TaskDetails:
    ...

    crontab = settings.task_schedules.get(
        task_id,
        RecurringTasks[task_id].default_cronstr
    )

    next_run: datetime = croniter(crontab).get_next(
        datetime,
        datetime.now(tz=settings.config.TIMEZONE),
    )

    # Get the last run details
    previous_start, previous_end, previous_duration = None, None, None
    last_run_details = get_previous_run_details(db, task_id)
    if last_run_details:
        previous_start, previous_end, previous_duration = last_run_details

    return TaskDetails(
        id=task_id,
        description=RecurringTasks[task_id].description,
        crontab=crontab,
        next_run=next_run,
        previous_start_time=previous_start,
        previous_end_time=previous_end,
        previous_duration=previous_duration,
        running=is_task_running(task_id),
        internal=RecurringTasks[task_id].internal,
    )
