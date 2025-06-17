from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.dependencies import get_database, get_preferences
from app.models.card import Card
from app.models.duration import TaskDuration
from app.models.episode import Episode
from app.models.font import Font
from app.models.loaded import Loaded
from app.models.series import Series
from app.models.snapshot import Snapshot
from app.models.sync import Sync
from app.models.template import Template
from app.models.user import User
from app.schemas.schedule import NewJob
from app.schemas.statistic import NewSnapshot
from app.logging.logger import Logger, log


def snapshot_database(*, log: Logger = log) -> None:
    """
    Schedulable function to take a snapshot of the database.

    Args:
        log: Logger for all log messages.
    """

    try:
        with next(get_database()) as db:
            take_snapshot(db, log=log)
    except Exception:
        log.exception('Failed to take snapshot')


def take_snapshot(db: Session, *, log: Logger = log) -> None:
    """
    Take a snapshot of the database.

    Args:
        db: Session to snapshot and add the snapshot to.
        log: Logger for all log messages.
    """

    # Determine total card creation count; max of Card.id and previous card
    # creation count
    # pylint: disable=not-callable
    try:
        cards_created = max(
            db.query(func.max(Card.id)).scalar(),
            db.query(func.max(Snapshot.cards_created)).scalar()
        )
    except TypeError:
        cards_created = db.query(func.max(Card.id)).scalar() or 0

    snapshot = NewSnapshot(
        blueprints=len(get_preferences().imported_blueprints),
        cards=db.query(Card.id).count(),
        episodes=db.query(Episode.id).count(),
        fonts=db.query(Font.id).count(),
        loaded=db.query(Loaded.id).count(),
        series=db.query(Series.id).count(),
        syncs=db.query(Sync.id).count(),
        templates=db.query(Template.id).count(),
        users=db.query(User.id).count(),
        filesize=db.query(Card.filesize)\
            .with_entities(func.sum(Card.filesize))\
            .scalar() or 0,
        cards_created=cards_created,
    )
    log.debug(f'Took snapshot of database ({snapshot})')

    db.add(Snapshot(**snapshot.dict()))
    db.commit()


def add_task_duration(db: Session, job: NewJob) -> TaskDuration | None:
    """
    Add the last-run task duration of the given job.

    Args:
        db: Session to the database to add the TaskDUration to.
        log: Logger for all log messages.

    Returns:
        Newly added TaskDuration object. None if there was no prior
        start/end time.
    """

    # Do not add a record if there is no start/end time
    if not job.previous_start_time or not job.previous_end_time:
        return None

    # Create new record
    duration_time = (job.previous_end_time - job.previous_start_time)
    duration = TaskDuration(
        task_name=job.id,
        start_time=job.previous_start_time,
        end_time=job.previous_end_time,
        duration=duration_time.total_seconds()
    )

    # Add to database, commit changes
    db.add(duration)
    db.commit()

    return duration
