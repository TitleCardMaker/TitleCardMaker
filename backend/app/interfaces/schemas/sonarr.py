from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CoverType = Literal[
    'unknown',
    'poster',
    'banner',
    'fanart',
    'screenshot',
    'headshot',
    'clearlogo'
]
SeriesStatus = Literal['continuing', 'ended', 'upcoming', 'deleted']
SeriesType = Literal['standard', 'daily', 'anime']


class SystemInfo(BaseModel):
    app_name: str = Field(alias='appName')

class RootFolder(BaseModel):
    path: str

class MediaCover(BaseModel):
    cover_type: CoverType = Field(alias='coverType')
    url: str

class SeriesStatistics(BaseModel):
    # season_count: int = Field(alias='seasonCount')
    # episode_count: int = Field(alias='episodeCount')
    # episode_file_count: int = Field(alias='episodeFileCount')
    size_on_disk: int = Field(alias='sizeOnDisk')
    # percent_of_episodes: int = Field(alias='percentOfEpisodes')

class SeriesResource(BaseModel):
    id: int
    title: str | None
    year: int
    ended: bool
    monitored: bool
    type: SeriesType = Field(alias='seriesType')
    status: SeriesStatus
    statistics: SeriesStatistics
    overview: str | None = None
    path: str | None
    root_folder_path: str | None = Field(alias='rootFolderPath')
    tags: list[int]
    images: list[MediaCover]
    imdb_id: str | None = Field(default=None, alias='imdbId')
    tvdb_id: int | None = Field(default=None, alias='tvdbId')
    tvmaze_id: int | None = Field(default=None, alias='tvMazeId')
    tvrage_id: int | None = Field(default=None, alias='tvRageId')

class EpisodeResource(BaseModel):
    episode_number: int | None = Field(alias='episodeNumber')
    season_number: int | None = Field(alias='seasonNumber')
    absolute_episode_number: int | None = Field(
        default=None,
        alias='absoluteEpisodeNumber'
    )
    airdate: datetime | None = Field(default=None, alias='airDateUtc')
    monitored: bool
    tvdb_id: int | None = Field(default=None, alias='tvdbId')
    has_file: bool = Field(default=False, alias='hasFile')
    title: str | None

class TagResource(BaseModel):
    id: int
    label: str | None
