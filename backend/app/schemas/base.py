# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false
from pathlib import Path
from typing import Literal, Self

from pydantic import FilePath, PositiveFloat, constr, model_validator
from pydantic.main import BaseModel


# Default value to use for arguments in Update objects that accept None
UNSPECIFIED = '_UnspecifiedValue'

# String that can be used as key in a dictionary
DictKey = constr(pattern=r'^[a-zA-Z]+[^ -]*$', min_length=1)

InterfaceType = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr', 'TMDb', 'TVDb']
ImageSource = Literal['Emby', 'Jellyfin', 'Plex', 'TMDb', 'TVDb']
MediaServer = Literal['Emby', 'Jellyfin', 'Plex']

# Pydantic base class
class Base(BaseModel):
    class Config:
        orm_mode = True

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
    season_text: constr(to_upper=True)
    episode_text: constr(to_upper=True)
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
    font_size: PositiveFloat = 1.0
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
    font_size: PositiveFloat = 1.0
    font_stroke_width: float = 1.0
    font_vertical_shift: int = 0

# Base class for all "update" models
class UpdateBase(Base):
    pass

# Function to validate two equal length lists are provided
def validate_argument_lists_to_dict(
        field0: list[str] | None,
        field1: list[str] | None,
        allow_empty_strings: bool = False,
    ) -> dict[str, str] | None:
    """
    Validation function to join two paired lists into a dictionary.

    Args:
        field0: The first list of keys to use as the output dictionary
            keys.
        field1: The second list of values to use as the output
            dictionary values.
        allow_empty_strings: Whether `''` are permitted in the values.

    Returns:
        A dictionary of the two lists, or `None` if both are `None`.

    Raises:
        ValueError: Only one set of the provided values is a list, or if
            the two lists are not the equal length.
    """

    # Both fields are None, return None
    if field0 is None and field1 is None:
        return None

    if isinstance(field0, list) != isinstance(field1, list):
        raise ValueError('Both fields must be lists or omitted')

    # Both provided as lists - filter out unspecified values
    BAD_VALS = [UNSPECIFIED] + ([] if allow_empty_strings else [''])
    list0 = [in_ for in_ in field0 if in_ not in BAD_VALS]
    list1 = [out_ for out_ in field1 if out_ not in BAD_VALS]

    if len(list0) != len(list1):
        raise ValueError('Both fields must be the same length')

    return dict(zip(list0, list1))
