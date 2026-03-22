from datetime import datetime
from typing import get_args
from warnings import simplefilter

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
)
from fastapi.responses import FileResponse
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.utils import FastAPIPaginationWarning
from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import Session

from app.db.pagination import Page
from app.db.users import get_current_user
from app.dependencies import get_log_database
from app.logging.database import LOGS_DATABASE_PATH
from app.logging.logger import log
from app.logging.models import Log as LogModel
from app.schemas.logs import LogEntry, LogInternalServerError, LogLevel
from app.settings import settings
from app.utils.tzip import TemporaryZip


# Do not warn about SQL pagination, not used for log filtering
simplefilter('ignore', FastAPIPaginationWarning)


# Create sub router for all /logs API requests
log_router = APIRouter(
    prefix='/logs',
    tags=['Logs'],
    dependencies=[Depends(get_current_user)],
)

# Map of log level names to numbers for relative comparison
_LEVEL_NUMBERS: dict[LogLevel, int] = {
    level: log.level(level).no
    for level in get_args(LogLevel)
}


@log_router.get('/query')
def query_logs(
        level: LogLevel = Query(default='DEBUG'),
        after: datetime | None = Query(default=None),
        before: datetime | None = Query(default=None),
        context_id: str | None = Query(default=None, min_length=1),
        contains_: str | None = Query(alias='contains', default=None, min_length=1),
        log_db: Session = Depends(get_log_database),
    ) -> Page[LogEntry]: # type: ignore
    """
    Query all log entries for the given criteria.

    - level: Minimum log level. All messages of lower levels are removed.
    - after: Earliest date of logs to return. ISO 8601 format.
    - before: Latest date of logs to return. ISO 8601 format.
    - context_id: Comma separated list of contexts to filter by. If `!`
    is included, logs with no context ID's are excluded.
    - contains: Required substring. Case insensitive.
    """

    # Build filters
    filters = [LogModel.level_number >= _LEVEL_NUMBERS[level]]
    if after is not None:
        filters.append(LogModel.timestamp >= after)
    if before is not None:
        filters.append(LogModel.timestamp <= before)
    if context_id is not None:
        # Includes !, do not allow null context IDs
        if '!' in context_id:
            filters.append(and_(
                # Do not allow null context IDs
                not_(LogModel.context_id.is_(None)),
                # Can match any of the given context IDs
                or_(*[
                    LogModel.context_id == context_id
                    for context_id in context_id.replace('!', '').split(',')
                ])
            ))
        # No !, allow null context IDs
        else:
            filters.append(or_(
                LogModel.context_id.is_(None),
                LogModel.context_id.in_(context_id.split(',')),
            ))
    if contains_ is not None:
        # Pipe-separated list of contains strings
        if '|' in contains_:
            filters.append(or_(*[
                LogModel.message.contains(substring)
                for substring in contains_.split('|')
            ]))
        else:
            filters.append(LogModel.message.contains(contains_))

    return paginate(
        log_db.query(LogModel)
            .filter(*filters)
            .order_by(LogModel.timestamp.desc())
    )


@log_router.get('/errors')
def get_internal_server_errors(
        log_db: Session = Depends(get_log_database),
    ) -> list[LogInternalServerError]:
    """
    Get a list of all internal server errors listed in the log files.
    """

    return [
        LogInternalServerError.model_validate(log)
        for log in log_db.query(LogModel)
            .filter(LogModel.message.startswith('Internal Server Error'))
            .order_by(LogModel.timestamp.desc())
            .all()
    ]


@log_router.get('/database-zip')
def get_database_zip(background_tasks: BackgroundTasks) -> FileResponse:
    """Get a zip of the log database."""

    # Add log file to a temporary directory
    tzip = TemporaryZip(settings.temporary_directory, background_tasks)
    tzip.add_file(LOGS_DATABASE_PATH, 'logs.sqlite')

    return FileResponse(tzip.zip())


@log_router.delete('/prune')
def prune_logs(
        log_db: Session = Depends(get_log_database),
        delete_before: datetime = Query(...),
    ) -> None:
    """
    Prune old logs from the database.
    
    - delete_before: Delete logs before this date.
    """

    log_query = log_db.query(LogModel).filter(LogModel.timestamp <delete_before)
    log.debug(f'Pruning {log_query.count():,} log entries')
    log_query.delete()
    log_db.commit()
