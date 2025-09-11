from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Literal, Union

from num2words import CONVERTER_CLASSES as SUPPORTED_LANGUAGE_CODES
from pydantic import (
    computed_field,
    constr,
    PositiveInt,
    field_validator,
    AnyUrl,
    FilePath,
    NonNegativeInt,
    StringConstraints,
)
from pydantic.fields import Field

from app.interfaces.tmdb import TMDbInterfaceV1
from app.magick.summary import StandardSummary, StylizedSummary
from app.schemas.base import Base
from app.yaml.sync import SeriesYamlWriter
from modules.BaseCardType import BaseCardType
from modules.FormatString import FormatString
from modules.RemoteCardType import RemoteCardTypeV1
from modules.TitleCard import TitleCard


ArchiveSummaryTypeOption = Literal['standard', 'stylized']
CardExtension = Literal['.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp']
EpisodeDataSourceOption = Literal['sonarr', 'emby', 'jellyfin', 'plex', 'tmdb']
FilesizeLimit = StringConstraints(
    pattern=r'^\d+\s+(Bytes|Kilobytes|Megabytes|B|Kb|KB|Mb|MB)$'
)
ImageSourceOption = Literal['tmdb', 'plex', 'emby', 'jellyfin']
LanguageCodeOption = Literal[*SUPPORTED_LANGUAGE_CODES.keys()]
Percentage = StringConstraints(pattern=r'^\d+\.?\d*%$')
Style = Literal[
    'art',
    'art blur',
    'art grayscale',
    'art blur grayscale',
    'unique',
    'blur',
    'blur unique',
    'grayscale unique',
    'blur grayscale unique',
]
TMDBLanguageOption = Literal[*TMDbInterfaceV1.LANGUAGE_CODES]

SyncExclusion = dict[
    Literal['series', 'tag', 'yaml'],
    constr(pattern=r'^.*\s*\(\d+\)$') | FilePath | str,
]

