from pathlib import Path
from typing import TYPE_CHECKING

from modules.BaseCardType import (
    BaseCardType,
    CardTypeDescription,
    Coordinate,
    Extra,
    ImageMagickCommands,
    Rectangle,
)
from modules.Debug import log
from modules.ImageMagickInterface import Dimensions
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


class CascadeTitleCard(BaseCardType):
    """
    CardType that produces title cards ... TODO
    """

    """API Parameters"""
    API_DETAILS: CardTypeDescription = CardTypeDescription(
        name='Cascade',
        identifier='cascade',
        example='/internal_assets/cards/cascade.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            
        ],
        description=[
            
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'cascade'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 20,
        'max_line_count': 3,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT: str = str((REF_DIRECTORY / 'SpockEssAlt1.ttf').resolve())
    TITLE_COLOR: str = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS: dict[str, str] = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number}'
    EPISODE_TEXT_COLOR = TITLE_COLOR
    EPISODE_TEXT_FONT = TITLE_FONT

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE: bool = True

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME: str = 'Cascade Style'

    """Implementation details"""
    DEFAULT_CASCADE_COUNT: int = 2
    DEFAULT_CASCASE_CROP: str = '66,33'
    DEFAULT_CASCADE_FILL_COLOR: str = 'transparent'
    DEFAULT_CASCADE_OUTLINE_COLOR: str = 'red'
    DEFAULT_CASCADE_WIDTH: int = 5

    __slots__ = (
        'alt_text',
        'cascade_count',
        'cascade_cropping',
        'cascade_fill_color',
        'cascade_outline_color',
        'cascade_width',
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
        'hide_episode_text',
        'hide_season_text',
        'output_file',
        'season_text',
        'source_file',
        'title_text',
        '__title_dimensions',
    )


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
            alt_text: str | None = None,
            cascade_count: int = DEFAULT_CASCADE_COUNT,
            cascade_cropping: str = DEFAULT_CASCASE_CROP,
            cascade_fill_color: str = DEFAULT_CASCADE_FILL_COLOR,
            cascade_outline_color: str = DEFAULT_CASCADE_OUTLINE_COLOR,
            cascade_width: int = DEFAULT_CASCADE_WIDTH,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            italicize_title_text: bool = False,
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
        self.alt_text = alt_text
        self.cascade_count = cascade_count
        self.cascade_cropping = cascade_cropping
        self.cascade_fill_color = cascade_fill_color
        self.cascade_outline_color = cascade_outline_color
        self.cascade_width = cascade_width
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.__title_dimensions: Dimensions = Dimensions(0, 0)


    @property
    def glass_commands(self) -> ImageMagickCommands:

        # Center of the rectangle/image
        center = Coordinate(self.WIDTH / 2, self.HEIGHT / 2)

        width = self.__title_dimensions.width + 50 # 50px side margin
        height = self.__title_dimensions.height * ((self.cascade_count * 2) + 1) + 50

        rectangle = Rectangle(
            center - (width / 2, (height / 2) + 75),
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
            f'-fill "rgba(0, 0, 0, 0.3)"',
            f'-draw "roundrectangle {rectangle} 25,25"',
        ]


    @property
    def cascading_text_commands(self) -> ImageMagickCommands:
        """"""

        # No cascading text, return empty commands
        if self.cascade_count <= 0 or not self.title_text:
            return []

        # Create the 1st image in the image stack as the reference
        # cascade image for later copying and cropping. This NEEDS to be
        # deleted from the final image
        commands = [
            fr'\(',
            f'-background none',
            f'-fill "{self.cascade_fill_color}"',
            f'-stroke "{self.cascade_outline_color}"',
            f'-strokewidth {self.cascade_width}',
            f'label:"{self.title_text}"',
            # Remove any white space padding
            f'-trim',
            # Repage so that future crops aren't misaligned
            f'+repage',
            fr'\)',
        ]

        # Add each cascade effect
        crop_heights = [float(c) for c in self.cascade_cropping.split(',')]
        for cascade_index in range(self.cascade_count):
            # Get crop amount for this cascade, defaulting to the last
            # one specified OR 50% if one was not specified
            try:
                crop = crop_heights[cascade_index]
            except IndexError:
                crop = crop_heights[-1] or 50

            # Offset to the center of the cropped image. Formula was
            # derived where 100% crop would result in 0px offset, and a
            # 50% crop would result in a half-height offset
            dy = self.__title_dimensions.height * (0.5 - (crop / 100 / 2)) \
                + (self.__title_dimensions.height * (cascade_index + 1))

            # Add top cascade
            commands.extend([
                # Add a new image to the stack
                fr'\(',
                # Clone the reference outline image
                f'-clone 1',
                # Crop the top part of the reference image
                f'-gravity north',
                f'-crop 0x{crop}%',
                # On the first cascade, clone the base iamge, all other
                # passes just grab the most recent cascade on the stack
                f'-clone {0 if cascade_index == 0 else (cascade_index * 2) + 1}',
                # Swap so that the text image is composed atop the reference
                f'+swap',
                f'-gravity center',
                f'-geometry +0-{dy}',
                f'-composite',
                fr'\)',
            ])

            # Add bottom cascase
            commands.extend([
                # Add a new image to the stack
                fr'\(',
                # Clone the reference outline image
                f'-clone 1',
                # Crop the bottom part of the reference image
                f'-gravity south',
                f'-crop 0x{crop}%',
                # Always clone the most recent cascade on the stack
                f'-clone {(cascade_index + 1) * 2}',
                # Swap so that the text image is composed atop the reference
                f'+swap',
                f'-gravity center',
                f'-geometry +0+{dy}',
                f'-composite',
                fr'\)',
            ])

        # TODO: handle multi-line text by only cascading the first and last line
        # of text. This will require two reference images on the stack, and 
        # some redoing of the image height calculations..

        # Delete the original base image (as its now merged in the last
        # cascade on the stack), and the reference cascade image
        stack_ids = range((self.cascade_count * 2) + 1)
        commands.append('-delete ' + ','.join(map(str, stack_ids)))

        return commands


    @property
    def alt_text_commands(self) -> ImageMagickCommands:
        """

        """

        # No alt text, return empty commands
        if not self.alt_text:
            return []

        # Position the alt text on the left side of the width
        dx = (self.WIDTH - self.__title_dimensions.width) / 2 - 8 # 8px margin
        dy = self.__title_dimensions.height * (self.cascade_count + 0.5) + 50

        size = 40 * self.episode_text_font_size

        return [
            f'-font "{self.TITLE_FONT}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {size}',
            f'-gravity west',
            f'-annotate +{dx}-{dy} "{self.alt_text}"',
        ]


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

        # Position the alt text on the left side of the text
        dx = (self.WIDTH - self.__title_dimensions.width) / 2 + 8 # 8px margin
        dy = self.__title_dimensions.height * (self.cascade_count + 0.5) + 50
        size = 40 * self.episode_text_font_size

        return [
            f'-font "{self.TITLE_FONT}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {size}',
            f'-gravity east',
            f'-annotate +{dx}-{dy} "{index_text}"',
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the title text to the image. This will always
        merge the title text into the 0th image in the image stack.
        """

        # No title text, return blank commands
        if not self.title_text:
            return []
 
        interline_spacing = self.font_interline_spacing
        interword_spacing = 30 + self.font_interword_spacing
        kerning = 1 * self.font_kerning
        size = 120 * self.font_size
        y_pos = 0 + self.font_vertical_shift

        return [
            fr'\(',
            f'-background none',
            f'-fill "{self.font_color}"',
            f'-font "{self.font_file}"',
            f'-interline-spacing {interline_spacing}',
            f'-interword-spacing {interword_spacing}',
            f'-kerning {kerning}',
            f'-pointsize {size}',
            f'-gravity center',
            f'label:"{self.title_text}"',
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
                ...
            ):
                if extra in extras:
                    del extras[extra]


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

        custom_extras = (
            ...
        )

        return (custom_extras
            or ((font.color != CascadeTitleCard.TITLE_COLOR)
            or (font.file != CascadeTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.vertical_shift != 0))
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

        # Pre-compute the dimensions of the title text as it is used
        # in many commands
        self.__title_dimensions = self.image_magick.get_text_label_dimensions(
            self.title_text_commands[1:-4],
            density=100,
        )

        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            f'-density 100',
            # Apply styling
            *self.resize_and_style,
            # Add all card components
            *self.glass_commands,
            *self.alt_text_commands,
            *self.index_text_commands,
            *self.title_text_commands,
            *self.cascading_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])
