# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false, reportAssignmentType=false
from pathlib import Path
from typing import Literal

from pydantic import ( # pylint: disable=no-name-in-module
    NonNegativeFloat,
    PositiveFloat,
    constr,
    root_validator,
    validator,
)

from app.schemas.base import Base, UpdateBase, UNSPECIFIED


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
    size: NonNegativeFloat = 1.0
    stroke_width: float = 1.0
    title_case: TitleCase | None = None
    vertical_shift: int = 0

class BaseNamedFont(BaseFont):
    name: constr(min_length=1)

"""
Creation classes
"""
class NewNamedFont(BaseNamedFont):
    replacements_in: list[constr(min_length=1)] = []
    replacements_out: list[str] = []

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('replacements_in', 'replacements_out', pre=True)
    def validate_list(cls, v: str | list[str]) -> list[str]:
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values: dict) -> dict:
        if len(values['replacements_in']) != len(values['replacements_out']):
            raise ValueError('Must provide same number of in/out replacements')
        return values

class PreviewFont(Base):
    color: str | None = None
    kerning: float | None = None
    interline_spacing: int | None = None
    interword_spacing: int | None = None
    size: PositiveFloat | None = None
    stroke_width: float | None = None
    vertical_shift: int | None = None

"""
Update classes
"""
class UpdateNamedFont(UpdateBase):
    name: constr(min_length=1) = UNSPECIFIED
    color: str | None = UNSPECIFIED
    interline_spacing: int = UNSPECIFIED
    interword_spacing: int = UNSPECIFIED
    kerning: float = UNSPECIFIED
    line_split_modifier: int = UNSPECIFIED
    replacements_in: list[str] = UNSPECIFIED
    replacements_out: list[str] = UNSPECIFIED
    size: PositiveFloat = UNSPECIFIED
    stroke_width: float = UNSPECIFIED
    title_case: TitleCase | None = UNSPECIFIED
    vertical_shift: int = UNSPECIFIED

    @validator('*', pre=True)
    def validate_arguments(cls, v):
        return None if v == '' else v

    @validator('replacements_in', 'replacements_out', pre=True)
    def validate_list(cls, v: str | list[str]) -> list[str]:
        return [v] if isinstance(v, str) else v

    @root_validator
    def validate_paired_lists(cls, values):
        if len(values['replacements_in']) != len(values['replacements_out']):
            raise ValueError('Must provide same number of in/out replacements')
        return values

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
