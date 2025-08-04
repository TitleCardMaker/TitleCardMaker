from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class TaskDuration(Base):
    __tablename__ = 'task_durations'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    task_name: Mapped[str]
    start_time: Mapped[datetime]
    end_time: Mapped[datetime] = mapped_column(default=func.now())
    duration: Mapped[float] # Duration in seconds


    def __repr__(self):
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60

        parts = []
        if hours > 0:
            parts.append(f'{hours} hour' + ('s' if hours > 1 else ''))
        if minutes > 0:
            parts.append(f'{minutes} minute' + ('s' if minutes > 1 else ''))
        if seconds > 0 and not parts:
            parts.append(f'{seconds:.1f} seconds')
        duration_str = " ".join(parts[:2])

        end_time = self.end_time.strftime('%Y-%m-%d %H:%M')
        return f'Task[{self.task_name}] taking {duration_str} ending {end_time}'
