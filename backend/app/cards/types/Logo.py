from pathlib import Path
from typing import Annotated, Any, Self

from pydantic import Field, FilePath, model_validator

from app.cards.base import (
    BaseCardType,
    CardDocumentation,
    CardTypeDescription,
    DefaultCardConfig,
    Extra,
    ImageMagickCommands,
    ImageStack,
    PreviewCard,
    add_cli,
)
from app.schemas.base import (
    BaseCardModel,
    BaseCardTypeCustomFontAllText,
    FontSize,
)


class LogoTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces logo-centric
    title cards, primarily for the purpose of reality TV shows.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Logo',
        identifier='logo',
        example='/public/cards/logo.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Logo Size',
                identifier='logo_size',
                description='How much to scale the size of the logo',
                tooltip='Number ><v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Logo Horizontal Shift',
                identifier='logo_horizontal_shift',
                description='Horizontal shift to apply to the logo',
                tooltip=(
                    'Positive values to shift the logo left, negative values '
                    'shift it right. Default is <v>0</v>. Unit is pixels.'
                ),
                default=0,
            ),
            Extra(
                name='Logo Vertical Shift',
                identifier='logo_vertical_shift',
                description='Vertical shift to apply to the logo',
                tooltip=(
                    'Positive values to shift the logo down, negative values '
                    'shift it up. Default is <v>0</v>. Unit is pixels.'
                ),
                default=0,
            ),
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>#CFCFCF</c>.',
                default='#CFCFCF',
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
                    'Additional vertical shift to apply to the episode text.'
                ),
                tooltip='Default is <v>0</v>. Unit is pixels.',
                default=0,
            ),
            Extra(
                name='Background Color',
                identifier='background',
                description='Background color to use behind the logo',
                tooltip=(
                    'Ignored if a background image is used. Default is '
                    '<c>black</c>.'
                ),
                default='black',
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
                tooltip='Default is <v>•</v>.',
                default='•',
            ),
            Extra(
                name='Background Image Enabling',
                identifier='use_background_image',
                description='Whether to use a background image (not color)',
                tooltip=(
                    'Either <v>True</v>, or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
                allowed_values=['True', 'False'],
                default='False',
            ),
            Extra(
                name='Stroke Text Color',
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
                    '<v>False</v>.'
                ),
                allowed_values=['True', 'False'],
                default='False',
            ),
            Extra(
                name='Blur Image Only',
                identifier='blur_only_image',
                description='Whether to only blur the background image',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, the '
                    'logo is not blurred. Default is <v>False</v>.'
                ),
                allowed_values=['True', 'False'],
                default='False',
            ),
        ],
        description=[
            'Variation of the Standard title card featuring a central logo.',
            'This card is intended to be used for very "spoilery" series, such '
            'as Reality TV shows.', 'The background of this card can either be '
            'a solid color or an image.', 'If a background image is desired, it'
            ' is recommended to use an Art Un/Watched Style.',
        ]
    )

    REF_DIRECTORY: Annotated[
        Path,
        'Directory where all reference files used by this card are stored'
    ] = BaseCardType.BASE_REF_DIRECTORY / 'standard'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=REF_DIRECTORY / 'Sequel-Neue.otf',
        font_color='#EBEBEB',
        font_case='upper',
        font_replacements={
            '[': '(', ']': ')', '(': '[', ')': ']', '―': '-', '…': '...'
        },
        title_max_line_width=32,
        title_max_line_count=2,
        title_split_style='bottom',
        uses_source_images=False,
    )

    """Default fonts and color for series count text"""
    SEASON_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Semibold.otf'
    EPISODE_COUNT_FONT = REF_DIRECTORY / 'Proxima Nova Regular.otf'
    SERIES_COUNT_TEXT_COLOR = '#CFCFCF'

    """Source path for the gradient image overlaid over all title cards"""
    __GRADIENT_IMAGE = REF_DIRECTORY / 'gradient.png'

    __slots__ = (
        'background',
        'blur_only_image',
        'episode_text',
        'episode_text_color',
        'episode_text_font_size',
        'episode_text_vertical_shift',
        'font_color',
        'font_file',
        'font_kerning',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_size',
        'font_stroke_width',
        'font_vertical_shift',
        'hide_season_text',
        'hide_episode_text',
        'omit_gradient',
        'output_file',
        'logo',
        'logo_horizontal_shift',
        'logo_size',
        'logo_vertical_shift',
        'season_text',
        'separator',
        'source_file',
        'stroke_color',
        'title_text',
        'use_background_image',
    )

    def __init__(self, *,
            card_file: Path,
            title_text: str,
            logo_file: Path,
            # Text
            season_text: str,
            episode_text: str,
            source_file: Path,
            hide_season_text: bool = False,
            hide_episode_text: bool = False,
            # Font
            font_color: str = CardConfig.font_color,
            font_file: str = str(CardConfig.font_file),
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
            background: str = 'black',
            blur_only_image: bool = False,
            episode_text_color: str = SERIES_COUNT_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            episode_text_vertical_shift: int = 0,
            logo_horizontal_shift: int = 0,
            logo_size: float = 1.0,
            logo_vertical_shift: int = 0,
            omit_gradient: bool = True,
            separator: str = '•',
            stroke_color: str = 'black',
            use_background_image: bool = False,
            **unused: Any,
        ) -> None:
        """Construct a new instance of this card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Get source file if indicated
        self.use_background_image = use_background_image
        self.blur_only_image = blur_only_image
        self.logo = logo_file
        self.source_file = source_file
        self.output_file = card_file

        # Ensure characters that need to be escaped are
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text

        # Font attributes
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.background = background
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.episode_text_vertical_shift = episode_text_vertical_shift
        self.omit_gradient = omit_gradient
        self.logo_horizontal_shift = logo_horizontal_shift
        self.logo_size = logo_size
        self.logo_vertical_shift = logo_vertical_shift
        self.separator = separator
        self.stroke_color = stroke_color


    @property
    def logo_commands(self) -> ImageMagickCommands:
        """Subcommands to add the logo to the Card."""

        # Post-resize max dimensions of the logo
        max_width = 1875 * self.logo_size
        max_height = 1030 * self.logo_size

        # Determine current dimensions of the logo
        current_width, current_height = self.image_magick.get_image_dimensions(
            self.logo
        )

        # Determine dimensions post-resizing
        scale = max_height / current_height  # -resize x{max_height}
        if current_width * scale > max_width:# -resize {max_width}x{max_height}>
            scale = max_width / current_width

        # Resize logo, get resized height to determine offset
        offset = 60 + ((1030 - (current_height * scale)) // 2) \
            + self.logo_vertical_shift

        return [
            f'-gravity north',
            *ImageStack(
                f'"{self.logo.resolve()}"',
                f'-resize x{max_height}',
                fr'-resize {max_width}x{max_height}\>',
            ),
            f'-geometry {self.logo_horizontal_shift:+}{offset:+}',
            f'-composite',
        ]


    @property
    def index_commands(self) -> ImageMagickCommands:
        """Subcommand for adding the index text to the source image."""

        # All index text is disabled, return blank command
        if self.hide_season_text and self.hide_episode_text:
            return []

        size = 67.75 * self.episode_text_font_size
        y = 697.2 + self.episode_text_vertical_shift

        # Only add season text
        if self.hide_episode_text:
            return [
                f'-kerning 5.42',
                f'-pointsize {size:.1f}',
                f'-interword-spacing 14.5',
                f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
                f'-gravity center',
                f'-fill black',
                f'-stroke black',
                f'-strokewidth 6',
                f'-annotate +0{y:+} "{self.season_text}"',
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'-strokewidth 0.75',
                f'-annotate +0{y:+} "{self.episode_text}"',
            ]

        # Only add episode text
        if self.hide_season_text:
            return [
                f'-kerning 5.42',
                f'-pointsize {size:.1f}',
                f'-interword-spacing 14.5',
                f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
                f'-gravity center',
                f'-fill black',
                f'-stroke black',
                f'-strokewidth 6',
                f'-annotate +0{y:+} "{self.episode_text}"',
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'-strokewidth 0.75',
                f'-annotate +0{y:+} "{self.episode_text}"',
            ]

        return [
            # Global text effects
            f'-background transparent',
            f'-gravity center',
            f'-kerning 5.42',
            f'-pointsize {size:.1f}',
            f'-interword-spacing 14.5',
            # Black stroke behind primary text
            *ImageStack(
                f'-fill black',
                f'-stroke black',
                f'-strokewidth 6',
                # Add season text
                f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
                f'label:"{self.season_text} {self.separator}"',
                # Add episode text
                f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
                f'label:"{self.episode_text}"',
                # Combine season+episode text into one "image"
                f'+smush 25',
                f'-trim',
            ),
            # Add season+episode text "image" to source image
            f'-geometry +0{y:+}',
            f'-composite',
            # Primary text
            *ImageStack(
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'-strokewidth 0.75',
                # Add season text
                f'-font "{self.SEASON_COUNT_FONT.resolve()}"',
                f'label:"{self.season_text} {self.separator}"',
                # Add episode text
                f'-font "{self.EPISODE_COUNT_FONT.resolve()}"',
                f'label:"{self.episode_text}"',
                f'+smush 30',
                f'-trim',
            ),
            # Add text to source image
            f'-geometry +0{y:+}',
            f'-composite',
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the title text to the image."""

        # No title text, return empty commands
        if not self.title_text:
            return []

        # Font customizations
        vertical_shift = 245 + self.font_vertical_shift
        font_size = 157.41 * self.font_size
        interline_spacing = -22 + self.font_interline_spacing
        interword_spacing = 50 + self.font_interword_spacing
        kerning = -1.25 * self.font_kerning
        stroke_width = 3.0 * self.font_stroke_width

        return [
            # Global title text options
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-kerning {kerning}',
            f'-interword-spacing {interword_spacing}',
            f'-interline-spacing {interline_spacing}',
            f'-pointsize {font_size}',
            # Stroke behind title text
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
            # Title text
            f'-fill "{self.font_color}"',
            f'-annotate +0+{vertical_shift} "{self.title_text}"',
        ]


    def create(self) -> None:
        """
        Make the necessary ImageMagick and system calls to create this
        object's defined title card.
        """

        # Sub-command to add source file or create colored background
        if self.use_background_image:
            blur_command = ''
            if self.blur and self.blur_only_image:
                blur_command = f'-blur {self.BLUR_PROFILE}'
            background_command = [
                f'"{self.source_file.resolve()}"',
                *self.resize,
                blur_command,
            ]
        else:
            background_command = [
                f'-set colorspace sRGB',
                f'-size "{self.TITLE_CARD_SIZE}"',
                f'xc:"{self.background}"',
            ]

        # Sub-command to optionally add gradient
        gradient_command = []
        if not self.omit_gradient:
            gradient_command = [
                f'"{self.__GRADIENT_IMAGE.resolve()}"',
                f'-composite',
            ]

        # Sub-command to style the overall image if indicated
        style_command = []
        if self.blur_only_image and self.grayscale:
            style_command = [
                f'-colorspace gray',
                f'-set colorspace sRGB',
            ]
        elif not self.blur_only_image:
            style_command = self.style

        self.image_magick.run([
            f'convert',
            # Add background image or color
            *background_command,
            # Overlay logo
            *self.logo_commands,
            # Optionally overlay gradient
            *gradient_command,
            # Apply style that is applicable to entire image
            *style_command,
            # Title text
            *self.title_text_commands,
            # Add episode or season+episode "image"
            *self.index_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[BaseCardModel]:
    """Get the Pydantic validator class for this card type."""

    class CardModel(BaseCardTypeCustomFontAllText):
        source_file: Path | None = None # type: ignore
        logo_file: FilePath
        font_color: str = LogoTitleCard.CardConfig.font_color
        font_file: FilePath = LogoTitleCard.CardConfig.font_file
        background: str = 'black'
        blur_only_image: bool = False
        episode_text_color: str = LogoTitleCard.SERIES_COUNT_TEXT_COLOR
        episode_text_font_size: FontSize = 1.0
        episode_text_vertical_shift: int = 0
        logo_horizontal_shift: int = 0
        logo_size: FontSize = 1.0
        logo_vertical_shift: int = 0
        omit_gradient: bool = True
        separator: str = '•'
        stroke_color: str = 'black'
        use_background_image: bool = False

        @model_validator(mode='after')
        def validate_source_file(self) -> Self:
            """
            Validate that a source file is provided if one is required.
            """

            if (self.use_background_image and (
                not self.source_file
                or not self.source_file.exists()
            )):
                raise ValueError(
                    f'Source file ({self.source_file}) indicated and does '
                    f'not exist'
                )

            return self

    return CardModel


add_cli(
    __name__,
    LogoTitleCard,
    get_validator_model(),
    documentation=CardDocumentation(
        static_variables={
            'title_text': 'The Marooning',
            'season_text': 'SEASON 1',
            'episode_text': 'EPISODE 1',
        },
        cards=[
            PreviewCard(
                filename='background_color',
                variables={'background': 'DarkSlateGray4'},
            ),
            PreviewCard(
                filename='episode_text_color',
                variables={'episode_text_color': 'Gold2'},
            ),
            PreviewCard(
                filename='episode_text_font_size',
                variables={'episode_text_font_size': 1.3},
            ),
            PreviewCard(
                filename='episode_text_vertical_shift',
                variables={'episode_text_vertical_shift': 20},
            ),
            PreviewCard(
                filename='logo_size',
                variables={'logo_size': 0.8},
            ),
            PreviewCard(
                filename='separator',
                variables={'separator': '//'},
            ),
            PreviewCard(
                filename='stroke_color',
                variables={'stroke_color': 'red'},
            ),
            PreviewCard(
                filename='omit_gradient',
                variables={
                    'omit_gradient': True,
                    'use_background_image': True,
                },
            ),
            PreviewCard(
                filename='blur_only_image_true',
                variables={
                    'blur_only_image': True,
                    'use_background_image': True,
                    'blur': True,
                },
            ),
            PreviewCard(
                filename='blur_only_image_false',
                variables={
                    'blur_only_image': False,
                    'use_background_image': True,
                    'blur': True,
                },
            ),
            PreviewCard(
                filename='use_background_image',
                variables={'use_background_image': True},
            ),
            PreviewCard(
                filename='logo_horizontal_shift',
                variables={'logo_horizontal_shift': 20},
            ),
            PreviewCard(
                filename='logo_vertical_shift',
                variables={'logo_vertical_shift': 20},
            ),
        ]
    ),
)
