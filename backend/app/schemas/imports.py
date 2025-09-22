# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from pydantic import AnyUrl, DirectoryPath, NonNegativeInt

from app.schemas.base import Base
from app.schemas.preferences import CardExtension

"""
Base classes
"""
class ImportBase(Base):
    yaml: str

class _KometaEpisode(Base):
    url_poster: AnyUrl | None = None

class _KometaSeason(Base):
    url_poster: AnyUrl | None = None
    episodes: dict[NonNegativeInt, _KometaEpisode] = {}

class _KometaSeries(Base):
    url_poster: AnyUrl | None = None
    url_background: AnyUrl | None = None
    seasons: dict[NonNegativeInt, _KometaSeason] = {}

class KometaYaml(Base):
    yaml: dict[int, _KometaSeries]

"""
Return classes
"""
class ImportYaml(ImportBase):
    ...

class ImportCardDirectory(Base):
    directory: DirectoryPath | None = None
    image_extension: CardExtension = '.jpg'
    force_reload: bool = False

class MultiCardImport(Base):
    series_ids: list[int]
    image_extension: CardExtension = '.jpg'
    force_reload: bool = False
