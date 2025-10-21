from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import Field, FilePath, StringConstraints, model_validator

from app.schemas.base import Base, BaseCardTypeCustomFontNoText
from modules.BaseCardType import (
    BaseCardType,
    CardTypeDescription,
    Extra,
    ImageMagickCommands,
)


GradientType = Literal['original', 'improved']


class OlivierTitleCard(BaseCardType):
    """
    This class describes a type of ImageMaker that produces title cards
    in the style of those designed by Reddit user /u/Olivier_286.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Olivier',
        identifier='olivier',
        example='/public/cards/olivier.webp',
        creators=['/u/Olivier_286', 'CollinHeist', 'Yozora'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>white</c>.',
                default='white',
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Episode Text Vertical Shift',
                identifier='episode_text_vertical_shift',
                description='Vertical offset to apply to the episode text',
                tooltip='Default is <v>0</v>. Unit is pixels.',
                default=0,
            ),
            Extra(
                name='Text Stroke Color',
                identifier='stroke_color',
                description='Color to use for the text stroke',
                tooltip='Default is <c>black</c>.',
                default='black',
            ),
            Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, text '
                    'may appear less legible on brighter images. Default is '
                    '<v>True</v>.'
                ),
                default='True',
            ),
            Extra(
                name='Gradient Type',
                identifier='gradient_type',
                description='The type of gradient to overlay',
                tooltip=(
                    'Either <v>original</v>, <v>improved</v>, or a custom '
                    'ImageMagick command to create a gradient image which '
                    'starts with <v>command:</v>. See documentation for more '
                    'details. Default is <v>improved</v>.'
                ),
            ),
        ],
        description=[
            'Title card with left-aligned title and episode text.', 'This card '
            'is structurally very similar to the Star Wars card except it does '
            'not feature the star overlay.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'olivier'
    SW_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'star_wars'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 16,
        'max_line_count': 5,
        'style': 'top',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Montserrat-Bold.ttf').resolve())
    TITLE_COLOR = 'white'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'EPISODE {to_cardinal(episode_number)}'
    EPISODE_TEXT_COLOR = 'white'
    EPISODE_PREFIX_FONT = SW_REF_DIRECTORY / 'HelveticaNeue.ttc'
    EPISODE_NUMBER_FONT = SW_REF_DIRECTORY / 'HelveticaNeue-Bold.ttf'
    STROKE_COLOR = 'black'

    """Gradient image"""
    GRADIENT = REF_DIRECTORY.parent / 'overline' / 'small_gradient.png'
    _ALT_GRADIENT = REF_DIRECTORY / 'alt_gradient.png'

    __slots__ = (
        'episode_prefix',
        'episode_text',
        'episode_text_color',
        'episode_text_font_size',
        'episode_text_vertical_shift',
        'font_color',
        'font_file',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_kerning',
        'font_size',
        'font_stroke_width',
        'font_vertical_shift',
        'gradient_type',
        'hide_episode_text',
        'omit_gradient',
        'output_file',
        'stroke_color',
        'source_file',
        'title_text',
    )

    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            # Text
            title_text: str,
            episode_text: str,
            hide_episode_text: bool = False,
            # Font
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            # Builtins
            blur: bool = False,
            grayscale: bool = False,
            # Extras
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            episode_text_vertical_shift: int = 0,
            omit_gradient: bool = True,
            gradient_type: GradientType | str = 'improved',
            stroke_color: str = STROKE_COLOR,
            **unused: Any,
        ) -> None:
        """Construct a new instance of this card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store source and output file
        self.source_file = source_file
        self.output_file = card_file

        # Store attributes of the text
        self.title_text = self.image_magick.escape_chars(title_text)

        # Determine episode prefix, modify text to remove prefix
        self.episode_prefix = None
        self.hide_episode_text = hide_episode_text or len(episode_text) == 0
        if not self.hide_episode_text and ' ' in episode_text:
            prefix, number = episode_text.split(' ', 1)
            self.episode_prefix = prefix.upper()
            episode_text = number
        self.episode_text = self.image_magick.escape_chars(episode_text)

        # Font customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.omit_gradient = omit_gradient
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.episode_text_vertical_shift = episode_text_vertical_shift
        self.gradient_type = gradient_type
        self.stroke_color = stroke_color


    @property
    def gradient_commands(self) -> ImageMagickCommands:
        """
        Subcommand to overlay the gradient to this image. This rotates
        and repositions the gradient overlay based on the text position.
        """

        if self.omit_gradient:
            return []

        # Gradient image, append to image
        if self.gradient_type in ('original', 'improved'):
            if self.gradient_type == 'original':
                gradient_command =[f'"{self.GRADIENT.resolve()}"', '-rotate 90']
            else:
                gradient_command = [f'"{self._ALT_GRADIENT.resolve()}"']

            return [
                fr'\(',
                *gradient_command,
                fr'\)',
                f'-geometry -{(self.WIDTH - self.HEIGHT) / 2}+0',
                f'-composite',
            ]

        # Custom gradient definition, generate and append
        return [self.gradient_type.removeprefix('custom:')]


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """ImageMagick commands to add the title text."""

        font_size = 124 * self.font_size
        stroke_width = 8.0 * self.font_stroke_width
        kerning = 0.5 * self.font_kerning
        interline_spacing = -20 + self.font_interline_spacing
        vertical_shift = 785 + self.font_vertical_shift

        return [
            fr'\(',
            f'-font "{self.font_file}"',
            f'-gravity northwest',
            f'-pointsize {font_size}',
            f'-kerning {kerning}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
            f'-annotate +320+{vertical_shift} "{self.title_text}"',
            fr'\)',
            fr'\(',
            f'-fill "{self.font_color}"',
            f'-stroke "{self.font_color}"',
            f'-strokewidth 0',
            f'-annotate +320+{vertical_shift} "{self.title_text}"',
            fr'\)',
        ]


    @property
    def episode_prefix_command(self) -> ImageMagickCommands:
        """ImageMagick commands to add the episode prefix text."""

        # No episode prefix/text, return empty command
        if self.episode_prefix is None or self.hide_episode_text:
            return []

        size = 60 * self.episode_text_font_size
        kerning = 19 * self.episode_text_font_size
        stroke_width = 5 * self.episode_text_font_size
        vertical_shift = -150 + self.episode_text_vertical_shift

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_PREFIX_FONT.resolve()}"',
            f'-pointsize {size}',
            f'-kerning {kerning}',
            f'-fill black',
            f'-stroke black',
            f'-strokewidth {stroke_width}',
            f'-annotate +325{vertical_shift:+} "{self.episode_prefix}"',
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 0',
            f'-annotate +325{vertical_shift:+} "{self.episode_prefix}"',
        ]


    @property
    def episode_number_text_command(self) -> ImageMagickCommands:
        """ImageMagick commands to add the episode number text."""

        # No episode text, return empty command
        if self.hide_episode_text:
            return []

        # Vertical shift
        kerning = 19 * self.episode_text_font_size
        size = 60 * self.episode_text_font_size
        stroke_width = 7 * self.episode_text_font_size
        vertical_shift = -150 + self.episode_text_vertical_shift

        # Get variable horizontal offset based of episode prefix
        text_offset = {'EPISODE': 425, 'CHAPTER': 425, 'PART': 275}
        if self.episode_prefix is None:
            offset = 0
        elif self.episode_prefix in text_offset:
            offset = text_offset[self.episode_prefix] \
                * self.episode_text_font_size
        else:
            offset_per_char = text_offset['EPISODE'] / len('EPISODE')
            offset = offset_per_char * len(self.episode_prefix) * 1.10\
                * self.episode_text_font_size

        return [
            f'-gravity west',
            f'-font "{self.EPISODE_NUMBER_FONT.resolve()}"',
            f'-pointsize {size}',
            f'-kerning {kerning}',
            f'-fill black',
            f'-stroke black',
            f'-strokewidth {stroke_width}',
            f'-annotate +{325+offset}{vertical_shift:+} "{self.episode_text}"',
            f'-fill "{self.episode_text_color}"',
            f'-stroke "{self.episode_text_color}"',
            f'-strokewidth 1',
            f'-annotate {325+offset:+}{vertical_shift:+} "{self.episode_text}"',
        ]


    def create(self) -> None:
        """Create the title card as defined by this object."""

        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            *self.resize_and_style,
            # Overlay gradient
            *self.gradient_commands,
            # Add text
            *self.title_text_command,
            *self.episode_prefix_command,
            *self.episode_number_text_command,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[Base]:
    """Get the Pydantic validator class for this card type."""

    # pyright: reportInvalidTypeForm=false
    class CardModel(BaseCardTypeCustomFontNoText):
        title_text: str
        episode_text: Annotated[str, StringConstraints(to_upper=True)]
        hide_episode_text: bool = False
        font_color: str = OlivierTitleCard.TITLE_COLOR
        font_file: FilePath = OlivierTitleCard.TITLE_FONT # type: ignore
        episode_text_color: str = OlivierTitleCard.EPISODE_TEXT_COLOR
        episode_text_font_size: Annotated[float, Field(gt=0)] = 1.0
        episode_text_vertical_shift: int = 0
        gradient_type: (
            Annotated[str, StringConstraints(pattern=r'^custom:.*$')]
            | GradientType
        ) = 'improved'
        omit_gradient: bool = True
        stroke_color: str = OlivierTitleCard.STROKE_COLOR

        @model_validator(mode='after')
        def toggle_text_hiding(self) -> Self:
            """
            Set the hide episode text flag if the episode text is blank.
            """
            self.hide_episode_text |= (len(self.episode_text) == 0)
            return self

    return CardModel
