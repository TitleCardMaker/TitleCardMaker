# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false, reportAssignmentType=false
from datetime import datetime
from typing import Any

from pydantic import PositiveFloat, root_validator, validator # pylint: disable=no-name-in-module

from app.schemas.base import (
    Base,
    UpdateBase,
    UNSPECIFIED,
    validate_argument_lists_to_dict
)
from app.schemas.card import TitleCard
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
    font_size: PositiveFloat | None = None
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

    extras: dict[str, Any] | None = None
    translations: dict[str, str] = {}

    @validator('template_ids', pre=False)
    def validate_unique_template_ids(cls, val):
        if len(val) != len(set(val)):
            raise ValueError('Template IDs must be unique')
        return val

"""
Update classes
"""
class UpdateEpisode(UpdateBase):
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
    font_size: PositiveFloat | None = UNSPECIFIED
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

    extra_keys: list[str] | None = UNSPECIFIED
    extra_values: list[Any] | None = UNSPECIFIED
    translations: dict[str, str] = UNSPECIFIED

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('extra_keys', 'extra_values', pre=True)
    def validate_list(cls, v):
        return [v] if isinstance(v, str) else v

    @validator('template_ids', pre=False)
    def validate_unique_template_ids(cls, val):
        if len(val) != len(set(val)):
            raise ValueError('Template IDs must be unique')
        return val

    @root_validator(pre=False)
    def convert_null_ids_to_empty_strings(cls, values):
        if 'emby_id' in values and values['emby_id'] is None:
            values['emby_id'] = ''
        if 'jellyfin_id' in values and values['jellyfin_id'] is None:
            values['jellyfin_id'] = ''
        return values

    @root_validator(pre=False)
    def validate_paired_lists(cls, values):
        return validate_argument_lists_to_dict(
            values, 'extras',
            'extra_keys', 'extra_values',
            output_key='extras',
        )

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
    series_id: int
    series: SeriesData
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
    font_size: PositiveFloat | None
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

    extras: dict[str, Any] | None
    translations: dict[str, str]
    cards: list[TitleCard]
