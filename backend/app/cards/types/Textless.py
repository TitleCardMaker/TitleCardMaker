from pathlib import Path
from typing import Any

from pydantic import FilePath

from app.cards.base import BaseCardType, CardTypeDescription, DefaultCardConfig
from app.logging.logger import log # noqa: F401
from app.schemas.base import Base, BaseCardModel



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

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=(
            BaseCardType.BASE_REF_DIRECTORY / 'standard' / 'Sequel-Neue.otf'
        ),
        font_case='blank',
        font_color='',
        title_max_line_width=999,
        title_max_line_count=1,
        title_split_style='bottom',
        episode_text_format='',
        uses_source_images=True, # Keep as true
    )

    __slots__ = (
        'output_file',
        'source_file',
    )


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
        source_file: FilePath

    return CardModel
