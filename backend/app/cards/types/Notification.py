from pathlib import Path
from re import match as re_match
from typing import Annotated, Any, Literal, Self

from pydantic import (
    Field,
    FilePath,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.cards.base import (
    BaseCardType,
    CardTypeDescription,
    Coordinate,
    DefaultCardConfig,
    Extra,
    ImageMagickCommands,
    ImageStack,
    Rectangle,
)
from app.schemas.base import (
    BaseCardModel,
    BaseCardTypeCustomFontAllText,
    FontSize,
)


Position = Literal['left', 'right']


class NotificationTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards which
    feature two compact rectangular frames styled to resemble a
    notification prompt. These "notifications" can be re-sized,
    positioned, and colored with extras.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Notification',
        identifier='notification',
        example='/public/cards/notification.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Edge Color',
                identifier='edge_color',
                description='Color of the edge of each notification box',
                tooltip='Default is <c>white</c>.',
                default='white',
            ),
            Extra(
                name='Edge Width',
                identifier='edge_width',
                description='How wide to make the edge coloring',
                tooltip='Number ><v>0</v>. Default is <v>5</v>. Unit is pixels.',
                default=5,
            ),
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
                name='Episode Text Vertical Shift',
                identifier='episode_text_vertical_shift',
                description=(
                    'Additional vertical shift to apply to the season and '
                    'episode text.'
                ),
                tooltip='Default is <v>0</v>. Unit is pixels.',
                default=0,
            ),
            Extra(
                name='Notification Background Color',
                identifier='glass_color',
                description='Background color of both text boxes',
                tooltip='Default is <c>rgba(0,0,0,0.50)</c>.',
                default='rgba(0,0,0,0.50)',
            ),
            Extra(
                name='Notification Position',
                identifier='position',
                description='Where to position the notifications',
                tooltip=(
                    'Either <v>left</v> or <v>right</v>. Default is '
                    '<v>right</v>.'
                ),
                default='right',
            ),
            Extra(
                name='Notification Box Adjustments',
                identifier='box_adjustments',
                description='Adjustments to the bounds of the notification',
                tooltip=(
                    'Specifiy as <v>{top} {right} {bottom} {left}</v> - e.g. '
                    '<v>-20 10 0 5</v>. Positive values move that face out, '
                    'negative values move the face in. Default is '
                    '<v>0 0 0 0</v>. Unit is pixels.'
                ),
                default='0 0 0 0',
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description=(
                    'Character that separates the season and episode text'
                ),
                tooltip='Default is <v>-</v>.',
                default='-',
            ),
        ],
        description=[
            'Card type featuring two compact rectangular frames styled to '
            'resemble a notification prompt.', 'These frames can be resized, '
            'positioned, and colored with extras.'
        ],
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'music'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=REF_DIRECTORY / 'Gotham-Bold.otf',
        font_color='white',
        font_case='source',
        title_max_line_width=28,
        title_max_line_count=4,
        title_split_style='bottom',
        episode_text_format='Episode {episode_number}',
    )

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = CardConfig.font_color
    EPISODE_TEXT_FONT = CardConfig.font_file

    """Implementation details"""
    EDGE_COLOR = CardConfig.font_color
    EDGE_WIDTH = 5
    GLASS_COLOR = 'rgba(0,0,0,0.50)'
    _GLASS_BLUR_PROFILE = '0x12'
    _TITLE_TEXT_Y_OFFSET = 215
    _TITLE_TEXT_MARGIN = 50
    _INDEX_TEXT_Y_OFFSET = 75
    _INDEX_TEXT_MARGIN = 45
    _TEXT_X_OFFSET = 35

    __slots__ = (
        'box_adjustments',
        'edge_color',
        'edge_width',
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
        'font_vertical_shift',
        'glass_color',
        'hide_season_text',
        'hide_episode_text',
        'output_file',
        'position',
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
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            box_adjustments: tuple[int, int, int, int] = (0, 0, 0, 0),
            edge_color: str = EDGE_COLOR,
            edge_width: int = EDGE_WIDTH,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            episode_text_vertical_shift: int = 0,
            glass_color: str = GLASS_COLOR,
            position: Position = 'right',
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
        self.font_vertical_shift = font_vertical_shift

        # Extras
        self.box_adjustments = box_adjustments
        self.edge_color = edge_color
        self.edge_width = edge_width
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.episode_text_vertical_shift = episode_text_vertical_shift
        self.glass_color = glass_color
        self.position: Position = position
        self.separator = separator


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if not self.title_text:
            return []

        gravity = 'southwest' if self.position == 'left' else 'southeast'
        y = self._TITLE_TEXT_Y_OFFSET + self.font_vertical_shift

        return [
            f'-gravity {gravity}',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {80 * self.font_size}',
            f'-interline-spacing {-10 + self.font_interline_spacing:+}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-kerning {1 * self.font_kerning}',
            f'-annotate {self._TEXT_X_OFFSET:+}{y:+}',
            f'"{self.title_text}"',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the season and episode text to the image.
        """

        # No index text, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Determine effective index text
        if self.hide_season_text:
            text = self.episode_text
        elif self.hide_episode_text:
            text = self.season_text
        else:
            text = f'{self.season_text} {self.separator} {self.episode_text}'

        gravity = 'southwest' if self.position == 'left' else 'southeast'
        y = self._INDEX_TEXT_Y_OFFSET + self.episode_text_vertical_shift

        return [
            f'-gravity {gravity}',
            f'-interline-spacing -10',
            f'-interword-spacing 0',
            f'-kerning 1',
            f'-pointsize {40 * self.episode_text_font_size}',
            f'-fill "{self.episode_text_color}"',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-annotate {self._TEXT_X_OFFSET:+}{y:+}',
            f'"{text}"',
        ]


    def get_glass_commands(self,
            text_commands: ImageMagickCommands,
            line_count: int,
            margin: int,
            y_offset: int,
            adjustments: tuple[int, int, int, int] = (0, 0, 0, 0),
        ) -> ImageMagickCommands:
        """
        Subcommands to add the "glass" effect to the image.

        Args:
            text_commands: Text commands to measure the dimensions of.
            line_count: Line count of the text.
            margin: Margin between the text and side of the glass.
            y_offset: How far from the bottom of the image the glass
                should be drawn.
            adjustments: Adjustments for the bounds of the glass.

        Returns:
            List of ImageMagick commands to draw the defined glass.
        """

        # Blank text commands, return
        if not text_commands:
            return []

        # Determine dimensions of the given text
        width, height = self.image_magick.get_text_dimensions(
            text_commands,
            interline_spacing=self.font_interline_spacing,
            line_count=line_count,
            density=100,
        )

        # How far the start x is from the side of the image
        x_offset = self._TEXT_X_OFFSET

        # Draw left-aligned rectangles
        if self.position == 'left':
            top_left = Coordinate(
                0 - adjustments[3],
                self.HEIGHT - y_offset - height - (margin / 3) - adjustments[0]
            )

            glass = Rectangle(
                top_left,
                Coordinate(
                    x_offset + width + margin + adjustments[1],
                    self.HEIGHT - y_offset + (margin / 3) + adjustments[2],
                )
            )

            edge = Rectangle(
                Coordinate(glass.end.x - self.edge_width, top_left.y),
                Coordinate(glass.end.x, glass.end.y)
            )
        # Draw right-aligned rectangles
        else:
            top_left = Coordinate(
                self.WIDTH - x_offset - width - margin - adjustments[3],
                self.HEIGHT - y_offset - height - (margin / 3) - adjustments[0],
            )

            glass = Rectangle(
                top_left,
                Coordinate(
                    self.WIDTH + adjustments[1],
                    self.HEIGHT - y_offset + (margin / 3) + adjustments[2]
                )
            )

            edge = Rectangle(
                top_left,
                Coordinate(
                    top_left.x + self.edge_width,
                    top_left.y + glass.height
                )
            )

        return [
            # Duplicate image to blur rectangle in the given bounds
            *ImageStack(
                f'-clone 0',
                f'-fill white',
                f'-colorize 100',
                f'-fill black',
                glass.draw(),
                f'-alpha off',
                f'-write mpr:mask',
                f'+delete',
            ),
            f'-mask mpr:mask',
            # Do not blur if whole image is being blurred
            f'' if self.blur else f'-blur {self._GLASS_BLUR_PROFILE}',
            f'+mask',
            # Draw glass shape
            f'-fill "{self.glass_color}"',
            glass.draw(),
            # Draw edge
            f'-fill "{self.edge_color}"',
            edge.draw(),
        ]


    def create(self) -> None:
        """Create this object's defined Title Card."""

        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            f'-density 100',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add background player glass
            *self.get_glass_commands(
                self.title_text_commands,
                len(self.title_text.splitlines()),
                self._TITLE_TEXT_MARGIN,
                y_offset=self._TITLE_TEXT_Y_OFFSET + self.font_vertical_shift,
                adjustments=self.box_adjustments,
            ),
            *self.get_glass_commands(
                self.index_text_commands,
                1,
                self._INDEX_TEXT_MARGIN,
                y_offset=(
                    self._INDEX_TEXT_Y_OFFSET + self.episode_text_vertical_shift
                ),
            ),
            # Add text
            *self.title_text_commands,
            *self.index_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[BaseCardModel]:
    """Get the Pydantic validator class for this card type."""

    BoxAdjustmentRegex = r'^([-+]?\d+)\s+([-+]?\d+)\s+([-+]?\d+)\s+([-+]?\d+)$'

    class CardModel(BaseCardTypeCustomFontAllText):
        season_text: str
        episode_text: str
        font_color: str = NotificationTitleCard.CardConfig.font_color
        font_file: FilePath = NotificationTitleCard.CardConfig.font_file
        box_adjustments: Annotated[
            str,
            StringConstraints(pattern=BoxAdjustmentRegex)
        ] | tuple[int, int, int, int] = (0, 0, 0, 0)
        edge_color: str | None = None
        edge_width: Annotated[int, Field(ge=0)] = NotificationTitleCard.EDGE_WIDTH
        episode_text_color: str | None = None
        episode_text_font_size: FontSize = 1.0
        episode_text_vertical_shift: int = 0
        glass_color: str = NotificationTitleCard.GLASS_COLOR
        position: Position = 'right'
        separator: str = '-'

        @field_validator('box_adjustments', mode='after')
        @classmethod
        def parse_box_adjustments(cls, value: str) -> tuple[int, int, int, int]:
            """Convert box adjustment strings to a tuple of integers"""

            return tuple(map(int, re_match(BoxAdjustmentRegex, value).groups()))

        @model_validator(mode='after')
        def assign_unassigned_color(self) -> Self:
            """Assign any unassigned colors to their default values."""

            if self.edge_color is None:
                self.edge_color = self.font_color
            if self.episode_text_color is None:
                self.episode_text_color = self.font_color

            return self

    return CardModel
