from pathlib import Path
from typing import Any, Literal, Self

from pydantic import FilePath, model_validator

from app.schemas.base import BaseCardModel, BaseCardTypeCustomFontAllText
from app.cards.base import (
    BaseCardType,
    CardTypeDescription,
    DefaultCardConfig,
    Extra,
    ImageMagickCommands,
)


TextGravity = Literal['center', 'east', 'west']
TitleTextPosition = Literal['left', 'right']
TextPosition = Literal[
    'upper left', 'upper right', 'right', 'lower right', 'lower left', 'left',
]


class DividerTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards
    similar to the AnimeTitleCard (same font), but featuring a vertical
    divider between the season and episode text. This card allows the
    positioning of text on the image to be adjusted. The general design
    was inspired by the title card interstitials in Overlord (season 3).
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Divider',
        identifier='divider',
        example='/public/cards/divider.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Text Gravity',
                identifier='text_gravity',
                description='Alignment of the index text (relative to itself)',
                tooltip=(
                    'Either <v>center</v>, <v>east</v>, or <v>west</v>. '
                    'Default is based on the specified Title Text Position '
                    '(i.e. <v>left</v> is <v>west</v>; <v>right</v> is '
                    '<v>east</v>).'
                ),
            ),
            Extra(
                name='Text Stroke Color',
                identifier='stroke_color',
                description='Color to use for the text stroke',
                tooltip='Default is <c>black</c>.',
                default='black',
            ),
            Extra(
                name='Title Text Side',
                identifier='title_text_position',
                description=(
                    'Which side the title text should be positioned relative '
                    'to the index text'
                ),
                tooltip=(
                    'Either <v>left</v>, or <v>right</v>. Default is '
                    '<v>left</v>.'
                ),
                default='left',
            ),
            Extra(
                name='Text Position',
                identifier='text_position',
                description='Where on the image to position the text',
                tooltip=(
                    'Either <v>upper left</v>, <v>upper right</v>, '
                    '<v>right</v>, <v>lower right</v>, <v>lower left</v>, or '
                    '<v>left</v>. Default is <v>lower right</v>.'
                ),
                default='lower right',
            ),
            Extra(
                name='Divider Color',
                identifier='divider_color',
                description='Color of the divider bar between text',
                tooltip='Default is to match the Font color.',
            )
        ],
        description=[
            'A simple title card featuring the title and index text separated '
            'by a vertical divider.', 'This card allows the text to be '
            'positioned at various points around the image.', 'Text on this '
            'image is unobtrusive, and is intended for shorter titles.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'anime'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=REF_DIRECTORY / 'Flanker Griffo.otf',
        font_color='white',
        font_case='source',
        font_replacements={'♡': '', '☆': '', '✕': 'x'},
        title_max_line_width=18,
        title_max_line_count=4,
        title_split_style='bottom',
        episode_text_format='Episode {episode_number}',
    )

    __slots__ = (
        'divider_color',
        'episode_text',
        'font_color',
        'font_file',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_kerning',
        'font_size',
        'font_stroke_width',
        'hide_season_text',
        'hide_episode_text',
        'output_file',
        'season_text',
        'source_file',
        'stroke_color',
        'text_position',
        'font_vertical_shift',
        'text_gravity',
        'title_text',
        'title_text_position',
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
            stroke_color: str = 'black',
            divider_color: str = CardConfig.font_color,
            text_gravity: TextGravity | None = None,
            title_text_position: TitleTextPosition = 'left',
            text_position: TextPosition = 'lower right',
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
        self.divider_color = divider_color
        self.stroke_color = stroke_color
        self.text_gravity = text_gravity
        self.title_text_position = title_text_position
        self.text_position = text_position


    @property
    def index_text_command(self) -> ImageMagickCommands:
        """Subcommand for adding the index text to the source image."""

        if self.text_gravity:
            gravity = self.text_gravity
        else:
            gravity = 'west' if self.title_text_position == 'left' else 'east'

        # Hiding all index text, return empty command
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Hiding season or episode text, only add that and divider bar
        if self.hide_season_text or self.hide_episode_text:
            text = self.episode_text if self.hide_season_text else self.season_text
            return [
                f'-gravity {gravity}',
                f'-pointsize {100 * self.font_size}',
                f'label:"{text}"',
            ]

        # Showing all text, add all text and divider
        return [
            f'-gravity {gravity}',
            f'-pointsize {100 * self.font_size}',
            f'label:"{self.season_text}\n{self.episode_text}"',
        ]


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """Subcommand for adding the title text to the source image."""

        # No title text, return blank commands
        if not self.title_text:
            return []

        gravity = 'east' if self.title_text_position == 'left' else 'west'

        return [
            f'-gravity {gravity}',
            f'-pointsize {100 * self.font_size}',
            f'label:"{self.title_text}"',
        ]


    @property
    def divider_height(self) -> int | float:
        """
        The height of the divider between the index and title text. This
        is calculated based on the maximum of the height of the index
        and title text. 0 is returned if a divider is not needed.
        """

        # No need for divider if either text is hidden, return 0
        if (len(self.title_text) == 0
            or (self.hide_season_text and self.hide_episode_text)):
            return 0

        index_text_line_count = (
            1 if self.hide_episode_text or self.hide_season_text else 2
        )

        return max(
            # Height of the index text
            self.image_magick.get_text_dimensions(
                [
                    f'-font "{self.font_file}"',
                    f'-interline-spacing {self.font_interline_spacing}',
                    *self.index_text_command,
                ],
                interline_spacing=self.font_interline_spacing,
                line_count=index_text_line_count,
            )[1],
            # Height of the title text
            self.image_magick.get_text_dimensions(
                [
                    f'-font "{self.font_file}"',
                    f'-interline-spacing {self.font_interline_spacing}',
                    *self.title_text_command,
                ],
                interline_spacing=self.font_interline_spacing,
                line_count=len(self.title_text.splitlines()),
            )[1]
        )


    def divider_command(self,
            divider_height: int | float,
            color: str,
        ) -> ImageMagickCommands:
        """
        Subcommand to add the dividing rectangle to the image.

        Args:
            divider_height: Height of the divider to create.
            color: Color to create the divider in.

        Returns:
            List of ImageMagick commands.
        """

        # No need for divider, use blank command
        if (not self.title_text
            or (self.hide_season_text and self.hide_episode_text)):
            return []

        return [
            fr'\(',
                f'-size 7x{divider_height-25}',
                f'xc:"{color}"',
            fr'\)',
            f'+size',
            f'-gravity center',
            f'+smush 25',
        ]


    def text_command(self,
            divider_height: int | float,
            is_stroke_text: bool,
        ) -> ImageMagickCommands:
        """
        Subcommand to add all text - index, title, and the divider - to
        the image.

        Args:
            divider_height: Height of the divider to create.
            is_stroke_text: Whether this text command is for the stroke
                text. This informs which color is used for the divider.

        Returns:
            List of ImageMagick commands.
        """

        divider_color = (
            self.stroke_color if is_stroke_text else self.divider_color
        )

        # Title on left, add text as: title divider index
        if self.title_text_position == 'left':
            return [
                *self.title_text_command,
                *self.divider_command(divider_height, divider_color),
                *self.index_text_command,
            ]

        # Title on right, add text as index divider title
        return [
            *self.index_text_command,
            *self.divider_command(divider_height, divider_color),
            *self.title_text_command,
        ]


    def create(self) -> None:
        """Create this object's defined Title Card."""

        interline_spacing = -20 + self.font_interline_spacing
        kerning = -0.5 * self.font_kerning
        stroke_width = 8 * self.font_stroke_width

        # The gravity of the text composition is based on the text position
        gravity = {
            'upper left':  'northwest',
            'upper right': 'northeast',
            'right':       'east',
            'lower right': 'southeast',
            'lower left':  'southwest',
            'left':        'west',
        }[self.text_position]

        # Get the height for the divider character based on the max text height
        divider_height = self.divider_height

        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add blurred stroke behind the title text
            f'-background transparent',
            f'-bordercolor transparent',
            f'-font "{self.font_file}"',
            f'-kerning {kerning}',
            f'-strokewidth {stroke_width}',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            fr'\(',
                f'-stroke "{self.stroke_color}"',
                *self.text_command(divider_height, is_stroke_text=True),
                # Combine text images
                f'+smush 25',
                # Add border so the blurred text doesn't get sharply cut off
                f'-border 50x{50+self.font_vertical_shift}',
                f'-blur 0x5',
            fr'\)',
            # Overlay blurred text in correct position
            f'-gravity {gravity}',
            f'-composite',
            # Add title text
            fr'\(',
                f'-fill "{self.font_color}"',
                # Use basically transparent color so text spacing matches
                f'-stroke "rgba(1, 1, 1, 0.01)"',
                *self.text_command(divider_height, is_stroke_text=False),
                f'+smush 25',
                f'-border 50x{50+self.font_vertical_shift}',
            fr'\)',
            # Overlay title text in correct position
            f'-gravity {gravity}',
            f'-composite',
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[BaseCardModel]:
    """Get the Pydantic validator class for this card type."""

    class CardModel(BaseCardTypeCustomFontAllText):
        season_text: str
        episode_text: str
        font_color: str = DividerTitleCard.CardConfig.font_color
        font_file: FilePath = DividerTitleCard.CardConfig.font_file
        stroke_color: str = 'black'
        divider_color: str | None = None
        text_gravity: TextGravity | None = None
        title_text_position: TitleTextPosition = 'left'
        text_position: TextPosition = 'lower right'

        @model_validator(mode='after')
        def assign_unassigned_color(self) -> Self:
            """Assign any unassigned colors to their default values."""

            if self.divider_color is None:
                self.divider_color = self.font_color

            return self

    return CardModel
