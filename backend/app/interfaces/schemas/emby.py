from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class SystemInfo(BaseModel):
    server_name: str = Field(alias='ServerName')
    version: str = Field(alias='Version')
    id: str = Field(alias='Id')

class UserQueryItem(BaseModel):
    name: str = Field(alias='Name')
    id: str = Field(alias='Id')

class UserQuery(BaseModel):
    items: list[UserQueryItem] = Field(alias='Items')

class UserDetails(BaseModel):
    name: str = Field(alias='Name')

class LibrarySubFolder(BaseModel):
    name: str = Field(alias='Name')
    id: int = Field(alias='Id')
    path: str = Field(alias='Path')

class LibraryMediaFolder(BaseModel):
    name: str = Field(alias='Name')
    id: int = Field(alias='Id')
    subfolders: list[LibrarySubFolder] = Field(alias='SubFolders')

class UserData(BaseModel):
    played: bool = Field(alias='Played', default=False)

class ItemDetails(BaseModel):
    parent_id: int | None = Field(alias='ParentId', default=None)
    name: str = Field(alias='Name')
    type: Literal['Series'] | str = Field(alias='Type')
    premiere_date: datetime | None = Field(alias='PremiereDate', default=None)
    production_year: int | None = Field(alias='ProductionYear', default=None)
    provider_ids: dict[str, str] = Field(alias='ProviderIds', default={})
    id: int = Field(alias='Id')
    series_id: str | None = Field(alias='SeriesId', default=None)
    index_number: int | None = Field(alias='IndexNumber', default=None)
    parent_index_number: int | None = Field(alias='ParentIndexNumber', default=None)
    status: Literal['Continuing'] | str | None = Field(alias='Status', default=None)
    overview: str | None = Field(alias='Overview', default=None)
    user_data: UserData = Field(alias='UserData', default_factory=UserData)

class QueryResult(BaseModel):
    total_record_count: int = Field(alias='TotalRecordCount')
    items: list[ItemDetails] = Field(alias='Items')

class EpisodeDetails(BaseModel):
    name: str = Field(alias='Name')
    id: str = Field(alias='Id')
    series_id: str = Field(alias='SeriesId')
    index_number: int = Field(alias='IndexNumber')
    parent_index_number: int = Field(alias='ParentIndexNumber')
    provider_ids: dict[str, str] = Field(alias='ProviderIds', default={})
    premiere_date: datetime | None = Field(alias='PremiereDate', default=None)
    user_data: UserData = Field(alias='UserData', default_factory=UserData)

class EpisodeQueryResult(BaseModel):
    total_record_count: int = Field(alias='TotalRecordCount')
    items: list[EpisodeDetails] = Field(alias='Items')
