from datetime import datetime, timedelta
from logging import Logger

from app.dependencies import get_log_database
from app.logging.logger import log
from app.logging.models import Log
from app.settings import settings


def clear_log_data(*, log: Logger = log) -> None:
    """Clear old logs from the database."""

    with next(get_log_database()) as db:
        cutoff_date = (
            datetime.now()
            - timedelta(days=settings.config.LOG_RETENTION_DAYS)
        )

        log_query = db.query(Log).filter(Log.timestamp < cutoff_date)
        log.debug(f'Clearing {log_query.count()} logs')
        log_query.delete()
        db.commit()
