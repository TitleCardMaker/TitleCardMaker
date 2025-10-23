# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Annotated
from pydantic import AnyUrl, DirectoryPath, Field

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
    episodes: dict[Annotated[int, Field(ge=0)], _KometaEpisode] = {}

class _KometaSeries(Base):
    url_poster: AnyUrl | None = None
    url_background: AnyUrl | None = None
    seasons: dict[Annotated[int, Field(ge=0)], _KometaSeason] = {}

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
