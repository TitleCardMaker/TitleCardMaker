from datetime import datetime, timedelta
from pathlib import Path
from typing import TypedDict
import sqlite3

from app.schemas.logs import LogLevel

from modules.Debug import (
    log,  # noqa: F401
    DATETIME_FORMAT,
    DATETIME_FORMAT_NO_TZ,
    LOG_DB
)


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
        shallow: bool = True,
    ) -> list[RawLogData]:
    """
    Read all raw log data from the SQLite database.

    Args:
        after: Earliest date of logs to return.
        before: Latest date of logs to return.
        shallow: Whether to only do a "shallow" query, which will only
            evaluate the most recent logs (last 1000 entries).
    """
    logs: list[RawLogData] = []
    
    # Build the query
    query = "SELECT * FROM logs"
    params = []
    
    conditions = []
    if after:
        conditions.append("timestamp > ?")
        params.append(after.strftime(DATETIME_FORMAT))
    if before:
        conditions.append("timestamp < ?")
        params.append(before.strftime(DATETIME_FORMAT))
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # Add ordering and limit for shallow queries
    query += " ORDER BY timestamp DESC"
    if shallow:
        query += " LIMIT 1000"
    
    try:
        conn = sqlite3.connect(LOG_DB)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        for row in rows:
            # Convert row to RawLogData format
            log_data: RawLogData = {
                'message': row['message'],
                'context_id': row['context_id'],
                'level': row['level'],
                'time': datetime.strptime(row['timestamp'], DATETIME_FORMAT),
                'execution': {
                    'file': row['file'],
                    'line': row['line']
                },
                'exception': None,
                'file': Path(row['file']) if row['file'] else Path('')
            }
            
            # Add exception details if present
            if row['exception_type']:
                log_data['exception'] = {
                    'type': row['exception_type'],
                    'value': row['exception_value'],
                    'traceback': row['exception_traceback']
                }
            
            logs.append(log_data)
            
    except sqlite3.Error as e:
        log.error(f"Error reading logs from database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    return logs

def clear_log_data() -> None:
    """
    Clear old logs from the database.
    Keeps logs from the last 7 days by default.
    """
    try:
        conn = sqlite3.connect(LOG_DB)
        cursor = conn.cursor()
        
        # Delete logs older than 7 days
        retention_days = 7
        cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime(DATETIME_FORMAT)
        cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_date,))
        
        conn.commit()
    except sqlite3.Error as e:
        log.error(f"Error clearing old logs: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
