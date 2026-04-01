from pathlib import Path
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import Field, FilePath, model_validator

from app.cards.base import (
    BaseCardType,
    CardTypeDescription,
    Coordinate,
    DefaultCardConfig,
    Extra,
    ImageMagickCommands,
    Rectangle,
    add_cli,
)
from app.interfaces.magick import Dimensions
from app.schemas.base import (
    BaseCardModel,
    BaseCardTypeCustomFontAllText,
    FontSize,
)


LinePosition = Literal['top', 'bottom']


class OverlineTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards featuring
    a thin line over (or under) the title text. This line is intersected
    by the episode text, and can be recolored.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Overline',
        identifier='overline',
        example='/public/cards/overline.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
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
                name='Line Color',
                identifier='line_color',
                description='Color of the line',
                tooltip='Default is to match the episode text or Font color.',
            ),
            Extra(
                name='Line Position',
                identifier='line_position',
                description='Position of the line and episode text',
                tooltip=(
                    'Either <v>top</v> or <v>bottom</v>. Default is <v>top</v>.'
                ),
                default='top',
            ),
            Extra(
                name='Line Width',
                identifier='line_width',
                description='Thickness of the line',
                tooltip=(
                    'Thickness of the line. Default is <v>9</v>. Unit is '
                    'pixels.'
                ),
                default=9,
            ),
            Extra(
                name='Line Toggle',
                identifier='hide_line',
                description='Whether to hide the line completely',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
                default='False',
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
                tooltip='Default is <v>-</v>.',
                default='-',
            ),
            Extra(
                name='Gradient Omission',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, text '
                    'may appear less legible on brighter images. Default is '
                    '<v>False</v>.'
                ),
                default='False',
            ),
        ],
        description=[
            'Simple Title Card with title and episode text at the bottom of '
            'image, and a thin line positioned above (or below) the title '
            'text.', 'The line (and episode text) can be repositioned and '
            'colored separately.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'overline'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=REF_DIRECTORY / 'HelveticaNeueMedium.ttf',
        font_color='white',
        title_max_line_width=30,
        title_max_line_count=2,
        title_split_style='bottom',
    )

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = CardConfig.font_color
    EPISODE_TEXT_FONT = (
        BaseCardType.BASE_REF_DIRECTORY
        / 'standard'
        / 'Proxima Nova Semibold.otf'
    )

    LINE_THICKNESS: Annotated[
        ClassVar[int],
        'How thick the line is (in pixels)'
    ] = 9

    """Gradient to overlay"""
    GRADIENT_IMAGE = REF_DIRECTORY / 'small_gradient.png'

    __slots__ = (
        'episode_text',
        'episode_text_color',
        'episode_text_font_size',
        'font_color',
        'font_file',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_kerning',
        'font_size',
        'font_stroke_width',
        'font_vertical_shift',
        'hide_episode_text',
        'hide_line',
        'hide_season_text',
        'line_color',
        'line_position',
        'line_width',
        'omit_gradient',
        'output_file',
        'season_text',
        'separator',
        'source_file',
        'title_text',
    )

    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = False,
            hide_episode_text: bool = False,
            font_color: str = CardConfig.font_color,
            font_file: str = str(CardConfig.font_file),
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            hide_line: bool = False,
            line_color: str = CardConfig.font_color,
            line_position: LinePosition = 'top',
            line_width: int = LINE_THICKNESS,
            omit_gradient: bool = False,
            separator: str = '-',
            **unused: Any,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.hide_line = hide_line
        self.line_color = line_color
        self.line_position = line_position
        self.line_width = line_width
        self.omit_gradient = omit_gradient
        self.separator = separator


    @property
    def gradient_commands(self) -> ImageMagickCommands:
        """Subcommand to add the gradient overlay to the image."""

        if self.omit_gradient:
            return []

        return [
            f'"{self.GRADIENT_IMAGE.resolve()}"',
            f'-composite',
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding title text to the image."""

        # No title text, or not being shown
        if len(self.title_text) == 0:
            return []

        # Position of the text is based on where the line is
        vertical_position = self.font_vertical_shift
        if self.line_position == 'top':
            vertical_position += 70
        else:
            vertical_position += 110

        # Use increased interline spacing for top line positioning
        if self.line_position == 'top':
            interline_spacing =  25 + self.font_interline_spacing
        else:
            interline_spacing = -25 + self.font_interline_spacing

        # Font characteristics
        size = 55 * self.font_size
        interword_spacing = 50 + self.font_interword_spacing
        kerning = -2 * self.font_kerning
        stroke_width = 5 * self.font_stroke_width

        return [
            f'-density 200',
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {size}',
            f'-strokewidth {stroke_width}',
            f'-stroke black',
            f'-kerning {kerning}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {interword_spacing}',
            f'-annotate +0+{vertical_position} "{self.title_text}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommands for adding index text to the source image."""

        # If not showing index text, return
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Set index text based on which text is hidden/not
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} {self.separator} {self.episode_text}'

        # Determine vertical position based on which element this text is
        vertical_shift = self.font_vertical_shift
        if self.line_position == 'top':
            vertical_shift += 232
        else:
            vertical_shift += 65

        return [
            f'-density 200',
            f'-gravity south',
            # f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-font "{self.REF_DIRECTORY.parent / "Proxima Nova Semibold.otf"}"',
            f'-fill "{self.episode_text_color}"',
            f'-strokewidth 2',
            f'-pointsize {22 * self.episode_text_font_size:.1f}',
            f'-interword-spacing 18',
            f'-kerning -2',
            f'-annotate +0+{vertical_shift} "{index_text}"'
        ]


    def line_commands(self,
            title_text_dimensions: Dimensions,
            index_text_dimensions: Dimensions,
        ) -> ImageMagickCommands:
        """
        Subcommands to add the over/underline to the image.

        Args:
            title_text_dimensions: Dimensions of the title text.
            index_text_dimensions: Dimensions of the index text.

        Returns:
            List of ImageMagick commands.
        """

        # Line is not being shown, skip
        if self.hide_line:
            return []

        # Determine starting vertical offset of the lines
        vertical_position = self.font_vertical_shift
        if self.line_position == 'top':
            vertical_position += 265
        else:
            vertical_position += 98
        vertical_position = self.HEIGHT - vertical_position

        # If index text is gone, draw singular rectangle
        if self.hide_season_text and self.hide_episode_text:
            right_rectangle = Rectangle(Coordinate(0, 0), Coordinate(0, 0))
            left_rectangle = Rectangle(
                Coordinate(
                    (self.WIDTH - title_text_dimensions.width) / 2 + 30,
                    vertical_position - (self.line_width / 2)
                ),
                Coordinate(
                    (self.WIDTH + title_text_dimensions.width) / 2 - 30,
                    vertical_position + (self.line_width / 2),
                )
            )
        else:
            # Create left rectangle
            left_rectangle = Rectangle(
                Coordinate(
                    (self.WIDTH - title_text_dimensions.width) / 2 + 30,
                    vertical_position - (self.line_width / 2),
                ),
                Coordinate(
                    (self.WIDTH - index_text_dimensions.width) / 2 - 10,
                    vertical_position + (self.line_width / 2),
                )
            )

            # Create right rectangle
            right_rectangle = Rectangle(
                Coordinate(
                    (self.WIDTH + index_text_dimensions.width) / 2 + 10,
                    vertical_position - (self.line_width / 2),
                ),
                Coordinate(
                    (self.WIDTH + title_text_dimensions.width) / 2 - 30,
                    vertical_position + (self.line_width / 2),
                )
            )

            # Draw nothing if either rectangle would invert or is too short
            if (left_rectangle.start.x > left_rectangle.end.x
                or right_rectangle.start.x > right_rectangle.end.x
                or left_rectangle.end.x - left_rectangle.start.x < 20
                or right_rectangle.end.x - right_rectangle.start.x < 20):
                return []

        return [
            f'-fill "{self.line_color}"',
            f'-stroke black',
            f'-strokewidth 2',
            left_rectangle.draw(),
            right_rectangle.draw(),
        ]


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Get the dimensions of the title and index text
        title_text_dimensions = self.image_magick.get_text_dimensions(
            self.title_text_commands,
        )
        index_text_dimensions = self.image_magick.get_text_dimensions(
            self.index_text_commands,
        )

        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add gradient overlay
            *self.gradient_commands,
            # Add text
            *self.title_text_commands,
            *self.index_text_commands,
            # Add line
            *self.line_commands(title_text_dimensions, index_text_dimensions),
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[BaseCardModel]:
    """Get the Pydantic validator class for this card type."""

    class CardModel(BaseCardTypeCustomFontAllText):
        font_color: str = OverlineTitleCard.CardConfig.font_color
        font_file: FilePath = OverlineTitleCard.CardConfig.font_file
        episode_text_color: str | None = None
        episode_text_font_size: FontSize = 1.0
        hide_line: bool = False
        line_color: str | None = None
        line_position: LinePosition = 'top'
        line_width: Annotated[
            int,
            Field(gt=0)
        ] = OverlineTitleCard.LINE_THICKNESS
        omit_gradient: bool = False
        separator: str = '-'

        @model_validator(mode='after')
        def assign_unassigned_color(self) -> Self:
            """Assign any unassigned colors to their default values."""

            if self.episode_text_color is None:
                self.episode_text_color = self.font_color
            if self.line_color is None:
                if self.episode_text_color is None:
                    self.line_color = self.font_color
                else:
                    self.line_color = self.episode_text_color

            return self

    return CardModel


add_cli(__name__, OverlineTitleCard, get_validator_model())
