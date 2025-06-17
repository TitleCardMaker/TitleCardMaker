from pathlib import Path
from random import choice as random_choice
from typing import Any, Literal, TYPE_CHECKING, Self

from pydantic import PositiveFloat, model_validator

from app.schemas.base import Base, BaseCardTypeAllText
from modules.BaseCardType import (
    BaseCardType,
    CardDescription,
    Coordinate,
    ImageMagickCommands,
    Extra,
)
from app.logging.logger import log  # noqa: F401

if TYPE_CHECKING:
    from modules.preferences import Preferences
    from modules.Font import Font


VerticalPosition = Literal['top', 'center', 'bottom', 'random']


class SkeletonCrewTitleCard(BaseCardType):
    """
    CardType that produces title cards intended for the "Star Wars: 
    Skeleton Crew" series. Uses custom fonts to create the shows text
    and borders just like the shows logo and poster.
    """

    API_DETAILS = CardDescription(
        name='Skeleton Crew',
        identifier='skeleton crew',
        example='/public/cards/skeleton_crew.webp',
        creators=['Supremicus'],
        source='builtin',
        supports_custom_fonts=False,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to use for the episode text',
                tooltip='Default is <c>transparent</c>.',
                default='transparent',
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the season and episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Outline Color',
                identifier='outline_color',
                description='Color of the outline border',
                tooltip='Default is to match the title color.',
            ),
            Extra(
                name='Outline Width',
                identifier='outline_width',
                description='Width of the outline border',
                tooltip='Number ><v>0</v>. Default is <v>16</v>. Unit is pixels.',
                default=16,
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
                tooltip='Default is <v>•</v>.',
                default='•',
            ),
            Extra(
                name='Stroke Color',
                identifier='stroke_color',
                description='Color of the stroke used for the title text',
                tooltip='Default is <c>transparent</c> (no stroke).',
                default='transparent',
            ),
            Extra(
                name='Text Vertical Position',
                identifier='vertical_position',
                description='Position of all text',
                tooltip=(
                    'Either <v>top</v>, <v>center</v>, <v>bottom</v>, or '
                    '<v>random</v> to randomly select a position. Default is '
                    '<v>bottom</v>.'
                ),
                default='bottom',
            ),
        ],
        description=[
            'Title card intended for the "Star Wars: Skeleton Crew" series '
            'with matching custom fonts to create the shows text and borders '
            'just like the shows logo. Customizable color and episode text '
            'color with the ability to change the vertical position.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'skeleton_crew'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 20,
        'max_line_count': 4,
        'style': 'top',
    }

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME: str = 'SkeletonCrew'

    """Characteristics of title font"""
    TITLE_FONT = str(REF_DIRECTORY / 'SkeletonCrew.otf')
    TITLE_FONT_BOTTOM = REF_DIRECTORY / 'SkeletonCrew-Offset.otf'
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'source'

    """Characteristics of index text"""
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'SF-DistantGalaxy.ttf'
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number}'

    """Standard font replacements for the title font"""
    FONT_REPLACEMENTS = {
        '_': '',
        '~': '',
        '@': 'at',
        '*': '',
        '{': '(',
        '}': ')',
        '&': 'and',
    }

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """Extras"""
    DEFAULT_EPISODE_TEXT_COLOR: str = 'transparent'
    DEFAULT_SEPARATOR_CHARACTER: str = '•'
    DEFAULT_STROKE_COLOR: str = 'transparent'
    DEFAULT_OUTLINE_COLOR: str = TITLE_COLOR
    DEFAULT_OUTLINE_WIDTH: float = 16

    __slots__ = (
        'episode_text',
        'episode_text_color',
        'episode_text_font_size',
        'font_color',
        'font_size',
        'font_stroke_width',
        'font_vertical_shift',
        'hide_season_text',
        'hide_episode_text',
        'output_file',
        'outline_color',
        'outline_width',
        'season_text',
        'separator',
        'source_file',
        'stroke_color',
        'title_text',
        'vertical_position',
        '_title_coordinates',
        '_index_coordinates',
    )

    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = False,
            hide_episode_text: bool = False,
            # Font
            font_color: str = TITLE_COLOR,
            font_size: float = 1.0,
            font_stroke_width: float = 1.0,
            font_vertical_shift: int = 0,
            # Extras
            episode_text_color: str = DEFAULT_EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            outline_color: str = DEFAULT_OUTLINE_COLOR,
            outline_width: float = DEFAULT_OUTLINE_WIDTH,
            separator: str = DEFAULT_SEPARATOR_CHARACTER,
            stroke_color: str = DEFAULT_STROKE_COLOR,
            vertical_position: VerticalPosition = 'bottom',
            # Builtins
            blur: bool = False,
            grayscale: bool = False,
            preferences: 'Preferences | None' = None,
            **unused: Any,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text

        # Font customizations
        self.font_color = font_color
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.separator = separator
        self.stroke_color = stroke_color
        if vertical_position == 'random':
            vertical_position = random_choice(['bottom', 'center', 'top'])
        self.vertical_position = vertical_position

        # Implementation details
        self._title_coordinates: tuple[Coordinate, Coordinate] | None = None
        self._index_coordinates: tuple[Coordinate, Coordinate] | None = None


    def draw_border_command(self) -> ImageMagickCommands:
        """
        Draws the opposite corner radius border for the title text
        cutout the bottom border if theres a multiline title or close
        it if the title is single line

        Returns:
            List of ImageMagick commands necessary to draw the
            index box rectangle.
        """

        # No title, don't make border
        if not self.title_text:
            return []

        # Pull in bottom title text to measure bottom border coditional
        title_main_text, title_bottom_text = self._title_text_lines

        # Get width of title main text
        main_text_width = [
            f'-font "{self.TITLE_FONT}"',
            f'-pointsize {200 * self.font_size}',
            f'-annotate +0+0 "{title_main_text}"',
        ]
        main_text_width, _ = self.image_magick.get_text_dimensions(
            main_text_width
        )

        # Get width of title bottom text
        bottom_text_width_command = [
            f'-font "{self.TITLE_FONT}"',
            f'-pointsize {200 * self.font_size}',
            f'-annotate +0+0 "{title_bottom_text}"',
        ]
        bottom_text_width, _ = self.image_magick.get_text_dimensions(
            bottom_text_width_command
        )

        # Calculate x_start and x_end for both main and bottom text
        main_x_start = (self.WIDTH - main_text_width) / 2
        main_x_end = (self.WIDTH + main_text_width) / 2
        bottom_x_start  = (self.WIDTH - bottom_text_width) / 2
        bottom_x_end = (self.WIDTH + bottom_text_width) / 2

        # Compare and adjust only if bottom text is wider than main text
        # and pad x0 and x1. This is incase of long titles
        start, end = self.get_title_coordinates()
        x0, y0, x1, y1 = start.x, start.y, end.x, end.y
        scaled_offset = 72 * self.font_size
        if bottom_x_start < main_x_start or bottom_x_end > main_x_end:
            x0 -= sum([scaled_offset, max(0, x0 - bottom_x_start)])
            x1 += sum([scaled_offset, max(0, bottom_x_end - x1)])

        # Additional offsets necessary for equal padding
        bottom_x_start -= 36
        bottom_x_end += 36

        # Adjust the lines slightly depending on what character the
        # bottom title text starts or ends with to style with the
        # character and not width bounds (20px from line to character)

        # Dictionary for characters with their adjustments
        # Negative numbers represent -=, positive numbers represent +=
        upper_chars = {
            'A': 40, 'C': 12, 'E': 12, 'G': 12, 'J': 40, 'M': 24, 'O': 10,
            'Q': 10, 'V': 10, 'W': 5, 'X': 10, 'Y': 10, 'Z': 9, '2': 12,
            '4': 32, '6': 34, '0': 10
        }

        # Dictionary for lowercase characters with their adjustments
        lower_chars = {
            'a': -32, 'b': -2, 'd': -10, 'g': -10, 'k': -18, 'l': -36, 
            'm': -22, 'o': -12, 'p': -4, 'q': -12, 'r': -16, 's': -6,
            'v': -6, 'w': -6, 'y': -12, '2': -4, '3': -6, '5': -8,
            '6': -23, '8': -6, '9': -8, '0': -14
        }

        # Check the first character
        if title_bottom_text:
            char = title_bottom_text[0]
            if char in upper_chars:
                bottom_x_start += int(upper_chars[char] * self.font_size)

        # Check the last character
        if title_bottom_text:
            char = title_bottom_text[-1]
            if char in lower_chars:
                bottom_x_end += int(lower_chars[char] * self.font_size)

        return [
            f'-fill transparent',
            f'-stroke "{self.outline_color}"', 
            f'-strokewidth {self.outline_width}',
            # Whitespace at end to keep as single draw command
            f'-draw "arc {x0+10},{y0+130} {x0+130},{y0+10} 180,270 ',
            f'line {x0+65},{y0+10} {x1-30},{y0+10} ',
            f'arc {x1-60},{y0+10} {x1},{y0+60} 270,360 ',
            f'line {x1},{y0+30} {x1},{y1-65} ',
            f'arc {x1},{y1-130} {x1-130},{y1-10} 0,90 ',
            # Open bottom border
        ] + ([
            f'line {x0+30},{y1-10} {bottom_x_start},{y1-10} ', #left x0
            f'arc {bottom_x_start+10},{y1-10} {bottom_x_start-10},{y1+6} 270,360 ',
            f'line {x1-65},{y1-10} {bottom_x_end},{y1-10} ', #right x1
            f'arc {bottom_x_end+10},{y1-10} {bottom_x_end-10},{y1-26} 90,180 ',
        ] if title_bottom_text else [
            # Close off bottom border if no title bottom text
            f'line {x1-65},{y1-10} {x0+30},{y1-10} ',
        ]) + [
            f'arc {x0+60},{y1-10} {x0+10},{y1-60} 90,180 ',
            f'line {x0+10},{y1-30} {x0+10},{y0+65}"',
            f'-stroke none',
        ]


    @property
    def index_box_commands(self) -> ImageMagickCommands:
        """
        ImageMagick commands to draw the opposite corner radius box for
        the index text.
        """

        # All text hidden, don't make the box
        if self.hide_season_text and self.hide_episode_text:
            return []

        start, end = self.get_index_coordinates()
        x0, y0, x1, y1 = start.x, start.y, end.x, end.y

        return [
            f'-fill "{self.outline_color}"',
            f'-draw "path \'M {x0+20},{y0} ',
            f'A 20,20 0 0,0 {x0},{y0+20} ',
            f'L {x0+20},{y0} L {x1-10},{y0} ',
            f'A 10,10 0 0,1 {x1},{y0+10} ',
            f'L {x1},{y0+10} L {x1},{y1-20} ',
            f'A 20,20 0 0,1 {x1-20},{y1} ',
            f'L {x1-20},{y1} L {x0+10},{y1} ',
            f'A 10,10 0 0,1 {x0},{y1-10} ',
            f'L {x0},{y1-10} L {x0},{y0+20} Z\'"',
        ]


    @property
    def _title_text_lines(self) -> tuple[str, str | None]:
        """Process the title text to split off the last line of text."""

        # Check for line breaks, return as is if single line
        if '\n' not in self.title_text:
            return self.title_text, None

        lines = self.title_text.rsplit('\n', maxsplit=1)
        return lines[0], lines[1]


    def get_title_coordinates(self) -> tuple[Coordinate, Coordinate]:
        """
        Get the start and end coordinates of the bounding box around the
        title text.
        """

        if self._title_coordinates is None:
            # Get dimensions of title text
            width, height = self.image_magick.get_text_label_dimensions(
                self.title_text_commands[:-1], # Remove -composite command
            )

            # Get start coordinates of the bounding box
            x_start, x_end = (self.WIDTH - width) / 2, (self.WIDTH + width) / 2

            # Adjust y start position based on gravity and add vertical shift
            # And adjust offset for single line titles to match 2 line titles
            if self.vertical_position == 'top':
                y_offset = 157
                y_offset += self.font_vertical_shift
                y_start = y_offset
            elif self.vertical_position == 'center':
                y_offset = 30
                y_offset += self.font_vertical_shift
                y_start = (self.HEIGHT - height) / 2 + y_offset
            else:
                y_offset = 217 if '\n' not in self.title_text else 60
                y_offset += self.font_vertical_shift
                y_start = self.HEIGHT - height - y_offset

            y_end = y_start + height

            # Additional offsets necessary for equal padding
            x_start -= 56
            x_end += 44
            y_start -= 50
            y_end += 16

            # Adjust for font size changes over multi-line
            if len(self.title_text.splitlines()) >= 2:
                # Font size * user input font size * 65%
                y_end -= 200 * self.font_size * 0.65
            else:
                y_end += 20

            self._title_coordinates = (
                Coordinate(x_start, y_start),
                Coordinate(x_end, y_end)
            )

        return self._title_coordinates


    def get_index_coordinates(self) -> tuple[Coordinate, Coordinate]:
        """
        Get the coordinates of the bounding box around the index text.
        """

        if self._index_coordinates is None:
            # Ensure title coordinates are calculated without causing
            # recursion as a precaution
            if self._title_coordinates is None:
                self._title_coordinates = self.get_title_coordinates()

            # Get dimensions of index text
            width, height = self.image_magick.get_text_dimensions(
                self.index_text_commands
            )

            # Calculate y offset based on title's coordinates
            y_offset = (self.HEIGHT - self._title_coordinates[0].y) - 35

            # Get start coordinates of the bounding box
            x_start, x_end = (self.WIDTH - width) / 2, (self.WIDTH + width) / 2
            y_end = self.HEIGHT - y_offset
            y_start = y_end - height

            # Additional offsets for equal padding
            x_start -= 24
            x_end += 22

            self._index_coordinates = (
                Coordinate(x_start, y_start),
                Coordinate(x_end, y_end)
            )

        return self._index_coordinates


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # If no title text, return empty commands
        if not self.title_text:
            return []

        # Split up text so we can change font of bottom text
        title_main_text, title_bottom_text = self._title_text_lines

        # Font size
        font_size = 200 * self.font_size

        # Determine gravity prefix based on vertical position
        # And adjust offset for single line titles to match 2 line titles
        if self.vertical_position == 'top':
            gravity_prefix = 'north'
            y_offset = 157
        elif self.vertical_position == 'center':
            gravity_prefix = 'center'
            y_offset = 30
        else:  # Assuming 'bottom' or any other value defaults to 'south'
            gravity_prefix = 'south'
            y_offset = 217 if '\n' not in self.title_text else 60

        # Text offsets
        y = y_offset + self.font_vertical_shift

        stroke_commands: list[str] = []
        if self.stroke_color != 'transparent':
            stroke_commands = [
                f'-stroke "{self.stroke_color}"',
                f'-strokewidth {4 * self.font_stroke_width}',
            ]

        return [
            # Add title text
            f'-font "{self.TITLE_FONT}"',
            f'-gravity {gravity_prefix}',
            f'-pointsize {font_size}',
            f'-background transparent',
            f'-fill "{self.font_color}"',
            fr'\(',
            f'-font "{self.TITLE_FONT}"',
            *stroke_commands,
            f'label:"{title_main_text}"',
        ] + ([
            # Conditionally add bottom title text if it exists
            f'-font "{self.TITLE_FONT_BOTTOM}"',
            f'label:"{title_bottom_text}"',
            f'-append',
        ] if title_bottom_text else []) + [
            fr'\)',
            f'-geometry +0{y:+}',
            f'-composite',
        ]


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding the index text to the image."""

        # All text hidden, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Set index text based on which text is hidden/not
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} {self.separator} {self.episode_text}'

        # Text offsets
        y = self.HEIGHT - self.get_title_coordinates()[0].y - 35

        return [
            f'-kerning 0',
            f'-pointsize {50 * self.episode_text_font_size}',
            f'-gravity south',
            f'-font "{self.EPISODE_TEXT_FONT}"',
            f'-fill {self.episode_text_color}',
            f'-stroke none',
            f'-antialias',
            f'-annotate +0{y:+} "{index_text}"',
        ]


    def create_overlay_image(self) -> Path:
        """
        Create the overlay image combining the title border, index box
        and index text.

        Returns:
            Path to the created image. This is a temporary image which
            must be deleted afterwards.
        """

        # Get random filename for intermediate image
        # PNG for transparency and quality
        image = self.image_magick.get_random_filename(
            self.source_file, extension='png'
        )

        self.image_magick.run([
            f'convert',
            f'-size "{self.TITLE_CARD_SIZE}"',
            f'xc:transparent',
            # Combine title border and index box
            *self.draw_border_command(),
            *self.index_box_commands,
            # Add index text
            *self.index_text_commands,
            f'"{image.resolve()}"',
        ])

        return image


    @staticmethod
    def modify_extras(
            extras: dict,
            custom_font: bool,
            custom_season_titles: bool,
        ) -> None:
        """
        Modify the given extras based on whether font or season titles
        are custom.

        Args:
            extras: Dictionary to modify.
            custom_font: Whether the font are custom.
            custom_season_titles: Whether the season titles are custom.
        """

        # Generic font, reset episode text and box colors
        if not custom_font:
            for extra in (
                'episode_text_color',
                'episode_text_font_size',
                'outline_color',
                'stroke_color',
            ):
                if extra in extras:
                    del extras[extra]


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determines whether the given font characteristics constitute a
        default or custom font.
        
        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.
        
        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = SkeletonCrewTitleCard._is_custom_extras(
            extras,
            {
                'episode_text_color': SkeletonCrewTitleCard.DEFAULT_EPISODE_TEXT_COLOR,
                'episode_text_font_size': 1.0,
                'outline_color': SkeletonCrewTitleCard.DEFAULT_OUTLINE_COLOR,
                'stroke_color': SkeletonCrewTitleCard.DEFAULT_STROKE_COLOR,
            }
        )

        return custom_extras or (
            font.size != 1.0
            or font.stroke_width != 1.0
            or font.vertical_shift != 0
        )


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Determine whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        return (
            custom_episode_map
            or episode_text_format != SkeletonCrewTitleCard.EPISODE_TEXT_FORMAT
        )


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Layers are ordered as:
        # [Source Image] | [Overlay image]

        # Temporary file which must be deleted
        overlay_image = self.create_overlay_image()

        self.image_magick.run([
            f'convert',
            # Layer 0 is the source image which will be the background
            fr'\(',
            f'"{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            fr'\)',
            # Layer 1 is the overlay image
            f'"{overlay_image.resolve()}"',
            # Use compose over to combine
            f'-compose over',
            f'-composite',
            # Add title text here over overlay layer because of transparency
            *self.title_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.delete_intermediate_images(overlay_image)


def get_validator_model() -> type[Base]:
    """Get the Pydantic validator class for this card type."""

    class CardModel(BaseCardTypeAllText):
        font_color: str = SkeletonCrewTitleCard.TITLE_COLOR
        font_size: PositiveFloat = 1.0
        font_vertical_shift: int = 0
        episode_text_color: str = 'transparent'
        episode_text_font_size: PositiveFloat = 1.0
        outline_color: str | None = None
        outline_width: PositiveFloat = SkeletonCrewTitleCard.DEFAULT_OUTLINE_WIDTH
        separator: str = SkeletonCrewTitleCard.DEFAULT_SEPARATOR_CHARACTER
        stroke_color: str = SkeletonCrewTitleCard.DEFAULT_STROKE_COLOR
        vertical_position: VerticalPosition = 'bottom'

        @model_validator(mode='after')
        def assign_unassigned_colors(self) -> Self:
            """Assign any unassigned colors to their default values."""

            if self.outline_color is None:
                self.outline_color = self.font_color

            return self

    return CardModel
