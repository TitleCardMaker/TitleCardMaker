from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import Field, FilePath

from app.interfaces.magick import Dimensions
from app.schemas.base import Base, BaseCardTypeCustomFontAllText
from app.cards.base import (
    BaseCardType,
    CardTypeDescription,
    Coordinate,
    Extra,
    ImageMagickCommands,
    Rectangle,
)


EpisodeTextLocation = Literal['compact', 'fixed']


class MarvelTitleCard(BaseCardType):
    """
    This class describes a CardType that produces title cards intended
    to match RedHeadJedi's style of Marvel Cinematic Universe posters.
    These cards feature a white border on the left, top, and right
    edges, and a black box on the bottom. All text is displayed in the
    bottom box.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Marvel',
        identifier='marvel',
        example='/public/cards/marvel.webp',
        creators=['CollinHeist', 'RedHeadJedi'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Border Color',
                identifier='border_color',
                description='Color of the border',
                tooltip=(
                    'Color of the left/top/right borders. Default is '
                    '<c>white</c>.'
                ),
                default='white',
            ),
            Extra(
                name='Border Size',
                identifier='border_size',
                description='Size of the border',
                tooltip=(
                    'Value greater than <v>0</v>. Default is <v>55</v>. Unit '
                    'is pixels.'
                ),
                default=55,
            ),
            Extra(
                name='Border Toggle',
                identifier='hide_border',
                description='Whether to hide the left/top/right borders',
                tooltip=(
                    'Whether to Either <v>True</v> or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
                default='False',
            ),
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>#C9C9C9</c>.',
                default='#C9C9C9',
            ),
            Extra(
                name='Episode Text Location',
                identifier='episode_text_location',
                description='Where to position the episode text.',
                tooltip=(
                    'Either <v>compact</v> to put the text directly next to '
                    'the title text; or <v>fixed</v> to put the text on the '
                    'outer edges of the text box. Default is <v>fixed</v>.'
                ),
                default='fixed',
            ),
            Extra(
                name='Fit Text',
                identifier='fit_text',
                description='Whether to dynamically adjust the font size.',
                tooltip=(
                    'Whether to scale the font size so that text always fits '
                    'in the bounds of the text box. Either <v>True</v> or '
                    '<v>False</v>. Default is <v>True</v>.'
                ),
                default='True',
            ),
            Extra(
                name='Text Box Color',
                identifier='text_box_color',
                description='Color of the (bottom) text box.',
                tooltip='Default is <c>black</c>.',
                default='black',
            ),
            Extra(
                name='Text Box Height',
                identifier='text_box_height',
                description='Height of the (bottom) text box.',
                tooltip='Default is <v>200</v>. Unit is pixels.',
                default=200,
            ),
        ],
        description=[
            "Card type styled to match RedHeadJedi's MCU poster set. These "
            'cards feature a white border on the outer edges, with all text '
            'on the bottom of the image.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'marvel'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 25,
        'max_line_count': 1,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Qualion ExtraBold.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_COLOR = '#C9C9C9'
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Qualion ExtraBold.ttf'

    """How thick the border is (in pixels)"""
    DEFAULT_BORDER_SIZE = 55

    """Color of the border"""
    DEFAULT_BORDER_COLOR = 'white'

    """Color of the text box"""
    DEFAULT_TEXT_BOX_COLOR = 'black'

    """Height of the text box (in pixels)"""
    DEFAULT_TEXT_BOX_HEIGHT = 200

    __slots__ = (
        'border_color',
        'border_size',
        'episode_text',
        'episode_text_color',
        'episode_text_position',
        'fit_text',
        'font_file',
        'font_size',
        'font_color',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_kerning',
        'font_vertical_shift',
        'hide_border',
        'hide_season_text',
        'hide_episode_text',
        'output_file',
        'season_text',
        'source_file',
        'title_text',
        'text_box_color',
        'text_box_height',
        'font_size_modifier',
    )

    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = False,
            hide_episode_text: bool = False,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            border_color: str = DEFAULT_BORDER_COLOR,
            border_size: int = DEFAULT_BORDER_SIZE,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_location: EpisodeTextLocation = 'fixed',
            fit_text: bool = True,
            hide_border: bool = False,
            text_box_color: str = DEFAULT_TEXT_BOX_COLOR,
            text_box_height: int = DEFAULT_TEXT_BOX_HEIGHT,
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
        self.font_size_modifier = 1.0
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.border_color = border_color
        self.border_size = border_size
        self.episode_text_color = episode_text_color
        self.episode_text_position = episode_text_location
        self.fit_text = fit_text
        self.hide_border = hide_border
        self.text_box_color = text_box_color
        self.text_box_height = text_box_height


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding title text to the source image."""

        # No title text, or not being shown
        if not self.title_text:
            return []

        # Font characteristics
        size = 150 * self.font_size * self.font_size_modifier
        kerning = 1.0 * self.font_kerning * self.font_size_modifier
        # When the modifier is <1.0, the text can appear shifted down - adjust
        vertical_shift = 820 \
            + self.font_vertical_shift \
            - ((self.font_size_modifier - 1.0) * -10)
            # Map the modifier [0.0, 1.0] -> [-10, 0] pixels

        return [
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {size}',
            f'-kerning {kerning}',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-gravity center',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
        ]


    def season_text_commands(self,
            title_text_dimensions: Dimensions,
        ) -> ImageMagickCommands:
        """
        Subcommands for adding episode text to the source image.

        Args:
            title_text_dimensions: Dimensions of the title text. For
                positioning the text in compact positioning mode.

        Returns:
            List of ImageMagick commands.
        """

        # Return if not showing text
        if self.hide_season_text:
            return []

        # Vertical positioning of text
        y_position = 810 + self.font_vertical_shift

        text_command = []
        if self.episode_text_position == 'compact':
            x_position = (self.WIDTH + title_text_dimensions.width) / 2 + 20
            text_command = [
                f'-gravity east',
                f'-annotate {x_position:+}{y_position:+} "{self.season_text}"',
            ]
        else:
            text_command = [
                f'-gravity west',
                f'-annotate +{self.border_size}{y_position:+} "{self.season_text}"',
            ]

        font_size = 70 * self.font_size_modifier

        return [
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {font_size}',
            f'-kerning 1',
            f'-interword-spacing 15',
            *text_command,
        ]


    def episode_text_commands(self,
            title_text_dimensions: Dimensions,
        ) -> ImageMagickCommands:
        """
        Subcommands for adding episode text to the source image.

        Args:
            title_text_dimensions: Dimensions of the title text. For
                positioning the text in compact positioning mode.

        Returns:
            List of ImageMagick commands.
        """

        # Return if not showing text
        if self.hide_episode_text:
            return []

        # Vertical positioning of text
        y_position = 810 + self.font_vertical_shift

        text_command = []
        if self.episode_text_position == 'compact':
            x_position = (self.WIDTH + title_text_dimensions.width) / 2 + 20
            text_command = [
                f'-gravity west',
                f'-annotate {x_position:+}{y_position:+} "{self.episode_text}"',
            ]
        else:
            text_command = [
                f'-gravity east',
                f'-annotate +{self.border_size}{y_position:+} "{self.episode_text}"',
            ]

        font_size = 70 * self.font_size_modifier

        return [
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {font_size}',
            f'-kerning 1',
            f'-interword-spacing 15',
            *text_command,
        ]


    def scale_text(self, title_text_dimensions: Dimensions) -> Dimensions:
        """
        Set the font size modifier to scale the title and index text and
        ensure it fits in the image.

        Args:
            title_text_dimensions: Dimensions of the title text for
                determining the scaling factor.

        Returns:
            New dimensions of the title text. If `fit_text` is False,
            or if the text is not scaled, then the original dimensions
            are returned.
        """

        # If not fitting text, return original dimensions
        if not self.fit_text:
            return title_text_dimensions

        # Get dimensions of season and episode text
        season_text_dimensions = self.image_magick.get_text_dimensions(
            self.season_text_commands(title_text_dimensions),
            width='sum',
        )
        episode_text_dimensions = self.image_magick.get_text_dimensions(
            self.episode_text_commands(title_text_dimensions),
            width='sum',
        )

        # Check left/right separately for overlap
        half_title = title_text_dimensions.width / 2
        left_width = half_title + season_text_dimensions.width
        right_width = half_title + episode_text_dimensions.width

        # Add margin
        left_width += 0 if self.hide_season_text else 40
        right_width += 0 if self.hide_episode_text else 40

        # If either side is too wide, scale by largest size
        max_width = (self.WIDTH / 2) - self.border_size
        if left_width > max_width or right_width > max_width:
            self.font_size_modifier = min(
                max_width / left_width,
                max_width / right_width,
            )

        # If font scalar was modified, recalculate+return text dimensions
        if self.font_size_modifier < 1.0:
            return self.image_magick.get_text_dimensions(
                self.title_text_commands,
            )

        # Scalar unmodified, return original dimensions
        return title_text_dimensions


    @property
    def border_commands(self) -> ImageMagickCommands:
        """Subcommands to add the border to the image."""

        # Border is not being shown, skip
        if self.hide_border:
            return []

        # Get each rectangle
        left_rectangle = Rectangle(
            Coordinate(0, 0),
            Coordinate(self.border_size, self.HEIGHT)
        )
        top_rectangle = Rectangle(
            Coordinate(0, 0),
            Coordinate(self.WIDTH, self.border_size)
        )
        right_rectangle = Rectangle(
            Coordinate(self.WIDTH - self.border_size, 0),
            Coordinate(self.WIDTH, self.HEIGHT)
        )

        return [
            f'-fill "{self.border_color}"',
            left_rectangle.draw(),
            top_rectangle.draw(),
            right_rectangle.draw(),
        ]


    @property
    def bottom_border_commands(self) -> ImageMagickCommands:
        """Subcommands to add the bottom border to the image."""

        rectangle = Rectangle(
            Coordinate(0, self.HEIGHT - self.text_box_height),
            Coordinate(self.WIDTH, self.HEIGHT)
        )

        return [
            f'-fill "{self.text_box_color}"',
            rectangle.draw(),
        ]


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        border_size = 0 if self.hide_border else self.border_size
        processing = [
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Resize to only fit in the bounds of the border
            f'-resize {self.WIDTH - (border_size)}x',
            f'-extent {self.TITLE_CARD_SIZE}',
        ]

        # Get the dimensions of the title and index text
        title_text_dimensions = self.image_magick.get_text_dimensions(
            self.title_text_commands,
        )

        # Apply any font scaling to fit text
        title_text_dimensions = self.scale_text(title_text_dimensions)

        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            *processing,
            # Add borders
            *self.border_commands,
            *self.bottom_border_commands,
            # Add text
            *self.title_text_commands,
            *self.season_text_commands(title_text_dimensions),
            *self.episode_text_commands(title_text_dimensions),
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file, pre_processing=processing),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[Base]:
    """Get the Pydantic validator class for this card type."""

    class CardModel(BaseCardTypeCustomFontAllText):
        font_file: FilePath = MarvelTitleCard.TITLE_FONT # type: ignore
        font_color: str = MarvelTitleCard.TITLE_COLOR
        border_color: str = MarvelTitleCard.DEFAULT_BORDER_COLOR
        border_size: Annotated[
            int,
            Field(gt=0)
        ] = MarvelTitleCard.DEFAULT_BORDER_SIZE
        episode_text_color: str = MarvelTitleCard.EPISODE_TEXT_COLOR
        episode_text_location: EpisodeTextLocation = 'fixed'
        fit_text: bool = True
        hide_border: bool = False
        text_box_color: str = MarvelTitleCard.DEFAULT_TEXT_BOX_COLOR
        text_box_height: Annotated[
            int,
            Field(gt=0)
        ] = MarvelTitleCard.DEFAULT_TEXT_BOX_HEIGHT

    return CardModel
