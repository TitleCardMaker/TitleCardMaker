# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false, reportAssignmentType=false, reportIncompatibleVariableOverride=false
from typing import Any, Literal

from pydantic import (
    conint,
    constr,
    Field,
    validator
)

from app.models.template import OPERATIONS, ARGUMENT_KEYS
from app.schemas.base import (
    Base,
    DictKey,
    MediaServer,
    SeasonTitleRange,
    UNSPECIFIED,
)
from app.schemas.connection import TMDbLanguageCode
from app.schemas.font import TitleCase
from app.schemas.ids import (
    EmbyID,
    IMDbID,
    JellyfinID,
    SonarrID,
    TMDbID,
    TVDbID,
    TVRageID
)
from app.schemas.preferences import Style

"""
Base classes
"""
Status = Literal['disabled', 'monitored', 'unmonitored']
FilterOperation = Literal[tuple(OPERATIONS.keys())]
FilterArgument = Literal[tuple(ARGUMENT_KEYS)]
SeriesOrder = Literal[
    'alphabetical', 'reverse-alphabetical',
    'cards', 'reverse-cards',
    'id', 'reverse-id',
    'sync',
    'year', 'reverse-year'
]

class Condition(Base):
    argument: FilterArgument
    operation: FilterOperation
    reference: str | None = None

class Translation(Base):
    language_code: TMDbLanguageCode
    data_key: DictKey

class MediaServerLibrary(Base):
    interface: MediaServer
    interface_id: int
    name: str

class BaseConfig(Base):
    font_id: int | None = None
    sync_specials: bool | None = None
    skip_localized_images: bool | None = None
    card_filename_format: str | None = None
    data_source_id: int | None = None
    card_type: str | None = None
    unwatched_style: Style | None = None
    watched_style: Style | None = None
    hide_season_text: bool | None = None
    hide_episode_text: bool | None = None
    episode_text_format: str | None = None
    image_source_priority: list[int] | None = None
    season_titles: dict[SeasonTitleRange, str] | None = None
    extras: dict[str, str] | None = None

    @validator('image_source_priority', pre=False)
    def validate_unique_isp_id(cls, val: list[int] | None) -> list[int] | None:
        if val is None:
            return val
        if len(val) != len(set(val)):
            raise ValueError('IDs must be unique')
        return val

class BaseTemplate(BaseConfig):
    name: constr(min_length=1)
    filters: list[Condition] = []
    translations: list[Translation] | None = None

class BaseSeries(BaseConfig):
    name: constr(min_length=1)
    year: conint(ge=1900)
    status: Status = 'monitored'
    template_ids: list[int] | None = None
    match_titles: bool = True
    auto_split_title: bool = True
    use_per_season_assets: bool = False
    translations: list[Translation] | None = None
    libraries: list[MediaServerLibrary] = []

    font_color: str | None = None
    font_title_case: TitleCase | None = None
    font_size: float | None = None
    font_kerning: float | None = None
    font_stroke_width: float | None = None
    font_interline_spacing: int | None = None
    font_interword_spacing: int | None = None
    font_vertical_shift: int | None = None

    emby_id: EmbyID = ''
    imdb_id: IMDbID = None
    jellyfin_id: JellyfinID = ''
    sonarr_id: SonarrID = ''
    tmdb_id: TMDbID = None
    tvdb_id: TVDbID = None
    tvrage_id: TVRageID = None
    set_url: str | None = None
    directory: str | None = None

class BaseUpdate(Base):
    name: constr(min_length=1) | None = UNSPECIFIED
    status: Status = UNSPECIFIED
    font_id: int | None = UNSPECIFIED
    sync_specials: bool | None = UNSPECIFIED
    skip_localized_images: bool | None = UNSPECIFIED
    card_filename_format: str | None = UNSPECIFIED
    data_source_id: int | None = UNSPECIFIED
    image_source_priority: list[int] | None = UNSPECIFIED
    translations: list[Translation] | None = UNSPECIFIED
    card_type: str | None = UNSPECIFIED
    hide_season_text: bool | None = UNSPECIFIED
    season_titles: dict[SeasonTitleRange, str] | None = UNSPECIFIED
    hide_episode_text: bool | None = UNSPECIFIED
    unwatched_style: Style | None = UNSPECIFIED
    watched_style: Style | None = UNSPECIFIED
    episode_text_format: str | None = UNSPECIFIED
    extras: dict[DictKey, str] | None = UNSPECIFIED

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('translations', pre=True)
    def validate_list(cls, v: str | list[str] | None) -> list[str] | None:
        # Filter out empty strings - all arguments can accept empty lists
        if v is None:
            return None

        return [val for val in ([v] if isinstance(v, str) else v) if val != '']

    @validator('image_source_priority', pre=False)
    def validate_unique_isp_ids(cls, val: list[int] | None) -> list[int] | None:
        if val is None:
            return val
        if len(val) != len(set(val)):
            raise ValueError('IDs must be unique')
        return val

