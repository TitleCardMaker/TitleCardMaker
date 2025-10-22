from pathlib import Path
from typing import Any

from pydantic import FilePath

from app.logging.logger import log # noqa: F401
from app.schemas.base import Base, BaseCardModel
from app.cards.base import BaseCardType, CardTypeDescription



class TextlessTitleCard(BaseCardType):
    """
    This class describes a type of CardType that does not modify the
    source image in anyway, only optionally blurring it. No text of any
    kind is added.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Textless',
        identifier='textless',
        example='/public/cards/textless.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=False,
        supports_custom_seasons=False,
        supported_extras=[],
        description=[
            'A card completely devoid of all text.',
            'This card is intended to easily enable users to have TCM manage '
            'non-TCM-created cards, as well as apply style modifiers (like '
            'blurring and grayscale) to images.',
        ]
    )

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 999,
        'max_line_count': 1,
        'style': 'bottom',
    }

    """Font case for this card is entirely blank"""
    DEFAULT_FONT_CASE = 'blank'

    """Default episode text format string, can be overwritten by each class"""
    EPISODE_TEXT_FORMAT = ''

    """Characteristics of the default title font"""
    TITLE_FONT = ''
    TITLE_COLOR = ''
    FONT_REPLACEMENTS = {}

    """Don't require source images to work w/ importing"""
    USES_SOURCE_IMAGES = True # Set as False; if required then caught by model

    __slots__ = ('source_file', 'output_file')


    def __init__(self, *,
            source_file: Path | None,
            card_file: Path,
            blur: bool = False,
            grayscale: bool = False,
            **unused: Any,
        ) -> None:
        """Construct a new instance of this card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store input/output files
        self.source_file = source_file
        self.output_file = card_file


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        if (self.source_file
            and isinstance(self.source_file, Path)
            and self.source_file.exists()):
            add_source = [f'"{self.source_file.resolve()}"']
        else:
            add_source = [
                f'-size {self.TITLE_CARD_SIZE}',
                f'xc:None',
            ]

        self.image_magick.run([
            f'convert',
            *add_source,
            *self.resize_and_style,
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[Base]:
    """Get the Pydantic validator class for this card type."""

    class CardModel(BaseCardModel):
        source_file: FilePath # Optional source file for importing w/o sources

    return CardModel
