from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.logging.database import LogsBase
from app.schemas.logs import LogLevel


class Log(LogsBase):
    """
    SQL Table that defines a Log entry. This contains all the details
    of a log message including timestamp, level, message, and exception
    information if present.
    """

    __tablename__ = 'logs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    timestamp: Mapped[datetime]
    level_name: Mapped[LogLevel]
    level_number: Mapped[int] = mapped_column(String, index=True)
    message: Mapped[str]
    context_id: Mapped[str | None] = mapped_column(index=True)
    file: Mapped[str | None]
    line: Mapped[int | None]
    exception_type: Mapped[str | None]
    exception_value: Mapped[str | None]
    exception_traceback: Mapped[str | None]
