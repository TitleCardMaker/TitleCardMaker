# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false, reportAssignmentType=false
from datetime import datetime
from json import loads
from re import sub as re_sub, IGNORECASE
from typing import Any, Self

from pydantic import (
    Field,
    PositiveInt,
    computed_field,
    field_validator,
    model_validator,
    root_validator,
)

from app.schemas.base import Base
from app.schemas.font import TitleCase
from app.schemas.series import Condition, SeasonTitleRange, Translation
from modules.CleanPath import CleanPath

"""
Base classes
"""
class ConfigBase(Base): # Base of Series, Episodes, and Templates
    font_id: int | None = None
    card_type: str | None = None
    hide_season_text: bool | None = None
    hide_episode_text: bool | None = None
    extra_keys: list[str] | None = Field(exclude=True, default=None)
    extra_values: list[Any] | None = Field(exclude=True, default=None)

    @computed_field
    def extras(self) -> dict[str, Any]:
        if self.extra_keys is None or self.extra_values is None:
            return {}

        return {
            key: value
            for key, value in zip(self.extra_keys, self.extra_values)
            if key and value
        }

"""
Creation classes
"""
class BlueprintSeries(ConfigBase):
    template_ids: list[int] = []
    match_titles: bool | None = None
    auto_split_title: bool | None = None
    font_color: str | None = None
    font_title_case: TitleCase | None = None
    font_size: float | None = None
    font_kerning: float | None = None
    font_stroke_width: float | None = None
    font_interline_spacing: int | None = None
    font_interword_spacing: int | None = None
    font_vertical_shift: int | None = None
    source_files: list[str] = []
    episode_text_format: str | None = None
    translations: list[Translation] | None = None
    season_title_ranges: list[SeasonTitleRange] | None = Field(exclude=True, default=None)
    season_title_values: list[str] | None = Field(exclude=True, default=None)
    skip_localized_images: bool | None = None

    @computed_field
    def season_titles(self) -> dict[SeasonTitleRange, str]:
        if self.season_title_ranges is None or self.season_title_values is None:
            return {}
        return {
            range: value
            for range, value in zip(
                self.season_title_ranges, self.season_title_values
            )
            if range and value
        }

class BlueprintEpisode(ConfigBase):
    template_ids: list[int] = []
    match_titles: bool | None = None
    auto_split_title: bool | None = None
    font_color: str | None = None
    font_title_case: TitleCase | None = None
    font_size: float | None = None
    font_kerning: float | None = None
    font_stroke_width: float | None = None
    font_interline_spacing: int | None = None
    font_interword_spacing: int | None = None
    font_vertical_shift: int | None = None
    title: str | None = None
    match_title: bool | None = None
    season_text: str | None = None
    episode_text: str | None = None

class BlueprintFont(Base):
    name: str
    color: str | None = None
    file: str | None = None
    kerning: float = None
    interline_spacing: int = None
    interword_spacing: int = None
    line_split_modifier: int = None
    replacements_in: list[str] = None
    replacements_out: list[str] = None
    size: float = None
    stroke_width: float = None
    title_case: TitleCase | None = None
    vertical_shift: int = None

class BlueprintTemplate(ConfigBase):
    name: str
    filters: list[Condition] = []
    episode_text_format: str | None = None
    translations: list[Translation] | None = None
    season_title_ranges: list[SeasonTitleRange] | None = Field(exclude=True, default=None)
    season_title_values: list[str] | None = Field(exclude=True, default=None)
    skip_localized_images: bool | None = None

    @computed_field
    def season_titles(self) -> dict[SeasonTitleRange, str]:
        if self.season_title_ranges is None or self.season_title_values is None:
            return {}
        return {
            range: value
            for range, value in zip(
                self.season_title_ranges, self.season_title_values
            )
            if range and value
        }

class Blueprint(Base):
    series: BlueprintSeries
    episodes: dict[str, BlueprintEpisode] = {}
    templates: list[BlueprintTemplate] = []
    fonts: list[BlueprintFont] = []
    previews: list[str] = []
    description: list[str] = []

"""
Update classes
"""

"""
Return classes
"""
class DownloadableFile(Base):
    url: str
    filename: str

class ExportBlueprint(Base):
    series: BlueprintSeries
    episodes: dict[str, BlueprintEpisode] = {}
    templates: list[BlueprintTemplate] = []
    fonts: list[BlueprintFont] = []

    @root_validator(skip_on_failure=True)
    def delete_null_args(cls, values: dict) -> dict:
        delete_keys = [key for key, value in values.items() if not value]
        for key in delete_keys:
            del values[key]

        return values

class ImportBlueprint(Blueprint):
    ...

class RemoteBlueprintFont(BlueprintFont):
    file_download_url: str | None = None

class RemoteBlueprintSeries(Base):
    name: str
    year: int
    imdb_id: str | None
    tmdb_id: int | None
    tvdb_id: int | None
    blueprint_count: PositiveInt = 1

class RemoteBlueprint(Base):
    id: int
    blueprint_number: int
    creator: str
    created: datetime
    series: RemoteBlueprintSeries
    json_: Blueprint = Field(alias='json')
    set_ids: list[int] = []

    @field_validator('json_', mode='before')
    @classmethod
    def parse_blueprint_json(cls, value: str) -> dict:
        return value if isinstance(value, dict) else loads(value)

    @model_validator(mode='after')
    def finalize_preview_urls(self) -> Self:
        # Remove illegal path characters
        full_name = f'{self.series.name} ({self.series.year})'
        clean_name = CleanPath.sanitize_name(full_name)

        # Remove prefix words like A/An/The
        sort_name = re_sub(r'^(a|an|the)(\s)', '', clean_name, flags=IGNORECASE)

        # Add base repo URL to all preview filenames
        self.json_.previews = [
            preview
            if preview.startswith('https://') else
            (
                f'https://github.com/CollinHeist/TCM-Blueprints-v2/raw'
                + f'/master/blueprints/{sort_name[0].upper()}/{clean_name}/'
                + f'{self.blueprint_number}/{preview}'
            )
            for preview in self.json_.previews
        ]

        return self

class RemoteBlueprintSet(Base):
    id: int
    name: str
    blueprints: list[RemoteBlueprint]
