# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    FilePath,
    StringConstraints,
    model_validator,
)


# Default value to use for arguments in Update objects that accept None
UNSPECIFIED = '_UnspecifiedValue'

# Convert string to uppercase
UppercaseString = Annotated[str, BeforeValidator(lambda s: s.upper())]

MinimumLengthString = Annotated[
    str,
    Field(min_length=1),
    'Strings which must be at least 1 character long',
]

FontSize = Annotated[
    float,
    Field(gt=0.0),
    'Font sizes must be positive',
]

ShadowDefinition = Annotated[
    str,
    StringConstraints(to_lower=True, pattern=r'^\d+x\d+[+-]\d+[+-]\d+$'),
    'Shadow definitions must be in the format "85x10+10+10"',
]

# String that can be used as key in a dictionary
DictKey = Annotated[
    str,
    StringConstraints(pattern=r'^[a-zA-Z]+[^ -]*$')
]

# Match absolute ranges (1-10), season numbers (1), episode ranges (s1e1-s1e10)
SeasonTitleRange = Annotated[
    str,
    StringConstraints(pattern=r'^(\d+-\d+)|^(\d+)|^(s\d+e\d+-s\d+e\d+)$')
]

InterfaceType = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr', 'TMDb', 'TVDb']
ImageSource = Literal['Emby', 'Jellyfin', 'Plex', 'TMDb', 'TVDb']
MediaServer = Literal['Emby', 'Jellyfin', 'Plex']

# Pydantic base class
class Base(BaseModel):
    class Config:
        from_attributes = True

# Base class for all card type validators
class BaseCardModel(Base):
    """
    Base class for all card type validators which accept a source, and
    Card file; and support blurred and grayscale styling.
    """
    source_file: FilePath
    card_file: Path
    blur: bool = False
    grayscale: bool = False

class BaseCardTypeAllText(BaseCardModel):
    """
    Base class for all card type validators which have title, season,
    and episode text.
    """
    title_text: str
    season_text: UppercaseString
    episode_text: UppercaseString
    hide_season_text: bool = False
    hide_episode_text: bool = False

    @model_validator(mode='after')
    def toggle_text_hiding(self) -> Self:
        self.hide_season_text |= (len(self.season_text) == 0)
        self.hide_episode_text |= (len(self.episode_text) == 0)
        return self

class BaseCardTypeCustomFontAllText(BaseCardTypeAllText):
    """
    Base class for all card type validators which have title, season,
    and episode text; as well as all title Font customizations.
    """
    font_color: str
    font_file: FilePath
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_kerning: float = 1.0
    font_size: Annotated[float, Field(ge=0.0)] = 1.0
    font_stroke_width: float = 1.0
    font_vertical_shift: int = 0

class BaseCardTypeCustomFontNoText(BaseCardModel):
    """
    Base class for all card type validators which have no text
    attributes, but has all font customizations.
    """
    font_color: str
    font_file: FilePath
    font_interline_spacing: int = 0
    font_interword_spacing: int = 0
    font_kerning: float = 1.0
    font_size: Annotated[float, Field(ge=0.0)] = 1.0
    font_stroke_width: float = 1.0
    font_vertical_shift: int = 0