class OptionsYaml(Base):
    source: Path
    execution_mode: Literal['serial', 'batch'] = 'serial'
    series: list[Path]

    @field_validator('series', mode='before')
    @classmethod
    def coerce_to_list(cls, v: Any) -> list[Any]:
        return v if isinstance(v, list) else [v]

    card_type: str = 'standard'

    @field_validator('card_type', mode='after')
    @classmethod
    def validate_card_type(cls, v: str) -> str:
        if v in TitleCard.CARD_TYPES:
            return v
        if not RemoteCardTypeV1(v).valid:
            raise ValueError(f'Invalid card type "{v}"')
        return v

    @computed_field
    @cached_property
    def card_class(self) -> type[BaseCardType]:
        if self.card_type in TitleCard.CARD_TYPES:
            return TitleCard.CARD_TYPES[self.card_type]
        return RemoteCardTypeV1(self.card_type).card_class

    card_extension: CardExtension = '.jpg'
    card_dimensions: str = Field(default='1920x1080', pattern=r'^\d+x\d+$')

    @field_validator('card_dimensions', mode='after')
    @classmethod
    def validate_card_dimensions(cls, v: str) -> str:
        try:
            width, height = map(int, v.lower().split('x'))
            assert width > 0 and height > 0
            return v
        except ValueError:
            raise ValueError('Invalid card dimensions - specify as WIDTHxHEIGHT')
        except AssertionError:
            raise ValueError((
                'Invalid card dimensions - both dimensions must be larger than '
                '0px'
            ))

    filename_format: str = '{full_name} - S{season:02}E{episode:02}'

    @field_validator('filename_format', mode='after')
    @classmethod
    def validate_filename_format(cls, v: str) -> str:
        if not TitleCard.validate_card_format_string(v):
            raise ValueError('Invalid filename format')
        return v

    image_source_priority: list[ImageSourceOption] = Field(
        default=['tmdb', 'plex', 'emby', 'jellyfin'],
    )

    @field_validator('image_source_priority', mode='before')
    @classmethod
    def parse_isp(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.lower().strip().replace(' ', '').split(',')
        return v

    episode_data_source: EpisodeDataSourceOption = 'sonarr'
    season_folder_format: str = 'Season {season}'

    @field_validator('season_folder_format', mode='after')
    @classmethod
    def validate_season_folder_format(cls, v: str) -> str:
        if not FormatString(v, data={'season': 1}).valid:
            raise ValueError('Invalid season folder format')
        return v

    enable_specials: bool = True
    language_codes: list[LanguageCodeOption] = ['en']

    @field_validator('language_codes', mode='after')
    @classmethod
    def validate_language_codes(cls, v: list[str]) -> list[str]:
        if not all(code in SUPPORTED_LANGUAGE_CODES for code in v):
            raise ValueError('Invalid language codes')
        return v

class ArchiveSummaryYaml(Base):
    create: bool = True
    type: ArchiveSummaryTypeOption = 'stylized'
    created_by: str | None = None
    background: str | None = None
    summary_minimum_episode_count: int = Field(default=3, ge=1)
    ignore_specials: bool = False

class ArchiveYaml(Base):
    path: Path
    all_variations: bool = True
    summary: ArchiveSummaryYaml = ArchiveSummaryYaml()

class BaseSyncYaml(Base):
    file: Path
    mode: Literal['append', 'match'] = 'append'
    compact: bool = True
    volumes: dict[str, str] = {}
    add_template: str | None = None
    card_directory: Path | None = None
    exclusions: list[SyncExclusion] = []
    required_tags: list[str] = []

    @cached_property
    def sync_writer(self) -> SeriesYamlWriter:
        return SeriesYamlWriter(
            file=self.file,
            sync_mode=self.mode,
            compact_mode=self.compact,
            volume_map=self.volumes,
            template=self.add_template,
            card_directory=self.card_directory,
        )

class MediaServerSyncYaml(BaseSyncYaml):
    filter_libraries: list[str] = []

class SonarrSyncYaml(BaseSyncYaml):
    filter_libraries: dict[str, str] = {}
    monitored_only: bool = False
    downloaded_only: bool = False
    series_type: Literal['anime', 'daily', 'standard'] | None = None

class EmbyYaml(Base):
    url: str
    api_key: str
    username: str
    verify_ssl: bool = True
    filesize_limit: Annotated[str, FilesizeLimit] | None = None
    watched_style: Style = 'unique'
    unwatched_style: Style = 'unique'
    sync: list[MediaServerSyncYaml] = []

    @field_validator('sync', mode='before')
    @classmethod
    def coerce_to_list(cls, v: Any) -> list[Any]:
        return v if isinstance(v, list) else [v]

class JellyfinYaml(Base):
    url: str
    api_key: str
    username: str
    verify_ssl: bool = True
    filesize_limit: Annotated[str, FilesizeLimit] | None = None
    watched_style: Style = 'unique'
    unwatched_style: Style = 'unique'
    sync: list[MediaServerSyncYaml] = []

    @field_validator('sync', mode='before')
    @classmethod
    def coerce_to_list(cls, v: Any) -> list[Any]:
        return v if isinstance(v, list) else [v]

class PlexYaml(Base):
    url: str
    token: str
    verify_ssl: bool = True
    integrate_with_kometa: bool = False
    filesize_limit: Annotated[str, FilesizeLimit] | None = None
    timeout: int = Field(default=10, ge=1)
    watched_style: Style = 'unique'
    unwatched_style: Style = 'unique'
    sync: list[MediaServerSyncYaml] = []

    @field_validator('sync', mode='before')
    @classmethod
    def coerce_to_list(cls, v: Any) -> list[Any]:
        return v if isinstance(v, list) else [v]

class SonarrYaml(Base):
    url: str
    api_key: str
    verify_ssl: bool = True
    downloaded_only: bool = True
    sync: list[SonarrSyncYaml] = []

    @field_validator('sync', mode='before')
    @classmethod
    def coerce_to_list(cls, v: Any) -> list[Any]:
        return v if isinstance(v, list) else [v]

class TMDbYaml(Base):
    api_key: str
    retry_count: int = Field(default=3, ge=0)
    minimum_resolution: str = Field(default='800x400', pattern=r'^\d+x\d+$')
    skip_localized_images: bool = False
    logo_language_priority: list[TMDBLanguageOption] = ['en']

    @field_validator('logo_language_priority', mode='before')
    @classmethod
    def coerce_to_list(cls, v: Any) -> list[Any]:
        return v if isinstance(v, list) else [v]

class TautulliYaml(Base):
    url: AnyUrl
    api_key: str
    update_script: FilePath
    verify_ssl: bool = True
    username: str | None = None
    agent_name: str = 'Update TitleCardMaker'
    script_timeout: Annotated[int, PositiveInt] = 30

class ImagemagickYaml(Base):
    container: str | None = None

class PreferencesYaml(Base):
    options: OptionsYaml
    archive: ArchiveYaml | None = None
    emby: EmbyYaml | None = None
    jellyfin: JellyfinYaml | None = None
    plex: PlexYaml | None = None
    sonarr: list[SonarrYaml] = []
    tmdb: TMDbYaml | None = None
    tautulli: TautulliYaml | None = None
    imagemagick: ImagemagickYaml | None = None

    @field_validator('sonarr', mode='before')
    @classmethod
    def coerce_to_list(cls, v: Any) -> list[Any]:
        return v if isinstance(v, list) else [v]

    @computed_field
    @cached_property
    def summary_class(self) -> type[BaseCardType]:
        if self.archive.summary.type == 'standard':
            return StandardSummary
        return StylizedSummary

"""
Series YAML file definitions
"""

class LibraryYaml(Base):
    path: Path
    name: str | None = None
    media_server: Literal['emby', 'jellyfin', 'plex'] | None = None
    config: dict[str, Any] = {}

class FontYaml(Base):
    case: Literal['blank', 'lower', 'upper', 'source', 'title'] | None = None
    color: str | None = None
    delete_missing: bool = True
    file: FilePath | None = None
    kerning: Annotated[str, Percentage] = '100%'
    stroke_width: Annotated[str, Percentage] = '100%'
    interline_spacing: int = 0
    interword_spacing: int = 0
    replacements: dict[str, str] = {}
    size: Annotated[str, Percentage] = '100%'
    vertical_shift: int = 0

class SeasonPosterFontYaml(Base):
    file: FilePath | None = None
    color: str | None = None
    kerning: Annotated[str, Percentage] = '100%'
    size: Annotated[str, Percentage] = '100%'

class SeasonPosterYaml(Base):
    create: bool = True
    text_placement: Literal['top', 'bottom'] = 'top'
    logo_placement: Literal['top', 'bottom'] = 'top'
    omit_gradient: bool = False
    omit_logo: bool = False
    titles: Annotated[dict[int, str], dict[NonNegativeInt, str]] = {}
    font: SeasonPosterFontYaml | None = None

class TranslationYaml(Base):
    language: Annotated[
        str,
        StringConstraints(min_length=2, max_length=2, to_lower=True)
    ]
    key: Annotated[str, StringConstraints(min_length=1)]

class SeriesYaml(Base):
    name: str | None = None
    year: int | None = None
    episode_data_source: EpisodeDataSourceOption | None = None
    image_source_priority: list[ImageSourceOption] | None = None

    @field_validator('image_source_priority', mode='before')
    @classmethod
    def parse_isp(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.lower().strip().replace(' ', '').split(',')
        return v

    refresh_titles: bool = True
    library: str | None = None
    filename_format: str | None = None
    card_type: str | None = None

    @field_validator('card_type', mode='after')
    @classmethod
    def validate_card_type(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v in TitleCard.CARD_TYPES:
            return v
        if not RemoteCardTypeV1(v).valid:
            raise ValueError(f'Invalid card type "{v}"')
        return v

    episode_text_format: str | None = None
    disable_sonarr: bool = False
    disable_tmdb: bool = False
    enable_specials: bool | None = None
    skip_localized_images: bool = False
    watched_style: Style | None = None
    unwatched_style: Style | None = None
    directory: Path | None = None
    font: FontYaml | str | None = None
    season_posters: SeasonPosterYaml | None = None
    hide_season_text: bool | None = None
    season_text: Annotated[
        dict[int | str, str],
        Union[
            NonNegativeInt,
            StringConstraints(pattern=r'^s\d+e\d+-s\d+e\d+$'),
            StringConstraints(pattern=r'^\d+-\d+$'),
        ]
    ] = {}
    translations: list[TranslationYaml] = []

    @field_validator('translations', mode='before')
    @classmethod
    def coerce_to_list(cls, v: Any) -> list[Any]:
        return v if isinstance(v, list) else [v]

    ignore_preferred_titles: bool = False
    extras: dict[str, Any] = {}
    emby_id: Annotated[str, StringConstraints(pattern=r'^\d+$')] | None = None
    imdb_id: Annotated[str, StringConstraints(pattern=r'^tt\d+$')] | None = None
    jellyfin_id: str | None = None
    sonarr_id: Annotated[int, NonNegativeInt] | None = None
    tmdb_id: Annotated[int, NonNegativeInt] | None = None
    tvrage_id: Annotated[int, NonNegativeInt] | None = None
    tvdb_id: Annotated[int, NonNegativeInt] | None = None
    archive: bool = True
    archive_name: Annotated[str, StringConstraints(min_length=1)] | None = None
    archive_all_variations: bool | None = None
    archive_variations: list[dict[str, Any]] = []
    template: str | dict[str, Any] | None = None

    @field_validator('template', mode='after')
    @classmethod
    def validate_template(cls, v: str | dict[str, Any] | None) -> str | dict[str, Any] | None:
        if isinstance(v, dict) and 'name' not in v:
            raise ValueError('Missing template name')
        return v

class YamlFile(Base):
    libraries: dict[str, LibraryYaml] = {}
    fonts: dict[str, FontYaml] = {}
    templates: dict[str, dict[str, Any]] = {}
    series: dict[str, SeriesYaml] = {}
