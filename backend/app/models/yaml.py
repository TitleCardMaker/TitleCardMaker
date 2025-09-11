from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import YamlBase


class Loaded(YamlBase):
    """
    SQL Table that defines a Loaded asset. This contains which media
    server the asset was loaded into, the file size of the asset, as
    well as relational objects to the parent Series, Episode, and Card.
    """

    __tablename__ = 'loaded'

    id: Mapped[int] = mapped_column(primary_key=True)


class SeasonPoster(YamlBase):
    """
    SQL Table that defines a Season Poster. This contains the details
    of a season poster, as well as relational objects to the parent Series.
    """

    __tablename__ = 'season_posters'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    series_name: Mapped[str] = mapped_column(index=True)
    library_name: Mapped[str] = mapped_column(index=True)
    season_number: Mapped[int] = mapped_column(index=True)
    filesize: Mapped[int]


class Blacklist(YamlBase):
    """
    SQL Table that defines a Blacklist. This contains the details
    of a blacklist, as well as relational objects to the parent Series.
    """

    __tablename__ = 'blacklist'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    series_name: Mapped[str] = mapped_column(index=True)
    season_number: Mapped[int] = mapped_column(index=True)
    episode_number: Mapped[int] = mapped_column(index=True)
    query_type: Mapped[str] = mapped_column(index=True)
    failures: Mapped[int]
    next: Mapped[datetime]


class SeriesRecord(YamlBase):
    """
    SQL Table that defines a Series Record. This contains the details
    of a series record, as well as relational objects to the parent Series.
    """

    __tablename__ = 'series_records'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    series_name: Mapped[str] = mapped_column(index=True)
    directory: Mapped[str] = mapped_column(index=True)
    hash: Mapped[str]
