# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from datetime import datetime
from typing import Literal

from app.schemas.base import Base


"""
Base classes
"""
LogLevel = Literal['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


"""
Return classes
"""
class LogException(Base):
    type: str
    value: str
    traceback: str

class LogEntry(Base):
    level: LogLevel
    context_id: str | None
    time: datetime
    message: str
    exception: LogException | None

class LogInternalServerError(Base):
    context_id: str | None
    time: datetime
    # message: str
    file: str
