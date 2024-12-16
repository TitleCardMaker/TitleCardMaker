from pathlib import Path
from typing import TYPE_CHECKING, Literal

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
    _ITALIC_TITLE_FONT = REF_DIRECTORY / 'SpockEssAlt1-It.ttf'
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
    DEFAULT_CASCADE_ALPHAS: str = '66,33'
    DEFAULT_CASCADE_COUNT: int = 2
    DEFAULT_CASCASE_CROP: str = '66,33'
    DEFAULT_CASCADE_FILL_COLOR: str = 'transparent'
    DEFAULT_CASCADE_OUTLINE_COLOR: str = 'red'
    DEFAULT_CASCADE_WIDTH: int = 5
    DEFAULT_GLASS_COLOR: str = 'rgba(0,0,0,0.3)'
    DEFAULT_GLASS_EDGE_COLOR: str = 'rgba(12,12,12,0.4)'

    __slots__ = (
        'alt_text',
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
        self.alt_text = alt_text
        self.cascade_alphas = cascade_alphas
        self.cascade_count = int(cascade_count)
        self.cascade_cropping = cascade_cropping
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
            f'-fill "{self.glass_color}"',
            f'-stroke "{self.glass_edge_color}" -strokewidth 2',
            f'-draw "roundrectangle {rectangle} 25,25"',
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
        alphas = [float(a) / 100 for a in self.cascade_alphas.split(',')]
        crop_heights = [float(c) for c in self.cascade_cropping.split(',')]
        for cascade_index in range(self.cascade_count):
            # Get crop amount for this cascade, defaulting to the last
            # one specified OR 50% if one was not specified
            try:
                alpha = alphas[cascade_index]
                crop = crop_heights[cascade_index]
            except IndexError:
                alpha = alphas[-1] or str(100 / (2 ** (cascade_index + 1)))
                crop = crop_heights[-1] or 50

            # Offset to the center of the cropped image. Formula was
            # derived where 100% crop would result in 0px offset, and a
            # 50% crop would result in a half-height offset
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
                # f'-clone {0 if cascade_index == 0 else (cascade_index * 2) + 1}',
                # Swap so that the text image is composed atop the reference
                f'+swap',
                f'-gravity center',
                f'-geometry +0-{top_dy}',
                f'-composite',
                fr'\)',
            ])

            # Add bottom cascase
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
                # f'-clone {(cascade_index + 1) * 2}',
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
            f'-font "{self.TITLE_FONT}"',
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
