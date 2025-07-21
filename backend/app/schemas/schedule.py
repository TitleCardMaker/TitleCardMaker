# pyright: reportInvalidTypeForm=false
from datetime import datetime

from app.schemas.base import Base

"""
Base classes
"""
CronExpression = r'^([^ ]+\s+){4}([^ ]+)$'

def Seconds(v: int, /) -> int: return v
def Minutes(v: int, /) -> int: return Seconds(v * 60)
def Hours(v: int, /) -> int: return Minutes(v * 60)
def Days(v: int, /) -> int: return Hours(v * 24)

"""
Return classes
"""
class CoreTaskDetails(Base):
    id: str
    description: str
    internal: bool = False
    default_crontab: str

class TaskDetails(Base):
    id: str
    description: str
    crontab: str
    next_run: datetime
    previous_start_time: datetime | None = None
    previous_end_time: datetime | None = None
    previous_duration: float | None = None
    running: bool
    internal: bool
