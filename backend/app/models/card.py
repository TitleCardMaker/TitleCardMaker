from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON, func
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.settings import settings

if TYPE_CHECKING:
    from app.models.connection import Connection
    from app.models.episode import Episode
    from app.models.loaded import Loaded
    from app.models.series import Series


class Card(Base):
    """
    SQL Table that defines a Title Card. This contains all the details
    used in the Card creation, as well as relational objects to the
    associated Series, Episode, and Loaded instances.
    """

    __tablename__ = 'card'

    # Referencial arguments
    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True,
    )
    interface_id: Mapped[int | None] = mapped_column(ForeignKey('connection.id'))
    series_id: Mapped[int] = mapped_column(ForeignKey('series.id'))
    episode_id: Mapped[int] = mapped_column(ForeignKey('episode.id'))

    created: Mapped[datetime] = mapped_column(
        default=func.now(), # pylint: disable=not-callable
    )

    connection: Mapped['Connection'] = relationship(back_populates='cards')
    series: Mapped['Series'] = relationship(back_populates='cards')
    episode: Mapped['Episode'] = relationship(back_populates='cards')
    loaded: Mapped['Loaded'] = relationship(
        back_populates='card',
        foreign_keys='Loaded.card_id',
    )

    card_file: Mapped[str]
    source_file: Mapped[str]
    filesize: Mapped[int]
    library_name: Mapped[str | None]

    card_type: Mapped[str]
    model_json: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(JSON), # type: ignore
        default={}
    )


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'Card "{self.card_file}"'


    @property
    def exists(self) -> bool:
        """Whether the Card file for this object exists."""

        return Path(self.card_file).exists()

    @property
    def file(self) -> Path:
        """Path of this Card file."""

        return Path(self.card_file)

    @property
    def file_url(self) -> str:
        """URL to the Card file."""

        return self.card_file.replace(
            str(settings.card_directory),
            '/cards'
        )
