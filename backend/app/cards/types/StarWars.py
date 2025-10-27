from pathlib import Path
from typing import Annotated, Any, Self

from pydantic import Field, FilePath, StringConstraints, model_validator

from app.cards.base import (
    BaseCardType,
    CardTypeDescription,
    DefaultCardConfig,
    Extra,
    ImageMagickCommands,
)
from app.schemas.base import BaseCardModel, BaseCardModel


class StarWarsTitleCard(BaseCardType):
    """
    This class describes a type of ImageMaker that produces title cards
    in the theme of Star Wars cards as designed by Reddit user
    /u/Olivier_286.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Star Wars',
        identifier='star wars',
        example='/public/cards/star wars.webp',
        creators=['/u/Olivier_286', 'CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=False,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color of the season and episode text',
                tooltip='Default is <c>#AB8630</c>.',
                default='#AB8630',
            ),
        ],
        description=[
            'Title cards intended for Star Wars (or really any space-themed) '
            'shows.', 'Similar to the Olivier title card, these cards feature '
            'left-aligned title and episode text', 'A star-filled gradient '
            'overlay is applied to the Source Image.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'star_wars'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=REF_DIRECTORY / 'Monstice-Base.ttf',
        font_color='#DAC960',
        font_case='upper',
        font_replacements={'Ō': 'O', 'ō': 'o'},
        title_max_line_width=16,
        title_max_line_count=5,
        title_split_style='top',
    )

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'EPISODE {to_cardinal(episode_number)}'
    EPISODE_TEXT_COLOR = '#AB8630'
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'HelveticaNeue.ttc'
    EPISODE_NUMBER_FONT = REF_DIRECTORY / 'HelveticaNeue-Bold.ttf'

    """Path to the reference star image to overlay on all source images"""
    __STAR_GRADIENT_IMAGE = REF_DIRECTORY / 'star_gradient.png'

    __slots__ = (
        'episode_text',
        'episode_text_color',
        'episode_prefix',
        'font_color',
        'font_file',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_kerning',
        'font_size',
        'font_vertical_shift',
        'hide_episode_text',
        'output_file',
        'source_file',
        'title_text',
    )

    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            episode_text: str,
            hide_episode_text: bool = False,
            font_color: str = CardConfig.font_color,
            font_file: str = str(CardConfig.font_file),
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            **unused: Any,
        ) -> None:
        """Initialize the CardType object."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store source and output file
        self.source_file = source_file
        self.output_file = card_file

        # Store episode title
        self.title_text = self.image_magick.escape_chars(title_text.upper())

        # Font customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Attempt to detect prefix text
        self.hide_episode_text = hide_episode_text
        if self.hide_episode_text:
            self.episode_prefix, self.episode_text = None, None
        else:
            if ' ' in episode_text:
                prefix, text = episode_text.upper().split(' ', 1)
                self.episode_prefix, self.episode_text = map(
                    self.image_magick.escape_chars,
                    (prefix, text)
                )
            else:
                self.episode_text = None
                self.episode_prefix = self.image_magick.escape_chars(
                    episode_text
                )

        # Extras
        self.episode_text_color = episode_text_color


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """Subcommands to add the episode title text to an image."""

        size = 124 * self.font_size
        interline_spacing = 20 + self.font_interline_spacing
        kerning = 0.5 * self.font_kerning
        vertical_shift = 829 + self.font_vertical_shift

        return [
            f'-font "{self.font_file}"',
            f'-gravity northwest',
            f'-pointsize {size}',
            f'-kerning {kerning:.1f}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-fill "{self.font_color}"',
            f'-annotate +320{vertical_shift:+} "{self.title_text}"',
        ]


    @property
    def episode_text_command(self) -> ImageMagickCommands:
        """Subcommands to add the episode text to an image."""

        # Hiding episode text, return blank command
        if self.hide_episode_text:
            return []

        return [
            # Global font options
            f'-gravity west',
            f'-pointsize 53',
            f'-kerning 19',
            f'+interword-spacing',
            f'-fill "{self.episode_text_color}"',
            f'-background transparent',
            # Create prefix text
            fr'\(',
                f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
                f'label:"{self.episode_prefix}"',
                # Create actual episode text
                f'-font "{self.EPISODE_NUMBER_FONT.resolve()}"',
                f'label:"{self.episode_text}"',
                # Combine prefix and episode text
                f'+smush 65',
            fr'\)',
            # Add combined text to image
            f'-geometry +325-140',
            f'-composite',
        ]


    def create(self) -> None:
        """Create the title card as defined by this object."""

        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles
            *self.resize_and_style,
            # Overlay star gradient
            f'"{self.__STAR_GRADIENT_IMAGE.resolve()}"',
            f'-composite',
            # Add title text
            *self.title_text_command,
            # Add episode text
            *self.episode_text_command,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[BaseCardModel]:
    """Get the Pydantic validator class for this card type."""

    # pyright: reportInvalidTypeForm=false
    class CardModel(BaseCardModel):
        title_text: str
        episode_text: Annotated[str, StringConstraints(to_upper=True)]
        hide_episode_text: bool = False
        font_color: str = StarWarsTitleCard.CardConfig.font_color
        font_file: FilePath = StarWarsTitleCard.CardConfig.font_file
        font_interline_spacing: int = 0
        font_interword_spacing: int = 0
        font_kerning: float = 1.0
        font_size: Annotated[float, Field(gt=0)] = 1.0
        font_vertical_shift: int = 0
        episode_text_color: str = StarWarsTitleCard.EPISODE_TEXT_COLOR

        @model_validator(mode='after')
        def toggle_text_hiding(self) -> Self:
            """Set the hide episode text flag if the episode text is blank"""

            self.hide_episode_text |= (len(self.episode_text) == 0)

            return self

    return CardModel
