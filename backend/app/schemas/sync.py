# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false
from typing import Literal

from pydantic import constr, field_validator

from app.schemas.base import Base, UNSPECIFIED


SonarrSeriesType = Literal['anime', 'daily', 'standard']
Interface = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr']


class Tag(Base):
    id: int
    label: str
    interface_id: int

class NewBaseSync(Base):
    name: constr(min_length=1)
    interface_id: int
    add_as_unmonitored: bool = False
    template_ids: list[int] = []
    required_tags: list[str] = []
    excluded_tags: list[str] = []

    @field_validator('template_ids', mode='after')
    @classmethod
    def validate_unique_template_ids(cls, value: list[int]) -> list[int]:
        if (cls.__name__.startswith(('New', 'Update'))
            and len(value) != len(set(value))):
            raise ValueError('Template IDs must be unique')
        return value

class NewMediaServerSync(NewBaseSync):
    required_libraries: list[str] = []
    excluded_libraries: list[str] = []

class NewEmbySync(NewMediaServerSync):
    interface: Literal['Emby'] = 'Emby'

class NewJellyfinSync(NewMediaServerSync):
    interface: Literal['Jellyfin'] = 'Jellyfin'

class NewPlexSync(NewMediaServerSync):
    interface: Literal['Plex'] = 'Plex'

class NewSonarrSync(NewBaseSync):
    interface: Literal['Sonarr'] = 'Sonarr'
    downloaded_only: bool = False
    monitored_only: bool = False
    required_series_type: SonarrSeriesType | None = None
    excluded_series_type: SonarrSeriesType | None = None
    required_root_folders: list[str] = []

class ExistingBaseSync(NewBaseSync):
    id: int
    interface: Interface

class EmbySync(ExistingBaseSync, NewMediaServerSync):
    interface: Interface = 'Emby'

class JellyfinSync(ExistingBaseSync, NewMediaServerSync):
    interface: Interface = 'Jellyfin'

class PlexSync(ExistingBaseSync, NewMediaServerSync):
    interface: Interface = 'Plex'

class SonarrSync(ExistingBaseSync, NewSonarrSync):
    interface: Interface = 'Sonarr'

class Sync(ExistingBaseSync, NewSonarrSync):
    ...

class UpdateSync(Base):
    name: constr(min_length=1) = UNSPECIFIED
    add_as_unmonitored: bool = UNSPECIFIED
    interface_id: int = UNSPECIFIED
    template_ids: list[int] = UNSPECIFIED
    required_tags: list[str] = UNSPECIFIED
    excluded_tags: list[str] = UNSPECIFIED
    required_libraries: list[str] = UNSPECIFIED
    excluded_libraries: list[str] = UNSPECIFIED
    downloaded_only: bool = UNSPECIFIED
    monitored_only: bool = UNSPECIFIED
    required_root_folders: list[str] = UNSPECIFIED
    required_series_type: SonarrSeriesType | None = UNSPECIFIED
    excluded_series_type: SonarrSeriesType | None = UNSPECIFIED

    @field_validator('template_ids', mode='after')
    @classmethod
    def validate_unique_template_ids(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError('Template IDs must be unique')
        return value
