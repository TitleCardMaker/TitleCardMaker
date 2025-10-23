from pathlib import Path
from random import random
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import Field, FilePath, StringConstraints, model_validator

from app.cards.base import (
    BaseCardType,
    CardTypeDescription,
    DefaultCardConfig,
    Extra,
    ImageMagickCommands,
)
from app.schemas.base import Base, BaseCardModel

TextSide = Literal['left', 'right']


class NegativeSpaceTitleCard(BaseCardType):
    """
    CardType that produces title cards featuring a large, prominent
    numeral on the side of the image with overlapping title text. The
    color of the numeral is inverted where the two texts overlap,
    showing the title in the negative space. All text can be recolored
    or adjusted independently via extras.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Negative Space',
        identifier='negative space',
        example='/public/cards/negative_space.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=False,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color of the season and episode text',
                tooltip='Default is to match the Font color.',
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the season and episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Episode Text Horizontal Shift',
                identifier='episode_text_horizontal_offset',
                description=(
                    'Additional horizontal shift to apply to the episode text.'
                ),
                tooltip='Default is <v>0</v>. Unit is pixels.',
                default=0,
            ),
            Extra(
                name='Episode Text Vertical Shift',
                identifier='episode_text_vertical_offset',
                description=(
                    'Additional vertical shift to apply to the episode text.'
                ),
                tooltip='Default is <v>0</v>. Unit is pixels.',
                default=0,
            ),
            Extra(
                name='Text Side',
                identifier='text_side',
                description='Which side to add all text to',
                tooltip=(
                    'Either <v>left</v>, <v>right</v>, or <v>random</v> (to '
                    'randomize for each Card). Default is <v>left</v>.'
                ),
                default='left',
            ),
            Extra(
                name='Title Text Horizontal Shift',
                identifier='title_text_horizontal_offset',
                description=(
                    'Additional horizontal shift to apply to the title text.'
                ),
                tooltip='Default is <v>0</v>. Unit is pixels.',
                default=0,
            ),
        ],
        description=[
            'Card type featuring a large, prominent numeral on the side of the '
            'image with overlapping title text. The color of the numeral is '
            'inverted where the two texts overlap, showing the title in the '
            'negative space. All text can be recolored or adjusted '
            'independently via extras.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'negative_space'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=REF_DIRECTORY / 'Futura.ttc',
        font_color='white',
        title_max_line_width=14,
        title_max_line_count=5,
        title_split_style='top',
        episode_text_format='{episode_number}',
    )

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = CardConfig.font_color
    EPISODE_TEXT_FONT = CardConfig.font_file

    """Implementation Details"""
    DEFAULT_TEXT_SIDE: ClassVar[TextSide] = 'left'

    __slots__ = (
        'episode_text',
        'episode_text_color',
        'episode_text_font_size',
        'episode_text_horizontal_offset',
        'episode_text_vertical_offset',
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
        'text_side',
        'title_text',
        'title_text_horizontal_offset',
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
            episode_text_font_size: float = 1.0,
            episode_text_horizontal_offset: int = 0,
            episode_text_vertical_offset: int = 0,
            text_side: TextSide | Literal['random'] = DEFAULT_TEXT_SIDE,
            title_text_horizontal_offset: int = 0,
            **unused: Any,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_episode_text = hide_episode_text

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = -55 + font_interline_spacing
        self.font_interword_spacing = 0 + font_interword_spacing
        self.font_kerning = 1.0 * font_kerning
        self.font_size = font_size
        self.font_vertical_shift = 0 + font_vertical_shift

        # Extras
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.episode_text_horizontal_offset = episode_text_horizontal_offset
        self.episode_text_vertical_offset = episode_text_vertical_offset
        self.title_text_horizontal_offset = title_text_horizontal_offset
        if text_side == 'random':
            text_side = 'left' if random() <= 0.5 else 'right'
        self.text_side: TextSide = text_side


    def title_text_commands(self,
            color: str | None = None,
        ) -> ImageMagickCommands:
        """
        Get the subcommand for adding the title text to the source
        image.

        Args:
            color: Override color for the title text.

        Returns:
            List of ImageMagick commands.
        """

        # No title text
        if not self.title_text:
            return []

        color = color or self.font_color
        gravity = 'west' if self.text_side == 'left' else 'east'

        # Determine x offset - use a custom offset based on the
        # outermost letter of the numeral
        offset = 125
        if not self.hide_episode_text:
            position = 0 if self.text_side == 'left' else -1
            offset = {
                '0': 350 - 325,
                '1': 350 - 240,
                '2': 350 - 300,
                '3': 350 - 300,
                '4': 350 - 250,
                '5': 350 - 275,
                '6': 350 - 325,
                '7': 350 - 275,
                '8': 350 - 290,
                '9': 350 - 325,
            }.get(self.episode_text[position], offset)
        offset += self.title_text_horizontal_offset

        return [
            f'-font "{self.font_file}"',
            f'-gravity {gravity}',
            f'-fill "{color}"',
            f'-pointsize {150 * self.font_size}',
            f'-kerning {self.font_kerning}',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-annotate {offset:+}{self.font_vertical_shift:+}',
            f'"{self.title_text}"',
        ]


    def numeral_commands(self, color: str | None = None) -> ImageMagickCommands:
        """
        Get the subcommand for adding the numeral text to the source
        image.

        Args:
            color: Override color for the numeral text.

        Returns:
            List of ImageMagick commands.
        """

        # If not showing numeral text, return
        if self.hide_episode_text:
            return []

        color = color or self.episode_text_color
        gravity = 'west' if self.text_side == 'left' else 'east'

        # Determine horizontal offset
        x = self.episode_text_horizontal_offset + {
            '0': 50,
            '1': -50,
            '4': 50,
            '5': 50,
            '7': 0 if self.text_side == 'left' else 25,
            '9': 50,
        }.get(self.episode_text[0 if self.text_side == 'left' else -1], 0)

        return [
            f'-font "{self.EPISODE_TEXT_FONT}"',
            f'-gravity {gravity}',
            f'-fill "{color}"',
            f'-pointsize {1250 * self.episode_text_font_size}',
            f'-kerning -125', # -150
            f'-annotate {x:+}{self.episode_text_vertical_offset:+}',
            f'"{self.episode_text}"',
        ]


    def create_text_image(self) -> Path:
        """
        Create the image containing the numeral and title text.

        Returns:
            Path to the created image. This is a temporary image which
            must be deleted afterwards.
        """

        # Get random filename for intermediate image
        image = self.image_magick.get_random_filename(self.source_file)

        self.image_magick.run([
            f'convert',
            f'-size "{self.TITLE_CARD_SIZE}"',
            f'xc:transparent',
            *self.numeral_commands(),
            *self.title_text_commands(),
            f'"{image.resolve()}"',
        ])

        return image


    def create_difference_mask(self) -> Path:
        """
        Create the difference mask in which the source image should be
        mapped to the white pixels, and the text mapped to the black.

        Returns:
            Path to the created image. This is a temporary image which
            must be deleted afterwards.
        """

        # Get random filename for intermediate image - this must be a
        # JPEG image for the mask to work
        image = self.image_magick.get_random_filename(
            self.source_file, extension='jpg'
        )

        # Create mask
        self.image_magick.run([
            f'convert',
            f'-size "{self.TITLE_CARD_SIZE}"',
            # First image is the filled number mask where white is the
            # episode number, and the background is black
            fr'\(',
                f'xc:black',
                *self.numeral_commands('white'),
            fr'\)',
            # Second image is the filled title mask where black is the
            # title text, and the background is white
            fr'\(',
                f'xc:white',
                *self.title_text_commands('black'),
            fr'\)',
            # Create difference composite mask of the two images
            f'-compose difference',
            f'-composite',
            f'"{image.resolve()}"',
        ])

        return image


    def create(self) -> None:
        """Create this object's defined Title Card."""

        # Masked Alpha Composition layers are ordered as:
        # [Replace Black Parts of Mask] | [Replace White Parts of Mask] | [Mask]

        # These are TemporaryPath objects which will be deleted
        text_image = self.create_text_image()
        difference_mask = self.create_difference_mask()

        self.image_magick.run([
            f'convert',
            # Layer 0 is the text
            f'"{text_image.resolve()}"',
            # Layer 1 is the source image
            fr'\(',
                f'"{self.source_file.resolve()}"',
                # Resize and apply styles to source image
                *self.resize_and_style,
            fr'\)',
            # Layer 2 is the mask
            f'"{difference_mask.resolve()}"',
            # Use masked alpha composition to combine images
            f'-composite',
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.delete_intermediate_images(
            text_image, difference_mask
        )


def get_validator_model() -> type[Base]:
    """Get the Pydantic validator class for this card type."""

    # pyright: reportInvalidTypeForm=false
    class CardModel(BaseCardModel):
        title_text: str
        episode_text: Annotated[str, StringConstraints(to_upper=True)]
        hide_episode_text: bool = False
        font_color: str = NegativeSpaceTitleCard.CardConfig.font_color
        font_file: FilePath = NegativeSpaceTitleCard.CardConfig.font_file
        font_interline_spacing: int = 0
        font_interword_spacing: int = 0
        font_size: Annotated[float, Field(gt=0)] = 1.0
        font_vertical_shift: int = 0
        episode_text_color: str | None = None
        episode_text_font_size: Annotated[float, Field(gt=0)] = 1.0
        episode_text_horizontal_offset: int = 0
        episode_text_vertical_offset: int = 0
        text_side: (
            TextSide | Literal['random']
        ) = NegativeSpaceTitleCard.DEFAULT_TEXT_SIDE
        title_text_horizontal_offset: int = 0

        @model_validator(mode='after')
        def toggle_text_hiding(self) -> Self:
            """
            Set the hide episode text flag if the episode text is empty.
            """
            self.hide_episode_text |= (len(self.episode_text) == 0)
            return self

        @model_validator(mode='after')
        def assign_unassigned_color(self) -> Self:
            """Assign any unassigned colors to their default values."""
            if self.episode_text_color is None:
                self.episode_text_color = self.font_color
            return self

    return CardModel
