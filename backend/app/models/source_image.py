from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.episode import Episode


class SourceImage(Base):
    """
    SQL Table that defines a Source Image for an Episode. This records
    metadata about the unique-style source image file on disk: when it
    was obtained, which interface it came from, its resolved path, and
    its dimensions. Art-style (backdrop) images are not tracked here
    because they are shared across all Episodes of a Series/Season.
    """

    __tablename__ = 'source_image'

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True,
    )
    episode_id: Mapped[int] = mapped_column(
        ForeignKey('episode.id'), unique=True, index=True,
    )
    created: Mapped[datetime] = mapped_column(
        default=func.now(), # pylint: disable=not-callable
    )

    episode: Mapped['Episode'] = relationship(back_populates='source_image')

    source_file: Mapped[str]
    filesize: Mapped[int]
    width: Mapped[int]
    height: Mapped[int]
    source: Mapped[str]
    """
    Where the image was obtained from. One of: "tmdb", "tvdb", "emby",
    "jellyfin", "plex", "upload", "mirror", "unknown".
    """


    def __repr__(self) -> str:
        return (
            f'SourceImage[{self.id}] Episode[{self.episode_id}] '
            f'from "{self.source}" at "{self.source_file}"'
        )


    @property
    def file(self) -> Path:
        """Path of this source image file."""

        return Path(self.source_file)


    @property
    def exists(self) -> bool:
        """Whether the source image file for this object exists."""

        return self.file.exists()
