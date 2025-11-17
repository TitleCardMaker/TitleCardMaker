# pyright: reportInvalidTypeForm=false
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator, validator

from app.schemas.base import Base, MinimumLengthString, UNSPECIFIED


TitleCase = Literal['blank', 'lower', 'source', 'title', 'upper']

DefaultFont = {
    'font_interline_spacing': 0,
    'font_interword_spacing': 0,
    'font_kerning': 1.0,
    'font_line_split_modifier': 0,
    'font_size': 1.0,
    'font_stroke_width': 1.0,
    'font_vertical_shift': 0,
}

"""
Base classes
"""
class BaseFont(Base):
    color: str | None = None
    interline_spacing: int = 0
    interword_spacing: int = 0
    kerning: float = 1.0
    line_split_modifier: int = 0
    size: Annotated[float, Field(ge=0.0)] = 1.0
    stroke_width: float = 1.0
    title_case: TitleCase | None = None
    vertical_shift: int = 0

class BaseNamedFont(BaseFont):
    name: MinimumLengthString

"""
Creation classes
"""
class NewNamedFont(BaseNamedFont):
    replacements_in: list[MinimumLengthString] = []
    replacements_out: list[str] = []

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('replacements_in', 'replacements_out', pre=True)
    def validate_list(cls, v: str | list[str]) -> list[str]:
        return [v] if isinstance(v, str) else v

    @model_validator(mode='after')
    def validate_paired_lists(self) -> Self:
        if len(self.replacements_in) != len(self.replacements_out):
            raise ValueError('Must provide same number of in/out replacements')
        return self

class PreviewFont(Base):
    color: str | None = None
    kerning: float | None = None
    interline_spacing: int | None = None
    interword_spacing: int | None = None
    size: Annotated[float, Field(ge=0.0)] | None = None
    stroke_width: float | None = None
    vertical_shift: int | None = None

"""
Update classes
"""
class UpdateNamedFont(Base):
    id: int | None = None # This is never updated, but used for some ID matching
    name: MinimumLengthString = UNSPECIFIED
    color: str | None = UNSPECIFIED
    interline_spacing: int = UNSPECIFIED
    interword_spacing: int = UNSPECIFIED
    kerning: float = UNSPECIFIED
    line_split_modifier: int = UNSPECIFIED
    replacements_in: list[str] = UNSPECIFIED
    replacements_out: list[str] = UNSPECIFIED
    size: Annotated[float, Field(ge=0.0)] = UNSPECIFIED
    stroke_width: float = UNSPECIFIED
    title_case: TitleCase | None = UNSPECIFIED
    vertical_shift: int = UNSPECIFIED

    @model_validator(mode='after')
    def validate_paired_lists(self) -> Self:
        if len(self.replacements_in) != len(self.replacements_out):
            raise ValueError('Must provide same number of in/out replacements')
        return self

"""
Return classes
"""
class FontAnalysis(Base):
    replacements: dict[str, str] = {}
    missing: list[str] = []

class NamedFont(BaseNamedFont):
    id: int
    sort_name: str
    file: Path | None
    file_name: str | None
    replacements_in: list[str]
    replacements_out: list[str]
