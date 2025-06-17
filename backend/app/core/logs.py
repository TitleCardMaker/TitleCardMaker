from datetime import datetime, timedelta
from pathlib import Path
from typing import TypedDict

from sqlalchemy import select

from app.logging.database import LogsSessionLocal
from app.logging.models import Log
from app.schemas.logs import LogLevel
from app.logging.logger import log


# pylint: disable=missing-class-docstring
class ExecutionDetails(TypedDict):
    file: str
    line: int

class ExceptionDetails(TypedDict):
    type: str
    value: str
    traceback: str

class RawLogData(TypedDict):
    message: str
    context_id: str
    level: LogLevel
    time: datetime
    execution: ExecutionDetails
    exception: ExceptionDetails | None
    file: Path
# pylint: enable=missing-class-docstring

def read_log_files(
        *,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[RawLogData]:
    """
    Read all raw log data from the SQLite database.

    Args:
        after: Earliest date of logs to return.
        before: Latest date of logs to return.
    """

    # Build the query
    query = select(Log)
    
    if after:
        query = query.where(Log.timestamp > after)
    if before:
        query = query.where(Log.timestamp < before)
    
    # Add ordering and limit for shallow queries
    query = query.order_by(Log.timestamp.desc())

    logs: list[RawLogData] = []
    try:
        db = LogsSessionLocal()
        rows = db.execute(query).scalars().all()

        for row in rows:
            # Convert row to RawLogData format
            log_data: RawLogData = {
                'message': row.message,
                'context_id': row.context_id,
                'level': row.level,
                'time': row.timestamp,
                'execution': {
                    'file': row.file or '',
                    'line': row.line or 0
                },
                'exception': None,
                'file': Path(row.file) if row.file else Path('')
            }

            # Add exception details if present
            if row.exception_type:
                log_data['exception'] = {
                    'type': row.exception_type,
                    'value': row.exception_value,
                    'traceback': row.exception_traceback
                }

            logs.append(log_data)

    except Exception as e:
        log.error(f"Error reading logs from database: {e}")
    finally:
        if 'db' in locals():
            db.close()

    return logs

def clear_log_data() -> None:
    """
    Clear old logs from the database.
    Keeps logs from the last 7 days by default.
    """
    try:
        db = LogsSessionLocal()
        
        # Delete logs older than 7 days
        retention_days = 7
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        db.query(Log).filter(Log.timestamp < cutoff_date).delete()
        db.commit()
    except Exception as e:
        log.error(f"Error clearing old logs: {e}")
    finally:
        if 'db' in locals():
            db.close()
