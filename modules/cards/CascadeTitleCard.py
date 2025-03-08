from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import PositiveFloat, conint, FilePath, root_validator

from app.schemas.base import Base, BaseCardTypeAllText
from modules.BaseCardType import (
    BaseCardType,
    CardTypeDescription,
    Coordinate,
    Extra,
    ImageMagickCommands,
    Rectangle,
)
from modules.Debug import log
from modules.EpisodeInfo2 import EpisodeInfo
from modules.FormatString import FormatString
from modules.ImageMagickInterface import Dimensions

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


class SequenceGenerator:
    """
    A sequence definition which defines some iterative logic for
    stepping through a set of numbers. These can take multiple forms,
    for example:
    
    >>> SequenceGenerator('80,60,40')
    [80, 60, 40, 40, ...] # 40 repeats forever

    >>> SequenceGenerator('80,-10')
    [80, 70, 60, ...] # Yields in decrements of 10 forever

    >>> SequenceGenerator('100,40,/2')
    [100, 40, 20, 10, ...] # Yields halved values forever

    The operators that are supported are: `+`, `-`, `/`, and `*`.
    """

    def __init__(self,
            sequence: str,
            /,
            bounds: tuple[int | float, int | float] | None = None,
        ) -> None:
        """
        Initialize this object with the given sequence.

        Args:
            sequence: Definiton of this sequence to generate.
            bounds: Lower/upper limits for bounds of this sequence.
                Applied inclusively - e.g. [lower, upper].
        """

        self._values = sequence.split(',')
        self._bounds = bounds
        self._index = 0

        self.__operator: str | None = None
        self.__step: float | None = None
        self.__value = 100

        if len(self._values) == 0:
            raise ValueError


    def __apply_bounds(self, value: float, /) -> float:
        """Apply the bounds of this sequence to the given value."""

        if not self._bounds:
            return value

        return min(max(self._bounds[0], value), self._bounds[1])


    def __iter__(self) -> 'SequenceGenerator':
        """Begin iteration through this object."""

        self._index = 0
        self.__operator = None
        self.__step = None
        self.__value = 0

        return self


    def __next__(self):
        """
        Get the next value in the sequence. This applies the iterative
        sequence logic in this object's definition.        
        """

        # Iterated values still available
        if self._index < len(self._values):
            value = self._values[self._index]

            # Element is not a step modifier
            if value[0].isdigit():
                self.__operator, self.__step = None, None
                self._index += 1
                self.__value = float(value)
                return self.__apply_bounds(self.__value)

            # Parse operator and step value
            self.__operator, self.__step = value[0], float(value[1:])

        # Modify last value based on last operator and step
        if self.__operator and self.__step is not None:
            if self.__operator == '+':
                self.__value += self.__step
            elif self.__operator == '-':
                self.__value -= self.__step
            elif self.__operator == '/':
                self.__value /= self.__step
            elif self.__operator == '*':
                self.__value *= self.__step
            else:
                raise ValueError

            self._index += 1
            return self.__apply_bounds(self.__value)

        # End of the sequence, return last value
        self._index += 1
        self.__value = float(self._values[-1])
        return self.__apply_bounds(self.__value)


    @classmethod
    def validate_sequence(cls,
            sequence: str,
            /,
            length: int,
            bounds: tuple[int | float, int | float] = (0, 100),
        ) -> None:
        """
        Validate the given sequence string. This ensures the sequences
        yields at least `length` many items which are bound within
        `bounds` (inclusive).

        Args:
            sequence: Strip being validated.
            length: Minimum number of items the sequence must yield.
            bounds: The top and bottom boundaries for all items.

        Raises:
            ValueError if the given sequence produces any out-of-bounds
                elements.
            Other exceptions may be raised in an invalid sequence is
            provided.
        """

        # Empty sequence, always valid
        if length <= 0:
            return None

        # Attempt to iterate through the sequence the specified times
        seq = cls(sequence)

        for index, value in zip(range(length), seq):
            if not bounds[0] <= value <= bounds[1]:
                raise ValueError(
                    f'Sequence element {index} ({value}) is out of bounds {bounds}'
                )

        return None


