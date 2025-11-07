from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

from .emby import SystemInfo


class UserQueryItem(BaseModel):
    id: str = Field(alias='Id')
    name: str = Field(alias='Name')

class Library(BaseModel):
    id: str = Field(alias='Id')
    name: str = Field(alias='Name')

class LibraryQuery(BaseModel):
    items: list[Library] = Field(alias='Items')

class UserData(BaseModel):
    played: bool = Field(alias='Played', default=False)

class ItemDetails(BaseModel):
    id: str = Field(alias='Id')
    name: str = Field(alias='Name')
    tags: list[str] = Field(alias='Tags', default=[])
    type: Literal['Series'] | str = Field(alias='Type')
    premiere_date: datetime | None = Field(alias='PremiereDate', default=None)
    production_year: int | None = Field(alias='ProductionYear', default=None)
    provider_ids: dict[str, str] = Field(alias='ProviderIds', default={})
    series_id: str | None = Field(alias='SeriesId', default=None)
    index_number: int | None = Field(alias='IndexNumber', default=None)
    parent_index_number: int | None = Field(alias='ParentIndexNumber', default=None)
    status: Literal['Continuing'] | str | None = Field(alias='Status', default=None)
    overview: str | None = Field(alias='Overview', default=None)
    user_data: UserData = Field(alias='UserData', default_factory=UserData)

class ItemQuery(BaseModel):
    items: list[ItemDetails] = Field(alias='Items')
    total_record_count: int = Field(alias='TotalRecordCount')


__all__ = [
    'UserQueryItem',
    'LibraryQuery',
    'ItemDetails',
    'ItemQuery',
    'SystemInfo',
]
