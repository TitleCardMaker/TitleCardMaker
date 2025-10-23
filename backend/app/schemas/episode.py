# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false, reportAssignmentType=false
from datetime import datetime
from typing import Annotated, Any, Self

from pydantic import Field, field_validator, model_validator

from app.schemas.base import Base, DictKey, UNSPECIFIED
from app.schemas.ids import EmbyID, IMDbID, JellyfinID, TMDbID, TVDbID, TVRageID
from app.schemas.preferences import Style

"""
Base classes
"""

"""
Creation classes
"""
class NewEpisode(Base):
    series_id: int
    template_ids: list[int] = []
    font_id: int | None = None

    source_file: str | None = None
    card_file: str | None = None

    season_number: int = 1
    episode_number: int = 1
    absolute_number: int | None = None

    title: str
    match_title: bool | None = None
    auto_split_title: bool | None = None

    card_type: str | None
    hide_season_text: bool | None
    season_text: str | None
    hide_episode_text: bool | None
    episode_text: str | None
    unwatched_style: Style | None
    watched_style: Style | None

    font_color: str | None = None
    font_size: Annotated[float, Field(ge=0.0)] | None = None
    font_kerning: float | None = None
    font_stroke_width: float | None = None
    font_interline_spacing: int | None = None
    font_interword_spacing: int | None = None
    font_vertical_shift: int | None = None

    airdate: datetime | None = None
    emby_id: EmbyID = ''
    imdb_id: IMDbID = None
    jellyfin_id: JellyfinID = ''
    tmdb_id: TMDbID = None
    tvdb_id: TVDbID = None
    tvrage_id: TVRageID = None

    extras: dict[DictKey, Any] | None = None
    translations: dict[DictKey, str] = {}

    @model_validator(mode='after')
    def validate_unique_template_ids(self) -> Self:
        if len(self.template_ids) != len(set(self.template_ids)):
            raise ValueError('Template IDs must be unique')
        return self

"""
Update classes
"""
class UpdateEpisode(Base):
    template_ids: list[int] = UNSPECIFIED
    font_id: int | None = UNSPECIFIED

    source_file: str | None = UNSPECIFIED
    card_file: str | None = UNSPECIFIED

    season_number: int = UNSPECIFIED
    episode_number: int = UNSPECIFIED
    absolute_number: int | None = UNSPECIFIED

    title: str = UNSPECIFIED
    match_title: bool | None = UNSPECIFIED
    auto_split_title: bool | None = UNSPECIFIED

    card_type: str | None = UNSPECIFIED
    hide_season_text: bool | None = UNSPECIFIED
    season_text: str | None = UNSPECIFIED
    hide_episode_text: bool | None = UNSPECIFIED
    episode_text: str | None = UNSPECIFIED
    unwatched_style: Style | None = UNSPECIFIED
    watched_style: Style | None = UNSPECIFIED

    font_color: str | None = UNSPECIFIED
    font_size: Annotated[float, Field(ge=0.0)] | None = UNSPECIFIED
    font_kerning: float | None = UNSPECIFIED
    font_stroke_width: float | None = UNSPECIFIED
    font_interline_spacing: int | None = UNSPECIFIED
    font_interword_spacing: int | None = UNSPECIFIED
    font_vertical_shift: int | None = UNSPECIFIED

    airdate: datetime | None = UNSPECIFIED
    emby_id: EmbyID | None = UNSPECIFIED
    imdb_id: IMDbID = UNSPECIFIED
    jellyfin_id: JellyfinID | None = UNSPECIFIED
    tmdb_id: TMDbID = UNSPECIFIED
    tvdb_id: TVDbID = UNSPECIFIED
    tvrage_id: TVRageID = UNSPECIFIED

    extras: dict[DictKey, str] | None = UNSPECIFIED
    translations: dict[str, str] = UNSPECIFIED

    @field_validator('*', mode='before')
    @classmethod
    def validate_arguments(cls, value: str) -> str | None:
        return None if value == '' else value

    @model_validator(mode='after')
    def validate_unique_template_ids(self) -> Self:
        if (self.template_ids is not UNSPECIFIED
            and len(self.template_ids) != len(set(self.template_ids))):
            raise ValueError('Template IDs must be unique')
        return self

    @model_validator(mode='after')
    def convert_null_ids_to_empty_strings(self) -> Self:
        if self.emby_id is not UNSPECIFIED:
            self.emby_id = self.emby_id or ''
        if self.jellyfin_id is not UNSPECIFIED:
            self.jellyfin_id = self.jellyfin_id or ''
        return self

class BatchUpdateEpisode(Base):
    episode_id: int
    update_episode: UpdateEpisode

"""
Return classes
"""
class SeriesData(Base):
    name: str
    small_poster_url: str

class EpisodeOverview(Base):
    id: int
    season_number: int
    episode_number: int

class EpisodeData(Base):
    season_number: int
    episode_number: int
    title: str
    uid: Any

class Episode(Base):
    id: int
    template_ids: list[int]
    font_id: int | None

    source_file: str | None
    card_file: str | None

    season_number: int
    episode_number: int
    absolute_number: int | None

    title: str
    match_title: bool | None
    auto_split_title: bool | None

    card_type: str | None
    hide_season_text: bool | None
    season_text: str | None
    hide_episode_text: bool | None
    episode_text: str | None
    unwatched_style: str | None
    watched_style: str | None

    font_color: str | None
    font_size: Annotated[float, Field(ge=0.0)] | None
    font_kerning: float | None
    font_stroke_width: float | None
    font_interline_spacing: int | None
    font_interword_spacing: int | None
    font_vertical_shift: int | None

    airdate: datetime | None
    emby_id: EmbyID
    imdb_id: IMDbID
    jellyfin_id: JellyfinID
    tmdb_id: TMDbID
    tvdb_id: TVDbID
    tvrage_id: TVRageID

    extras: dict[DictKey, Any] | None
    translations: dict[str, str]

class ReducedEpisodeData(Base):
    id: int
    series_id: int
    series: SeriesData
    season_number: int
    episode_number: int
    title: str

class ExtendedEpisodeData(Episode):
    pass

class SimplifiedEpisodeData(Base):
    id: int

    season_number: int
    episode_number: int
    absolute_number: int | None

    title: str
    match_title: bool | None
    auto_split_title: bool | None

    season_text: str | None
    hide_season_text: bool | None
    episode_text: str | None
    hide_episode_text: bool | None

    extras: dict[DictKey, Any] | None
    translations: dict[str, str]