class CascadeTitleCard(BaseCardType):
    """
    CardType that produces title cards ... TODO
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Cascade',
        identifier='cascade',
        example='/internal_assets/cards/cascade.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Alternate Text Format',
                identifier='alt_text',
                description='Text to display above the title',
                tooltip=(
                    'Can be literal text (.e.g <v>My Series</v>), or a format '
                    'string (e.g. <v>{series_name}</v>) to dynamically adjust '
                    'the text. Set as empty quotes to remove. Default is '
                    '<v>{series_name.upper()}</v>.'
                ),
                default='{series_name.upper()}',
            ),
            Extra(
                name='Alterate Text Color',
                identifier='alt_text_color',
                description='Color of the alterate text',
                tooltip='Defaults to the Episode Text Color.',
            ),
            Extra(
                name='Cascade Text Count',
                identifier='cascade_count',
                description='How many cascades of text to create',
                tooltip=(
                    'Number between <v>0</v> and <v>25</v>. Default is '
                    '<v>2</v>.'
                ),
                default=2,
            ),
            Extra(
                name='Cascade Transparencies',
                identifier='cascade_alphas',
                description='How transparent to make the cascading text',
                tooltip=(
                    'See <a href="" target="_blank">the documentation</a> for '
                    'details. Default is <v>66,/2</v>.'
                ),
                default='66,/2',
            ),
            Extra(
                name='Cascade Cropping',
                identifier='cascade_cropping',
                description='How much to crop out of the cascading text',
                tooltip=(
                    'See <a href="" target="_blank">the documentation</a> for '
                    'details. Default is <v>66,/2</v>.'
                ),
                default='66,/2',
            ),
            Extra(
                name='Cascade Text Fill Color',
                identifier='cascade_fill_color',
                description='Color to fill the cascading text with',
                tooltip='Default is <c>transparent</c>.',
                default='transparent',
            ),
            Extra(
                name='Cascade Text Outline Color',
                identifier='cascade_outline_color',
                description='Color to outline the cascading text with',
                tooltip='Default is <c>white</c>.',
                default='white',
            ),
            Extra(
                name='Cascade Text Outline Width',
                identifier='cascade_width',
                description='How wide to make the outline of the cascade text',
                tooltip=(
                    'Number between <v>0</v> and <v>50</v>. Default is '
                    '<v>5</v>. Unit is pixels.'
                ),
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
                name='Glass Toggle',
                identifier='enable_glass',
                description='Whether to draw background glass behind all text',
                tooltip=(
                    'Either <v>True</v> or <v>False</v> to disable the glass. '
                    'Default is <v>True</v>.'
                ),
                default='True',
            ),
            Extra(
                name='Glass Color',
                identifier='glass_color',
                description='Color of the background glass',
                tooltip='Default is <c>rgba(0,0,0,0.3)</c>.',
                default='rgba(0,0,0,0.3)',
            ),
            Extra(
                name='Glass Edge Color',
                identifier='glass_edge_color',
                description='Color of the edge of the background glass',
                tooltip='Default is <c>rgba(12,12,12,0.4)</c>.',
                default='rgba(12,12,12,0.4)',
            ),
            Extra(
                name='Italicize Title Text',
                identifier='italicize_title_text',
                description='Whether to italicize the title text',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Only works when using '
                    'the default Font. Default is <v>False</v>.'
                ),
                default='False',
            ),
            Extra(
                name='Allow Kanji in Episode Text',
                identifier='allow_kanji_episode_text',
                description='Permit kanji characters in the episode text',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v> then '
                    'an alternate font is used which correctly displays Kanji '
                    'characters; it is recommended to set the Episode Text '
                    'Format to <v>{kanji}</v> . Default is <v>False</v>.'
                ),
                default='False',
            ),
        ],
        description=[
            'A card type which features an adjustable number of cascading '
            'outlines of text.', 'The color, count, and visual styling of the '
            'cascading text can all be adjusted with extras.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'cascade'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 20,
        'max_line_count': 4,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    _ITALIC_TITLE_FONT = REF_DIRECTORY / 'SpockEssAlt1-It.ttf'
    TITLE_FONT = str((REF_DIRECTORY / 'SpockEssAlt1.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'E{episode_number}'
    EPISODE_TEXT_COLOR = TITLE_COLOR
    EPISODE_TEXT_FONT = TITLE_FONT
    _KANJI_TEXT_FONT = REF_DIRECTORY.parent / 'anime' / 'hiragino-mincho-w3.ttc'

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE = True

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Cascade Style'

    """Implementation details"""
    DEFAULT_CASCADE_ALPHAS: str = '66,/2'
    DEFAULT_CASCADE_COUNT: int = 2
    DEFAULT_CASCASE_CROP: str = '66,/2'
    DEFAULT_CASCADE_FILL_COLOR: str = 'transparent'
    DEFAULT_CASCADE_OUTLINE_COLOR: str = TITLE_COLOR#'red'
    DEFAULT_CASCADE_WIDTH: int = 5
    DEFAULT_GLASS_COLOR: str = 'rgba(0,0,0,0.3)'
    DEFAULT_GLASS_EDGE_COLOR: str = 'rgba(12,12,12,0.4)'

    __slots__ = (
        'allow_kanji_episode_text',
        'alt_text',
        'alt_text_color',
        'cascade_alphas',
        'cascade_count',
        'cascade_cropping',
        'cascade_fill_color',
        'cascade_outline_color',
        'cascade_width',
        'enable_glass',
        'episode_text',
        'episode_text_color',
        'episode_text_font_size',
        'font_file',
        'font_color',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_kerning',
        'font_size',
        'font_vertical_shift',
        'glass_color',
        'glass_edge_color',
        'hide_episode_text',
        'hide_season_text',
        'italicize_title_text',
        'output_file',
        'season_text',
        'source_file',
        'title_text',
        '__bottom_dimensions',
        '__multiline_mode',
        '__title_dimensions',
        '__top_dimensions',
    )


    @staticmethod
    def season_text_formatter(episode_info: EpisodeInfo) -> str:
        """
        Fallback season title formatter.

        Args:
            episode_info: Info of the Episode whose season text is being
                determined.

        Returns:
            `S{x}` for the given season number.
        """

        return f'S{episode_info.season_number}'


    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            # Text
            title_text: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = False,
            hide_episode_text: bool = False,
            # Font
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            # Builtins
            blur: bool = False,
            grayscale: bool = False,
            # Extras
            allow_kanji_episode_text: bool = False,
            alt_text: str | None = None,
            alt_text_color: str = EPISODE_TEXT_COLOR,
            cascade_alphas: str = DEFAULT_CASCADE_ALPHAS,
            cascade_count: int = DEFAULT_CASCADE_COUNT,
            cascade_cropping: str = DEFAULT_CASCASE_CROP,
            cascade_fill_color: str = DEFAULT_CASCADE_FILL_COLOR,
            cascade_outline_color: str = DEFAULT_CASCADE_OUTLINE_COLOR,
            cascade_width: int = DEFAULT_CASCADE_WIDTH,
            enable_glass: bool = True,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            italicize_title_text: bool = False,
            glass_color: str = DEFAULT_GLASS_COLOR,
            glass_edge_color: str = DEFAULT_GLASS_EDGE_COLOR,
            preferences: 'Preferences | None' = None,
            **unused,
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

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = 0 + font_interword_spacing
        self.font_kerning = 1.0 * font_kerning
        self.font_size = font_size
        self.font_vertical_shift = 0 + font_vertical_shift

        # Extras
        self.allow_kanji_episode_text = allow_kanji_episode_text
        self.alt_text = alt_text
        self.alt_text_color = alt_text_color
        self.cascade_alphas = SequenceGenerator(cascade_alphas, (0, 100))
        self.cascade_count = cascade_count
        self.cascade_cropping = SequenceGenerator(cascade_cropping, (1, 100))
        self.cascade_fill_color = cascade_fill_color
        self.cascade_outline_color = cascade_outline_color
        self.cascade_width = cascade_width
        self.enable_glass = enable_glass
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.glass_color = glass_color
        self.glass_edge_color = glass_edge_color
        self.italicize_title_text = italicize_title_text
        self.__multiline_mode = len(title_text.splitlines()) > 1
        self.__bottom_dimensions = Dimensions(0, 0)
        self.__top_dimensions = Dimensions(0, 0)
        self.__title_dimensions = Dimensions(0, 0)


    @property
    def glass_commands(self) -> ImageMagickCommands:
        """
        Subcommands to draw the background glass to the image. This adds
        the rectangle to the 0th image in the stack.
        """

        # Glass disabled, return empty commands
        if not self.enable_glass or not self.title_text:
            return []

        # Center of the rectangle/image
        center = Coordinate(self.WIDTH / 2, self.HEIGHT / 2)

        # Height of the alt/index text; +100% size = 83% size increase
        alt_text_height = (45 * self.episode_text_font_size) + 30
        if (self.hide_season_text and self.hide_episode_text
            and not self.alt_text):
            alt_text_height = 0

        # Determine effective dimensions of the cascading text elements
        width = self.__title_dimensions.width + 50
        height = (
            # Height of the title itself
            self.__title_dimensions.height
            # Combined height of both cascades
            + (self.__top_dimensions.height * self.cascade_count)
            + (self.__bottom_dimensions.height * self.cascade_count)
            # Margin
            + 50
        )

        rectangle = Rectangle(
            center - (width / 2, (height / 2) + alt_text_height),
            center + (width / 2, height / 2)
        )

        return [
            # Blur rectangle in the given bounds
            fr'\( -clone 0',
            f'-fill white',
            f'-colorize 100',
            f'-fill black',
            f'-draw "roundrectangle {rectangle} 25,25"',
            f'-alpha off',
            f'-write mpr:mask',
            fr'+delete \)',
            f'-mask mpr:mask',
            f'' if self.blur else f'-blur 0x12',
            f'+mask',
            # Draw glass shape
            f'-fill "{self.glass_color}"',
            f'-stroke "{self.glass_edge_color}" -strokewidth 2',
            f'-draw "roundrectangle {rectangle} 25,25"',
            # Reset stroke for subsequent text commands
            f'+stroke',
        ]


    @property
    def cascading_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the cascading text to the image."""

        # No cascading text, return empty commands
        if self.cascade_count <= 0 or not self.title_text:
            return []

        # Both text modes need a reference image for the top line
        commands = [
            fr'\(',
            f'-background none',
            f'-fill "{self.cascade_fill_color}"',
            f'-stroke "{self.cascade_outline_color}"',
            f'-strokewidth {self.cascade_width}',
            f'label:"{self.title_text.splitlines()[0]}"',
            # Remove any white space padding
            f'-trim',
            # Repage so that future crops aren't misaligned
            f'+repage',
            fr'\)',
        ]
        # Multiple lines of text: Create two reference images; one for
        # the top line of text, the other for the last. These need to be
        # deleted from the final image by deleting indices 1 and 2.
        if self.__multiline_mode:
            commands.extend([
                fr'\(',
                f'-background none',
                f'-fill "{self.cascade_fill_color}"',
                f'-stroke "{self.cascade_outline_color}"',
                f'-strokewidth {self.cascade_width}',
                f'label:"{self.title_text.splitlines()[-1]}"',
                # Remove any white space padding
                f'-trim',
                # Repage so that future crops aren't misaligned
                f'+repage',
                fr'\)',
            ])
        # Single line of text: Create one reference image as the entire
        # title text. This needs to be deleted from the final image by
        # deleting index 1.
        else:
            pass

        # Add each cascade effect
        for alpha, crop, cascade_index in zip(
                self.cascade_alphas,
                self.cascade_cropping,
                range(self.cascade_count)
            ):
            # Offset to the center of the cropped image. Formula was
            # derived where 100% crop would result in 0px offset, and a
            # 50% crop would result in a half-height offset
            alpha /= 100.0
            top_dy = (
                (
                    (self.__title_dimensions.height / 2)
                    - (self.__top_dimensions.height * (crop / 100 / 2))
                )
                + self.__top_dimensions.height * (cascade_index + 1)
            )
            bottom_dy = (
                (
                    (self.__title_dimensions.height / 2)
                    - (self.__bottom_dimensions.height * (crop / 100 / 2))
                )
                + self.__bottom_dimensions.height * (cascade_index + 1)
            )

            # Add top cascade
            top_reference_id = 1
            commands.extend([
                # Add a new image to the stack
                fr'\(',
                # Clone the reference outline image
                f'-clone {top_reference_id}',
                # Crop the top part of the reference image
                f'-gravity north',
                f'-crop 0x{crop}%',
                # Apply alpha modifier to cloned image
                f'-channel A',
                f'-evaluate multiply {alpha}',
                f'+channel',
                # On the first cascade, clone the base image, all other
                # passes just grab the most recent cascade on the stack
                f'-clone 0' if cascade_index == 0 else f'+clone',
                # Swap so that the text image is composed atop the reference
                f'+swap',
                f'-gravity center',
                f'-geometry +0-{top_dy}',
                f'-composite',
                fr'\)',
            ])

            # Add bottom cascade
            bottom_reference_id = 2 if self.__multiline_mode else 1
            commands.extend([
                # Add a new image to the stack
                fr'\(',
                # Clone the reference outline image
                f'-clone {bottom_reference_id}',
                # Crop the bottom part of the reference image
                f'-gravity south',
                f'-crop 0x{crop}%',
                # Apply alpha modifier to cloned image
                f'-channel A',
                f'-evaluate multiply {alpha}',
                f'+channel',
                # Always clone the most recent cascade on the stack
                f'+clone',
                # Swap so that the text image is composed atop the reference
                f'+swap',
                f'-gravity center',
                f'-geometry +0+{bottom_dy}',
                f'-composite',
                fr'\)',
            ])

        # Delete the original base image (as its now merged in the last
        # cascade on the stack), and the reference cascade image(s)
        stack_ids = range(
            (self.cascade_count * 2) + (2 if self.__multiline_mode else 1)
        )
        commands.append('-delete ' + ','.join(map(str, stack_ids)))

        return commands


    @property
    def alt_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the alternate text to the image. This adds
        the text to the 0th image of the stack.
        """

        # No alt text, return empty commands
        if not self.alt_text:
            return []

        # Do not display alt text if the episode text was already longer
        # than the title width
        index_width, _ = self.image_magick.get_text_dimensions(
            self.index_text_commands,
            density=100,
        )
        if index_width > self.__title_dimensions.width:
            return []

        # Position the alt text on the left side of the width
        dx = (self.WIDTH - self.__title_dimensions.width) / 2 - 8 # 8px margin
        dy = (
            # Half of the lines of text are above the center point
            (self.__title_dimensions.height / 2)
            # Add height of all cascades 
            + (self.__top_dimensions.height * self.cascade_count)
            # 50 px margin
            + 50
        )

        size = 40 * self.episode_text_font_size

        text_commands = [
            f'-font "{self.TITLE_FONT}"',
            f'-fill "{self.alt_text_color}"',
            f'-pointsize {size}',
            f'-gravity west',
            f'-annotate +{dx}-{dy} "{self.alt_text}"',
        ]

        # Truncate alt text if this and the index text are too wide
        alt_width, _ = self.image_magick.get_text_label_dimensions(
            ['-background none'] + text_commands[:-1] + [f'label:"{self.alt_text}"'],
            density=100,
        )

        if index_width + alt_width + 25 > self.__title_dimensions.width:
            new_width = self.__title_dimensions.width - index_width - 25
            new_length = int(new_width / alt_width * len(self.alt_text)) - 1
            if new_length <= 0:
                return []

            modifed_text = self.alt_text[:new_length]
            text_commands[-1] = f'-annotate +{dx}-{dy} "{modifed_text}.."'

        return text_commands


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the season and episode text to the image.
        """

        # All text hidden, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Determine index text
        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_episode_text:
            index_text = self.season_text
        else:
            index_text = f'{self.season_text} {self.episode_text}'

        font = self.TITLE_FONT
        if self.allow_kanji_episode_text:
            font = str(self._KANJI_TEXT_FONT.resolve())

        # Position the index text on the right side of the text
        dx = (self.WIDTH - self.__title_dimensions.width) / 2 + 8
        dy = (
            # Height of the top half of the title
            (self.__title_dimensions.height / 2)
            # Height of the top cascades
            + (self.__top_dimensions.height * self.cascade_count)
            # Margin
            + 50
        )
        size = 40 * self.episode_text_font_size

        return [
            f'-font "{font}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {size}',
            f'-gravity east',
            f'-annotate +{dx}-{dy} "{index_text}"',
        ]


    def get_title_text_commands(self,
            which: Literal['all', 'top', 'bottom'],
        ) -> ImageMagickCommands:
        """
        Get the subcommands to add the title text to the image. This
        will always merge the title text into the 0th image in the image
        stack.

        Args:
            which: Which text to create in the commands. Top/bottom will
                only added the first or last line of text, and all will
                display all lines.

        Returns:
            List of ImageMagick commands.
        """

        # No title text, return blank commands
        if not self.title_text:
            return []
 
        # Determine text to add to the image
        if which == 'all':
            text = self.title_text
        elif which == 'bottom':
            text = self.title_text.splitlines()[-1]
        else:
            text = self.title_text.splitlines()[0]

        # Font characteristics
        interline_spacing = self.font_interline_spacing
        interword_spacing = 30 + self.font_interword_spacing
        kerning = 1 * self.font_kerning
        size = 120 * self.font_size
        y_pos = 0 + self.font_vertical_shift
        if self.italicize_title_text:
            file = str(self._ITALIC_TITLE_FONT.resolve())
        else:
            file = self.font_file

        return [
            fr'\(',
            f'-background none',
            f'-fill "{self.font_color}"',
            f'-font "{file}"',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {interword_spacing}',
            f'-kerning {kerning}',
            f'-pointsize {size}',
            f'-gravity center',
            f'label:"{text}"',
            # Remove any white space padding
            f'-trim',
            fr'\)',
            f'-geometry +0{y_pos:+}',
            # Add to image
            f'-composite',
        ]


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
                'alt_text_color',
                'cascade_fill_color',
                'cascade_outline_color',
                'episode_text_color',
                'episode_text_font_size',
                'glass_color',
                'glass_edge_color',
            ):
                if extra in extras:
                    del extras[extra]
        if not custom_season_titles:
            if 'allow_kanji_episode_text' in extras:
                del extras['allow_kanji_episode_text']


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = CascadeTitleCard._is_custom_extras(
            extras,
            {
                'alt_text_color': CascadeTitleCard.EPISODE_TEXT_COLOR,
                'cascade_fill_color': CascadeTitleCard.DEFAULT_CASCADE_FILL_COLOR,
                'cascade_outline_color': CascadeTitleCard.DEFAULT_CASCADE_OUTLINE_COLOR,
                'episode_text_color': CascadeTitleCard.EPISODE_TEXT_COLOR,
                'episode_text_font_size': 1.0,
                'glass_color': CascadeTitleCard.DEFAULT_GLASS_COLOR,
                'glass_edge_color': CascadeTitleCard.DEFAULT_GLASS_EDGE_COLOR,
            }
        )

        return (custom_extras
            or (
                font.color != CascadeTitleCard.TITLE_COLOR
                or font.file != CascadeTitleCard.TITLE_FONT
                or font.interline_spacing != 0
                or font.interword_spacing != 0
                or font.kerning != 1.0
                or font.size != 1.0
                or font.vertical_shift != 0
            )
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
            or episode_text_format != CascadeTitleCard.EPISODE_TEXT_FORMAT
        )


    def create(self) -> None:
        """Create this object's defined Title Card."""

        # Pre-compute the dimensions of the title text as it is used in
        # multiple commands
        self.__title_dimensions = self.image_magick.get_text_label_dimensions(
            self.get_title_text_commands('all')[1:-4],
            density=100,
        )
        if self.__multiline_mode:
            self.__top_dimensions = self.image_magick.get_text_label_dimensions(
                self.get_title_text_commands('top')[1:-4],
                density=100,
            )
            self.__bottom_dimensions = self.image_magick.get_text_label_dimensions(
                self.get_title_text_commands('bottom')[1:-4],
                density=100,
            )
        else:
            self.__top_dimensions = self.__title_dimensions
            self.__bottom_dimensions = self.__title_dimensions

        # Create the Title Card
        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            f'-density 100',
            # Apply styling
            *self.resize_and_style,
            # Add all card components
            *self.glass_commands,
            *self.index_text_commands,
            *self.alt_text_commands,
            *self.get_title_text_commands('all'),
            *self.cascading_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[Base]:
    """Get the Pydantic validator class for this card type."""

    # pyright: reportInvalidTypeForm=false
    class CardModel(BaseCardTypeAllText):
        font_color: str = CascadeTitleCard.TITLE_COLOR
        font_file: FilePath = CascadeTitleCard.TITLE_FONT # type: ignore
        font_interline_spacing: int = 0
        font_interword_spacing: int = 0
        font_kerning: float = 1.0
        font_size: PositiveFloat = 1.0
        font_vertical_shift: int = 0
        allow_kanji_episode_text: bool = False
        alt_text: str | None = '{series_name}'
        alt_text_color: str | None = None
        cascade_count: conint(ge=0, le=25) = CascadeTitleCard.DEFAULT_CASCADE_COUNT
        cascade_alphas: str = CascadeTitleCard.DEFAULT_CASCADE_ALPHAS
        cascade_cropping: str = CascadeTitleCard.DEFAULT_CASCASE_CROP
        cascade_fill_color: str = CascadeTitleCard.DEFAULT_CASCADE_FILL_COLOR
        cascade_outline_color: str = CascadeTitleCard.DEFAULT_CASCADE_OUTLINE_COLOR
        cascade_width: conint(ge=0, le=50) = CascadeTitleCard.DEFAULT_CASCADE_WIDTH
        episode_text_color: str | None = None
        episode_text_font_size: PositiveFloat = 1.0
        enable_glass: bool = True
        glass_color: str = CascadeTitleCard.DEFAULT_GLASS_COLOR
        glass_edge_color: str = CascadeTitleCard.DEFAULT_GLASS_EDGE_COLOR
        italicize_title_text: bool = False

        @root_validator(skip_on_failure=True)
        def assign_unassigned_color(cls, values: dict) -> dict:
            """Assign any unassigned colors to their default values."""

            if values['episode_text_color'] is None:
                values['episode_text_color'] = values['font_color']
            if values['alt_text_color'] is None:
                values['alt_text_color'] = values['episode_text_color']

            return values

        @root_validator(skip_on_failure=True, pre=True)
        def finalize_format_strings(cls, values: dict) -> dict:
            """
            Finalize the alternate text format string using all
            available data
            """

            alt_text = values.get('alt_text', '{series_name.upper()}')
            if alt_text is not None:
                values['alt_text'] = FormatString(alt_text, data=values).result

            return values

        @root_validator(skip_on_failure=True)
        def validate_sequence_strings(cls, values: dict) -> dict:
            """
            Validate the cascade sequence strings are valid for at least
            the specified cascade count.
            """

            try:
                SequenceGenerator.validate_sequence(
                    values['cascade_alphas'],
                    length=values['cascade_count'],
                )
            except Exception as exc:
                raise ValueError(
                    f'Cascade Transparency sequence is invalid ({exc})'
                )
            try:
                SequenceGenerator.validate_sequence(
                    values['cascade_cropping'],
                    length=values['cascade_count'],
                )
            except Exception as exc:
                raise ValueError(
                    f'Cascade Cropping sequence is invalid ({exc})'
                )

            return values

    return CardModel
