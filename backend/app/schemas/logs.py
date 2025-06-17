# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from datetime import datetime
from typing import Literal

from app.schemas.base import Base


LogLevel = Literal['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

class LogEntry(Base):
    level_name: LogLevel
    level_number: int
    context_id: str | None
    timestamp: datetime
    message: str
    exception_type: str | None
    exception_value: str | None
    exception_traceback: str | None

class LogInternalServerError(Base):
    context_id: str | None
    timestamp: datetime
