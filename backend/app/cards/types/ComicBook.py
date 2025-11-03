from math import cos, sin, pi as PI
from pathlib import Path
from random import uniform
from re import match as re_match
from typing import Annotated, Any, Literal, Self

from pydantic import (
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
)
from app.schemas.base import BaseCardModel, BaseCardTypeCustomFontAllText


class SvgRectangle:
    """Class that defines a movable SVG rectangle."""

    def __init__(self, width: int | float, height: int | float) -> None:
        """
        Initialize this Rectangle object for a rectangle of the given
        dimensions.

        Args:
            width: Width of the rectangle.
            height: Height of the rectangle
        """

        self.width = width
        self.height = height
        self.center = Coordinate(0, 0)
        self.rotation = 0
        self.offset = Coordinate(0, 0)


    def rotate(self, angle_degrees: float = 0.0) -> 'SvgRectangle':
        """
        Set the rotation of this rectangle.

        Args:
            angle_degrees: Angle (in degrees) of the rotation to set.

        Returns:
            This object.
        """

        self.rotation = angle_degrees

        return self


    def shift_origin(self, origin: Coordinate) -> 'SvgRectangle':
        """
        Set the origin (for rotation and relative placement) of this
        Rectangle.

        Args:
            origin: Coordinates to set as this object's origin.

        Returns:
            This object.
        """

        self.center = origin

        return self


    @property
    def draw_commands(self) -> ImageMagickCommands:
        """
        Draw this rectangle with the necessary SVG ImageMagickCommands.

        Returns:
            List of ImageMagick commands to draw this rectangle.
        """

        start_position = Coordinate(
            -self.width / 2 + self.offset.x,
            -self.height / 2 + self.offset.y,
        )

        return [
            f'-draw "translate {self.center.as_svg}',
            f'rotate {self.rotation}',
            f'path \'M {start_position.as_svg}',
            f'l {self.width} 0',
            f'l 0 {self.height}',
            f'l {-self.width} 0',
            f'l 0 {-self.height}\' "',
        ]


class ComicBookTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards styled
    after a Comic Book panel. There are two banners - one for the title
    and one for the index text - on the top and bottom of the card.
    These panels can be rotated, recolored, and repositioned freely.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Comic Book',
        identifier='comic book',
        example='/public/cards/comic book.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>black</c>.',
                default='black',
            ),
            Extra(
                name='Index Text Position',
                identifier='index_text_position',
                description='Position of the index text on the top of the image',
                tooltip=(
                    'Either <v>left</v>, <v>middle</v>, or <v>right</v>. '
                    'Default is <v>left</v>.'
                ),
                default='left',
            ),
            Extra(
                name='Index Text Box Fill Color',
                identifier='episode_text_box_fill_color',
                description='Fill color of the text box for the episode text',
                tooltip='Default is to match the Title Text Box Fill Color.',
            ),
            Extra(
                name='Title Text Box Fill Color',
                identifier='text_box_fill_color',
                description='Fill color of the text box for the title text',
                tooltip='Default is <c>white</c>.',
                default='white',
            ),
            Extra(
                name='Index Text Rotation Angle',
                identifier='index_text_rotation_angle',
                description='Rotation of the index text',
                tooltip=(
                    'Can be any number, or specified like <v>random[lower, '
                    'upper]</v> for a random angle between <v>lower</v> and '
                    '<v>upper</v> to be chosen. Positive angles are tilted '
                    'down, negative tilted up. Default is <v>-4.0</v>. Unit is '
                    'degrees.'
                ),
                default=-4.0,
            ),
            Extra(
                name='Index Banner Vertical Shift',
                identifier='index_banner_shift',
                description=(
                    'Additional vertical shift to apply to the index text banner'
                ),
                tooltip=(
                    'Negative values shift the banner up, positive values '
                    'shift the banner down. Default is <v>0</v>. Unit is '
                    'pixels.'
                ),
                default=0,
            ),
            Extra(
                name='Hide Index Banner',
                identifier='hide_index_banner',
                description='Whether to hide the index text banner',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
                default='False',
            ),
            Extra(
                name='Text Box Edge Color',
                identifier='text_box_edge_color',
                description='Edge color of all text boxes',
                tooltip='Default is to match the Font color.',
            ),
            Extra(
                name='Title Text Rotation Angle',
                identifier='title_text_rotation_angle',
                description='Rotation of the title text',
                tooltip=(
                    'Can be any number, or specified like <v>random[lower, '
                    'upper]</v> for a random angle between <v>lower</v> and '
                    '<v>upper</v> to be chosen. Positive angles are tilted '
                    'down, negative tilted up. Default is <v>-4.0</v>. Unit is '
                    'degrees.'
                ),
                default=-4.0,
            ),
            Extra(
                name='Title Banner Vertical Shift',
                identifier='title_banner_shift',
                description=(
                    'Additional vertical shift to apply to the title text banner'
                ),
                tooltip=(
                    'Negative values shift the banner up, positive values '
                    'shift the banner down. Default is <v>0</v>. Unit is '
                    'pixels.'
                ),
                default=0,
            ),
            Extra(
                name='Hide Title Banner',
                identifier='hide_title_banner',
                description='Whether to hide the title text banner',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
                default='False',
            ),
            Extra(
                name='Banner Fill Color',
                identifier='banner_fill_color',
                description=(
                    'Fill color for both the title and episode text banners'
                ),
                tooltip='Default is <c>rgba(235,73,69,0.6)</c>.',
                default='rgba(235,73,69,0.6)',
            ),
        ],
        description=[
            'Title card styled after a comic book page.', 'The top and bottom '
            'of the card can each be individually colored, toggled, and angled.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'comic_book'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=REF_DIRECTORY / 'cc-wild-words-bold-italic.ttf',
        font_color='black',
        font_replacements={'é': 'e', 'É': 'E'},
        title_max_line_width=32,
        title_max_line_count=2,
        title_split_style='top',
    )

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = CardConfig.font_color
    EPISODE_TEXT_FONT = CardConfig.font_file

    """Implementation details"""
    BANNER_FILL_COLOR = 'rgba(235,73,69,0.6)'
    TEXT_BOX_WIDTH_MARGIN = 50
    TEXT_BOX_HEIGHT_MARGIN = 50
    TITLE_TEXT_VERTICAL_OFFSET = 125

    __slots__ = (
        'banner_fill_color',
        'episode_text',
        'episode_text_box_fill_color',
        'episode_text_color',
        'font_color',
        'font_file',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_kerning',
        'font_size',
        'font_vertical_shift',
        'hide_episode_text',
        'hide_index_banner',
        'hide_season_text',
        'hide_title_banner',
        'index_banner_shift',
        'index_text_rotation_angle',
        'index_text_position',
        'output_file',
        'text_box_fill_color',
        'text_box_edge_color',
        'title_text',
        'title_text_rotation_angle',
        'season_text',
        'source_file',
        'title_banner_shift',
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
            episode_text_color : str = EPISODE_TEXT_COLOR,
            index_text_position: Literal['left', 'middle', 'right'] = 'left',
            text_box_fill_color: str = 'white',
            episode_text_box_fill_color: str = 'white',
            text_box_edge_color: str | None = None,
            title_text_rotation_angle: float = -4.0,
            index_text_rotation_angle: float = -4.0,
            banner_fill_color: str = BANNER_FILL_COLOR,
            title_banner_shift: int = 0,
            index_banner_shift: int = 0,
            hide_title_banner: bool = False,
            hide_index_banner: bool = False,
            **unused: Any
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

        # Optional extras
        self.banner_fill_color = banner_fill_color
        self.episode_text_box_fill_color = episode_text_box_fill_color
        self.episode_text_color = episode_text_color
        self.hide_title_banner = hide_title_banner
        self.hide_index_banner = hide_index_banner
        self.index_banner_shift = index_banner_shift
        self.index_text_position = index_text_position
        self.index_text_rotation_angle = index_text_rotation_angle
        self.text_box_fill_color = text_box_fill_color
        self.text_box_edge_color = text_box_edge_color
        self.title_banner_shift = title_banner_shift
        self.title_text_rotation_angle = title_text_rotation_angle


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if not self.title_text:
            return []

        # Font characteristics
        font_size = 100 * self.font_size
        y_coordinate = self.TITLE_TEXT_VERTICAL_OFFSET +self.font_vertical_shift

        # String for the rotation of the title text
        rotation = (
            f'{self.title_text_rotation_angle}x{self.title_text_rotation_angle}'
        )

        return [
            f'-gravity south',
            f'-pointsize {font_size}',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-kerning {1 * self.font_kerning}',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-strokewidth 0',
            f'+stroke',
            f'-annotate {rotation}+0+{y_coordinate} "{self.title_text}"',
        ]


    @property
    def title_text_box_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text box."""

        # No index text, return empty commands
        if not self.title_text:
            return []

        # Get dimensions of the title text
        title_width, title_height = self.image_magick.get_text_dimensions(
            self.title_text_commands,
            interline_spacing=self.font_interline_spacing,
            line_count=len(self.title_text.splitlines()),
        )

        # Create the rectangle that will border the title text
        title_text_rectangle = SvgRectangle(
            title_width + self.TEXT_BOX_WIDTH_MARGIN,
            title_height + self.TEXT_BOX_HEIGHT_MARGIN,
        )

        # Rotate by given angle
        title_text_rectangle.rotate(self.title_text_rotation_angle)

        # Shift rectangle to placement of title text
        title_text_rectangle.shift_origin(
            Coordinate(
                self.WIDTH / 2,
                self.HEIGHT
                - self.TITLE_TEXT_VERTICAL_OFFSET
                - (title_height / 2)
            )
        )

        # Only drawing the text box, return that command
        if self.hide_title_banner:
            return [
                f'-gravity center',
                f'-fill "{self.text_box_fill_color}"',
                f'-stroke "{self.text_box_edge_color}"',
                f'-strokewidth 5',
                *title_text_rectangle.draw_commands,
            ]

        # Create bottom fill rectangle
        bottom_fill_rectangle = SvgRectangle(
            self.WIDTH * 2, # x/y Margin to account for rotation
            self.TITLE_TEXT_VERTICAL_OFFSET + 500
        )
        bottom_fill_rectangle.rotate(self.title_text_rotation_angle)
        bottom_fill_rectangle.shift_origin(
            Coordinate(
                self.WIDTH / 2,
                self.HEIGHT
                - self.TITLE_TEXT_VERTICAL_OFFSET
                - (title_height / 2)
                + (self.TITLE_TEXT_VERTICAL_OFFSET+500)/2
            )
        )
        bottom_fill_rectangle.offset = Coordinate(0, self.title_banner_shift)

        return [
            # Draw bottom fill rectangle
            f'-gravity center',
            f'-fill "{self.banner_fill_color}"',
            f'-stroke "{self.text_box_edge_color}"',
            f'-strokewidth 5',
            *bottom_fill_rectangle.draw_commands,
            # Add title text rectangle
            f'-gravity center',
            f'-fill "{self.text_box_fill_color}"',
            *title_text_rectangle.draw_commands,
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the index text."""

        # No index text, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Determine index text
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} {self.episode_text}'

        # Font characteristics
        font_size = 50 * self.font_size

        # Determine placement gravity and offset of the text
        y_coordinate = 75
        if self.index_text_position == 'left':
            gravity = 'northwest'
            x_coordinate = 35
        elif self.index_text_position == 'middle':
            gravity = 'north'
            x_coordinate = 0
        else:
            gravity = 'northeast'
            x_coordinate = 35

        # String for the rotation of the index text
        rotation = (
            f'{self.index_text_rotation_angle}x{self.index_text_rotation_angle}'
        )

        return [
            f'-gravity {gravity}',
            f'-pointsize {font_size}',
            f'-font "{self.font_file}"',
            f'-fill "{self.episode_text_color}"',
            f'+kerning',
            f'-strokewidth 0',
            f'+stroke',
            f'+interword-spacing',
            f'-annotate {rotation}+{x_coordinate}+{y_coordinate} "{index_text}"',
        ]


    @property
    def index_text_box_commands(self) -> ImageMagickCommands:
        """
        Subcommands required to add the index text box and the bottom
        fill rectangle.
        """

        # No index text, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Get dimensions of the index text
        index_width, index_height = self.image_magick.get_text_dimensions(
            self.index_text_commands,
        )

        # Create the rectangle that will border the index text
        index_text_rectangle = SvgRectangle(
            index_width + (self.TEXT_BOX_WIDTH_MARGIN / 2),
            index_height + (self.TEXT_BOX_HEIGHT_MARGIN / 2),
        )

        # Apply indicated rotation
        index_text_rectangle.rotate(self.index_text_rotation_angle)

        # Determine new origin of the index text based on placement location
        y_coordinate = 75 + (index_height / 2)
        if self.index_text_position == 'left':
            # The index text origin is 35px from the left of the image
            index_text_origin = Coordinate(35, y_coordinate)

            # Determine the offset to the center of the rotated index text
            angle = self.index_text_rotation_angle * PI / 180
            x = index_width / 2
            y = 0
            index_text_rectangle.offset = Coordinate(
                x * cos(angle) - y * sin(angle),
                (x * sin(angle) + y * cos(angle))/abs(self.index_text_rotation_angle),
            )
        elif self.index_text_position == 'middle':
            index_text_origin = Coordinate(self.WIDTH / 2 - 10, y_coordinate)
        else:
            index_text_origin = Coordinate(self.WIDTH - 35, y_coordinate)

            # Determine the offset to the center of the rotated index text
            angle = self.index_text_rotation_angle * PI / 180
            x = -index_width / 2
            y = 0
            index_text_rectangle.offset = Coordinate(
                x * cos(angle) - y * sin(angle),
                (x * sin(angle) + y * cos(angle))/abs(self.index_text_rotation_angle),
            )

        # Shift rectangle to placement of index text
        index_text_rectangle.shift_origin(index_text_origin)

        # If not drawing the banner, return only text rectangle
        if self.hide_index_banner:
            return [
                f'-gravity center',
                f'-fill "{self.episode_text_box_fill_color}"',
                f'-stroke "{self.text_box_edge_color}"',
                f'-strokewidth 5',
                *index_text_rectangle.draw_commands,
            ]

        index_fill_rectangle = SvgRectangle(
            self.WIDTH * 2, # x/y Margin to account for rotation
            75 + 500
        )
        index_fill_rectangle.rotate(self.index_text_rotation_angle)

        y_coordinate = 75 + (index_height / 2) - (75 + 500) / 2 \
            + self.index_banner_shift
        if self.index_text_position == 'left':
            index_fill_rectangle.shift_origin(Coordinate(
                35,
                y_coordinate
            ))
        elif self.index_text_position == 'middle':
            index_fill_rectangle.shift_origin(Coordinate(
                self.WIDTH / 2,
                y_coordinate,
            ))
        else:
            index_fill_rectangle.shift_origin(Coordinate(
                self.WIDTH - 35,
                y_coordinate,
            ))

        return [
            # Draw banner
            f'-fill "{self.banner_fill_color}"',
            f'-stroke "{self.text_box_edge_color}"',
            f'-strokewidth 5',
            *index_fill_rectangle.draw_commands,
            # Draw text
            f'-fill "{self.episode_text_box_fill_color}"',
            *index_text_rectangle.draw_commands,
        ]


    def create(self) -> None:
        """Create this object's defined Title Card."""

        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # # Draw title text rectangles
            *self.title_text_box_commands,
            # Draw index text rectangles
            *self.index_text_box_commands,
            # Draw text last because the -annotate position affects -draw commands
            # Add title text
            *self.title_text_commands,
            # Add index text
            *self.index_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[BaseCardModel]:
    """Get the Pydantic validator class for this card type."""

    RandomAngleRegex = r'random\[([+-]?\d+.?\d*),\s*([+-]?\d+.?\d*)\]'

    class CardModel(BaseCardTypeCustomFontAllText):
        font_color: str = ComicBookTitleCard.CardConfig.font_color
        font_file: FilePath = ComicBookTitleCard.CardConfig.font_file
        episode_text_color: str = ComicBookTitleCard.EPISODE_TEXT_COLOR
        index_text_position: Literal['left', 'middle', 'right'] = 'left'
        text_box_fill_color: str = 'white'
        episode_text_box_fill_color: str | None = None
        text_box_edge_color: str | None = None
        title_text_rotation_angle: (
            float | Annotated[str, StringConstraints(pattern=RandomAngleRegex)]
        ) = -4.0
        index_text_rotation_angle: (
            float | Annotated[str, StringConstraints(pattern=RandomAngleRegex)]
        ) = -4.0
        banner_fill_color: str = ComicBookTitleCard.BANNER_FILL_COLOR
        title_banner_shift: int = 0
        index_banner_shift: int = 0
        hide_title_banner: bool = False
        hide_index_banner: bool = False

        @field_validator(
            'title_text_rotation_angle',
            'index_text_rotation_angle',
            mode='after',
        )
        @classmethod
        def validate_random_angle(cls, value: str | float) -> float:
            """
            Validate the rotation angles. This verifies the randomized angles
            are valid, generates them if necessary, and limits all angles
            between 0 and 360 degrees.
            """

            # If angle is a random range string, replace with random value in range
            if isinstance(value, str):
                # Get bounds from the random range string
                lower, upper = map(
                    float,
                    re_match(RandomAngleRegex, value).groups() # type: ignore
                )

                # Lower bound cannot be above upper bound
                if lower >= upper:
                    raise ValueError(f'Lower bound must be below upper bound')

                return uniform(lower, upper) % 360

            return value % 360

        @model_validator(mode='after')
        def assign_unassigned_color(self) -> Self:
            """Assign any unassigned colors to their default values."""
            if self.text_box_edge_color is None:
                self.text_box_edge_color = self.font_color
            if self.episode_text_box_fill_color is None:
                self.episode_text_box_fill_color = self.text_box_fill_color
            return self

    return CardModel
