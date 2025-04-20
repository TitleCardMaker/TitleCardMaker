from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import PositiveInt
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.query import get_series
from app.dependencies import get_database, get_preferences
from app.internal.auth import get_current_user
from app.models.card import Card
from app.models.episode import Episode
from app.models.font import Font
from app.models.loaded import Loaded
from app.models.preferences import Preferences
from app.models.series import Series
from app.models.snapshot import Snapshot as SnapshotModel
from app.models.sync import Sync
from app.models.duration import TaskDuration
from app.models.template import Template
from app.schemas.statistic import (
    AssetSize,
    CardCount,
    Duration,
    EpisodeCount,
    Snapshot,
    Statistic,
)


statistics_router = APIRouter(
    prefix='/statistics',
    tags=['Statistics'],
    dependencies=[Depends(get_current_user)],
)


@statistics_router.get('/system')
def get_system_statistics(
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> list[Statistic]:
    """Get all system statistics."""

    # Count objects
    card_count = db.query(Card.id).count()
    episode_count = db.query(Episode.id).count()
    font_count = db.query(Font.id).count()
    loaded_count = db.query(Loaded.id).count()
    series_count = db.query(Series.id).count()
    monitored_count = db.query(Series.id).filter_by(status='monitored').count()
    unmonitored_count = db.query(Series.id).filter_by(status='unmonitored').count()
    disabled_count = db.query(Series.id).filter_by(status='disabled').count()
    sync_count = db.query(Sync.id).count()
    template_count = db.query(Template.id).count()

    # Get and format total asset size | pylint: disable=not-callable
    asset_size = db.query(Card.filesize)\
        .with_entities(func.sum(Card.filesize))\
        .scalar()
    asset_size = 0 if asset_size is None else asset_size
    formatted_filesize = preferences.format_filesize(asset_size)

    return [
        Statistic(
            value=card_count, value_text=f'{card_count:,}', unit='Cards',
            description='Number of Title Cards',
        ),
        Statistic(
            value=series_count, value_text=f'{series_count:,}', unit='Series',
            description='Number of Series',
        ),
        Statistic(
            value=monitored_count, value_text=f'{monitored_count:,}',
            unit='Monitored',
            description='Number of Monitored Series',
        ),
        Statistic(
            value=unmonitored_count, value_text=f'{unmonitored_count:,}',
            unit='Unmonitored',
            description='Number of Unmonitored Series',
        ),
        Statistic(
            value=disabled_count, value_text=f'{disabled_count:,}',
            unit='Disabled',
            description='Number of Disabled Series',
        ),
        Statistic(
            value=episode_count, value_text=f'{episode_count:,}',
            unit='Episodes',
            description='Number of Episodes',
        ),
        Statistic(
            value=asset_size, value_text=formatted_filesize[0],
            unit=formatted_filesize[1],
            description='File size of all Title Cards',
        ),
        Statistic(
            value=font_count, value_text=f'{font_count:,}', unit='Fonts',
            description='Number of Named Fonts',
        ),
        Statistic(
            value=template_count, value_text=f'{template_count:,}',
            unit='Templates', description='Number of Templates',
        ),
        Statistic(
            value=sync_count, value_text=f'{sync_count:,}', unit='Syncs',
            description='Number of Syncs',
        ),
        Statistic(
            value=loaded_count, value_text=f'{loaded_count:,}',
            unit='Loaded Cards', description='Number of loaded Title Cards',
        )
    ]


@statistics_router.get('/series/{series_id}')
def get_series_statistics(
        series_id: int,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> list[Statistic]:
    """
    Get the statistics for the given Series.

    - series_id: ID of the Series to get the statistics of.
    """

    # Verify Series exists
    get_series(db, series_id, raise_exc=True)

    # Count the Episodes, Cards, and total asset size | pylint: disable=not-callable
    episode_count = db.query(Episode.id).filter_by(series_id=series_id).count()
    card_count = db.query(Card.id).filter_by(series_id=series_id).count()
    asset_size = (db.query(Card.filesize)\
        .filter_by(series_id=series_id)\
        .with_entities(func.sum(Card.filesize))\
        .scalar()) or 0

    return [
        CardCount(value=card_count, value_text=f'{card_count:,}'),
        EpisodeCount(value=episode_count, value_text=f'{episode_count:,}'),
        AssetSize(
            value=asset_size,
            value_text=preferences.format_filesize(asset_size)[0],
            unit=preferences.format_filesize(asset_size)[1],
        ),
    ]


@statistics_router.get('/snapshots')
def get_snapshots(
        previous_days: float = Query(default=14, ge=0.0),
        previous_hours: float = Query(default=0, ge=0.0),
        slice_: PositiveInt = Query(alias='slice', default=1),
        db: Session = Depends(get_database),
    ) -> list[Snapshot]:
    """
    Get the database Snapshots from the given number of days in the past.

    - previous_days: How many days of past snapshots to return. Added to
    previous hours.
    - previous_hours: How many hours of past snapshots to return. Added
    to previous days.
    - slice: How to "slice" the return - e.g. `1` would be every
    Snapshot, `2` would be every other, etc.
    """

    previous = datetime.now() \
        - timedelta(days=previous_days, hours=previous_hours)

    # Get subquery on Snapshots which includes the row number column for
    # slicing
    subquery = (
        # Add row number as new column
        select(
            SnapshotModel,
            func.row_number().over(order_by=SnapshotModel.id).label('row')
        )
        # Apply timestamp filter
        .filter(SnapshotModel.timestamp > previous)
        .subquery()
    )

    return db.query(subquery).filter(subquery.c.row % slice_ == 0).all()


@statistics_router.get('/task-durations')
def get_task_durations(
        after: datetime = Query(default=datetime.now() - timedelta(days=7)),
        task_name: str | None = Query(default=None),
        db: Session = Depends(get_database),
    ) -> list[Duration]:
    """
    Get the Task Durations for the given Series.

    - after: Datetime to filter by. All tasks after this datetime will
    be returned.
    - task_name: Optional Task name to filter by.
    """

    filters = []
    if after:
        filters.append(TaskDuration.start_time > after)
    if task_name:
        filters.append(TaskDuration.task_name == task_name)

    return db.query(TaskDuration).filter(*filters).all()