"""
Creation classes
"""
class NewTemplate(BaseTemplate):
    name: str = Field(..., min_length=1)

class NewSeries(BaseSeries):
    sync_id: int | None = None

    @validator('template_ids', pre=False)
    def validate_unique_template_ids(cls, val: list[int]) -> list[int]:
        if len(val) != len(set(val)):
            raise ValueError('Template IDs must be unique')
        return val

"""
Update classes
"""
class UpdateTemplate(BaseUpdate):
    name: constr(min_length=1) = UNSPECIFIED
    filters: list[Condition] = UNSPECIFIED

class UpdateSeries(BaseUpdate):
    year: conint(ge=1900) = UNSPECIFIED
    directory: str | None = UNSPECIFIED
    template_ids: list[int] | None = UNSPECIFIED
    font_id: int | None = UNSPECIFIED
    sync_specials: bool | None = UNSPECIFIED
    skip_localized_images: bool | None = UNSPECIFIED
    use_per_season_assets: bool = UNSPECIFIED
    card_filename_format: str | None = UNSPECIFIED
    match_titles: bool = UNSPECIFIED
    auto_split_title: bool = UNSPECIFIED
    translations: list[Translation] | None = UNSPECIFIED
    libraries: list[MediaServerLibrary] = UNSPECIFIED

    card_type: str | None = UNSPECIFIED
    hide_season_text: bool | None = UNSPECIFIED
    hide_episode_text: bool | None = UNSPECIFIED
    unwatched_style: Style | None = UNSPECIFIED
    watched_style: Style | None = UNSPECIFIED
    episode_text_format: str | None = UNSPECIFIED

    font_color: str | None = UNSPECIFIED
    font_title_case: TitleCase | None = UNSPECIFIED
    font_size: float | None = UNSPECIFIED
    font_kerning: float | None = UNSPECIFIED
    font_stroke_width: float | None = UNSPECIFIED
    font_interline_spacing: int | None = UNSPECIFIED
    font_interword_spacing: int | None = UNSPECIFIED
    font_vertical_shift: int | None = UNSPECIFIED

    emby_id: EmbyID | None = UNSPECIFIED # Not actually optional
    imdb_id: IMDbID = UNSPECIFIED
    jellyfin_id: JellyfinID | None = UNSPECIFIED # Not actually optional
    sonarr_id: SonarrID | None = UNSPECIFIED # Not actually optional
    tmdb_id: TMDbID = UNSPECIFIED
    tvdb_id: TVDbID = UNSPECIFIED
    tvrage_id: TVRageID = UNSPECIFIED
    set_url: str | None = UNSPECIFIED

    @validator('template_ids', pre=False)
    def validate_unique_ids(cls, val):
        if len(val) != len(set(val)):
            raise ValueError('Template IDs must be unique')
        return val

class BatchUpdateSeries(Base):
    series_id: int
    update: UpdateSeries

"""
Return classes
"""
class SearchResult(Base):
    name: str
    year: int
    overview: list[str] = ['No overview available']
    poster: str | None = None
    ongoing: bool | None = None
    emby_id: str | None = None
    imdb_id: str | None = None
    jellyfin_id: str | None = None
    sonarr_id: str | None = None
    tmdb_id: int | None = None
    tvdb_id: int | None = None
    tvrage_id: int | None = None
    added: bool = False

class Template(BaseTemplate):
    id: int
    sort_name: str
    season_titles: dict[SeasonTitleRange, str]
    extras: dict[str, Any]

class Series(BaseSeries):
    id: int
    sync_id: int | None
    full_name: str
    sort_name: str
    # clean_name: str
    # poster_path: str | None
    poster_url: str
    small_poster_url: str | None
    episode_count: int
    card_count: int
    font_color: str | None
    font_title_case: TitleCase | None
    font_size: float | None
    font_kerning: float | None
    font_stroke_width: float | None
    font_interline_spacing: int | None
    font_interword_spacing: int | None
    font_vertical_shift: int | None
    season_titles: dict[SeasonTitleRange, str] | None
    extras: dict[str, Any] | None
    # Don't error on ID validation errors
    emby_id: Any
    imdb_id: Any
    jellyfin_id: Any
    sonarr_id: Any
    tmdb_id: Any
    tvdb_id: Any
    tvrage_id: Any

class SeriesOverview(Base):
    id: int
    name: str
    full_name: str
    sort_name: str
    year: int
    poster_url: str
    # small_poster_url: str
    libraries: list[MediaServerLibrary] = []
    status: Status

class SeriesOverviewWithCounts(Base):
    id: int
    name: str
    full_name: str
    sort_name: str
    year: int
    poster_url: str
    # small_poster_url: str
    libraries: list[MediaServerLibrary] = []
    episode_count: int
    card_count: int
    status: Status

class SeriesSearchResult(Base):
    id: int
    name: str
    year: int
    poster_url: str
