from pathlib import Path
from random import random
from typing import Annotated, Any, Self

from pydantic import Field, FilePath, model_validator

from app.info.episode import EpisodeInfo
from app.schemas.base import Base, BaseCardTypeCustomFontAllText
from modules.BaseCardType import (
    BaseCardType,
    CardTypeDescription,
    Dimensions,
    Extra,
    ImageMagickCommands,
    Shadow,
)


class CalligraphyTitleCard(BaseCardType):
    """
    CardType that produces title cards featuring a prominet logo, with
    all text using a handwritten calligraphy font. A matte paper texture
    is applied to the image.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Calligraphy',
        identifier='calligraphy',
        example='/public/cards/calligraphy.webp',
        creators=['CollinHeist', '/u/Recker_Man'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Texture Toggle',
                identifier='add_texture',
                description='Whether to add the "grain" texture',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is <v>True</v>.'
                ),
                default='True',
            ),
            Extra(
                name='Texture Randomization Toggle',
                identifier='randomize_texture',
                description='Whether to randomly reposition the texture overlay',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is <v>True</v>.'
                ),
                default='True',
            ),
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is to match the Font color.',
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>',
                default=1.0,
            ),
            Extra(
                name='Offset Title Toggle',
                identifier='offset_titles',
                description='Whether to offset multi-line titles',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If enabled, then '
                    'multi-line titles will be adjusted so the second line '
                    'hangs below the first. Default is <v>True</v>.'
                ),
                default='True',
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
                tooltip='Default is <v>-</v>.',
                default='-',
            ),
            Extra(
                name='Shadow Color',
                identifier='shadow_color',
                description='Color of the text drop shadow.',
                tooltip='Default is <c>black</c>.',
                default='black',
            ),
            Extra(
                name='Logo Size',
                identifier='logo_size',
                description='Scalar for how much to scale the size of the logo',
                tooltip='Number ><v>0.0</v>. Default is <v>1.0</v>',
                default=1.0,
            ),
            Extra(
                name='Deep Blur Unwatched Toggle',
                identifier='deep_blur_if_unwatched',
                description=(
                    'Whether to apply a stronger blur to unwatched Episodes'
                ),
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Applies a more '
                    'spoiler-free blurring if a Blur style is used and the '
                    'Episode is unwatched. Default is <v>True</v>.'
                ),
                default='True',
            ),
        ],
        description=[
            'Stylized Card featuring a prominent logo and all text in a hand-'
            'written calligraphy font. A subtle matte paper texture is applied '
            'to the image.', 'Looks best when a blurred/grayscale style is '
            'utilized as the text and texture are more pronounced.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'calligraphy'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 20,
        'max_line_count': 2,
        'style': 'forced even',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'SlashSignature.ttf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'source'
    FONT_REPLACEMENTS = {}

    """How to format episode text"""
    EPISODE_TEXT_FORMAT = 'Episode {titlecase(to_cardinal(episode_number))}'

    """Texture image to compose with"""
    TEXTURE_IMAGE = REF_DIRECTORY / 'texture.jpg'

    """Custom blur profile"""
    BLUR_PROFILE = '0x10'

    """Blur profile to use if deep blurring is enabled"""
    DEEP_BLUR_PROFILE = BaseCardType.BLUR_PROFILE

    __slots__ = (
        'add_texture',
        'deep_blur',
        'episode_text_color',
        'episode_text_font_size',
        'episode_text',
        'font_color',
        'font_file',
        'font_size',
        'font_interline_spacing',
        'font_vertical_shift',
        'hide_episode_text',
        'hide_season_text',
        'font_interword_spacing',
        'font_kerning',
        'logo_file',
        'logo_size',
        'output_file',
        'randomize_texture',
        'season_text',
        'separator',
        'shadow_color',
        'source_file',
        'title_text',
    )

    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            season_text: str,
            episode_text: str,
            hide_season_text: bool = True,
            hide_episode_text: bool = False,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            logo_file: Path | None = None,
            watched: bool = True,
            blur: bool = False,
            grayscale: bool = False,
            add_texture: bool = True,
            deep_blur_if_unwatched: bool = True,
            episode_text_color: str = TITLE_COLOR,
            episode_text_font_size: float = 1.0,
            logo_size: float = 1.0,
            offset_titles: bool = True,
            randomize_texture: bool = True,
            separator: str = '-',
            shadow_color: str = 'black',
            **unused: Any,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        self.source_file = source_file
        self.output_file = card_file
        self.logo_file = logo_file

        # Ensure characters that need to be escaped are
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text

        # Offset multi-line titles if indicated
        if offset_titles:
            title_text = self.__offset_title(title_text)
        self.title_text = self.image_magick.escape_chars(title_text)

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.add_texture = add_texture
        self.deep_blur = blur and deep_blur_if_unwatched and not watched
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.logo_size = logo_size
        self.randomize_texture = randomize_texture
        self.separator = separator
        self.shadow_color = shadow_color


    @staticmethod
    def SEASON_TEXT_FORMATTER(episode_info: EpisodeInfo) -> str:
        """
        Fallback season title formatter.

        Args:
            episode_info: Info of the Episode whose season text is being
                determined.

        Returns:
            'Specials' if the season number is 0; otherwise the cardinal
            version of the season number. If that's not possible, then
            just 'Season {x}'.
        """

        if episode_info.season_number == 0:
            return 'Specials'

        return 'Season {titlecase(to_cardinal(season_number))}'


    def __offset_title(self, title_text: str) -> str:
        """
        Apply indention / offset to the given title text.

        Args:
            title_text: Title to apply the offset to.

        Returns:
            Modified title text.
        """

        # Cannot offset single-line titles
        if '\n' not in title_text:
            return title_text

        # Split into separate lines
        lines = title_text.splitlines()

        # Don't offset if the bottom line is much longer than the first
        if (len(lines[1]) > len(lines[0]) * 2
            or len(lines[1]) > len(lines[0]) + 12):
            return title_text

        def limit(lower: int, value: int, upper: int) -> int:
            return max(lower, min(value, upper))

        offset_count = limit(3, len(lines[1]), 10)
        offset_count2 = 7 # limit(6, (len(lines[0]) // 2) + offset_count, 8)
        lines[0] = lines[0] + (' ' * offset_count)
        lines[1] = (' ' * offset_count2) + lines[1]
        title_text = '\n'.join(lines)

        return title_text


    def __get_logo_size(self) -> Dimensions:
        """
        Get the effective size of the logo as it is overlaid onto the
        image.

        Returns:
            Effective dimensions of the logo after having been scaled.
        """

        if self.logo_file is None:
            return Dimensions(0, 0)

        # Get base dimensions of the logo (before resizing)
        width, height = self.image_magick.get_image_dimensions(self.logo_file)

        # -resize 2800x
        scaled_w = 2800
        scaled_h = height * (scaled_w / width)

        # -resize x{750 * self.logo_size}>
        if scaled_h > (max_height := 750 * self.logo_size):
            downsize = max_height / scaled_h
            return Dimensions(scaled_w * downsize, scaled_h * downsize)

        return Dimensions(scaled_w, scaled_h)


    @property
    def texture_commands(self) -> ImageMagickCommands:
        """Subcommand to apply the texture image (if enabled)."""

        # Not adding texture, return
        if not self.add_texture:
            return []

        texture_command = [
            f'"{self.TEXTURE_IMAGE.resolve()}"',
        ]

        # If randomizing the texture, scale by random value
        if self.randomize_texture:
            random_height = (random() + 1.0) * self.HEIGHT
            texture_command = [
                fr'\( "{self.TEXTURE_IMAGE.resolve()}"',
                fr'-resize x{random_height} \)',
            ]

        return [
            *texture_command,
            f'-gravity center',
            f'-compose multiply',
            f'-composite',
            f'-compose over',
        ]


    @property
    def logo_commands(self) -> ImageMagickCommands:
        """Subcommand to add the logo (and drop shadow) to the image."""

        # Logo not specified or does not exist, return empty commands
        if not self.logo_file or not self.logo_file.exists():
            return []

        logo_height = 725 * self.logo_size

        base_command = [
            f'"{self.logo_file.resolve()}"',
            f'-resize 2800x',
            fr'-resize x{logo_height}\>',
        ]

        return self.add_drop_shadow(base_command, '95x10+0+35', 0, 0)


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommand for adding title text to the source image."""

        # No title text, or not being shown
        if len(self.title_text) == 0:
            return []

        # Font characteristics
        size = 160 * self.font_size
        interline_spacing = -70 + self.font_interline_spacing
        kerning = 1.0 * self.font_kerning
        vertical_shift = 600 + self.font_vertical_shift

        base_commands = [
            f'-background None',
            f'-font "{self.font_file}"',
            f'-pointsize {size}',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-fill "{self.font_color}"',
            f'label:"{self.title_text}"',
        ]

        return self.add_drop_shadow(
            base_commands,
            Shadow(opacity=95, sigma=2, x=0, y=17),
            x=0, y=vertical_shift,
            shadow_color=self.shadow_color,
        )


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """Subcommands for adding index text to the source image."""

        # Return if not showing text
        if self.hide_season_text and self.hide_episode_text:
            return []

        if self.hide_season_text:
            index_text = self.episode_text
        elif self.hide_season_text:
            index_text = self.season_text
        else:
            index_text = (
                f'{self.season_text} {self.separator} {self.episode_text}'
            )

        interline_spacing = -50 + self.font_interline_spacing
        kerning = 1.0 * self.font_kerning
        size = 75 * self.episode_text_font_size

        # Determine vertical offset - if no logo, place on top of image
        if not self.logo_file or not self.logo_file.exists():
            y = -750
        # Logo is provided, position just above logo
        else:
            _, logo_height = self.__get_logo_size()
            y = (-logo_height / 2) - 125 # 125px margin

        base_commands = [
            f'-background None',
            f'-font "{self.font_file}"',
            f'-pointsize {size}',
            f'-interline-spacing {interline_spacing}',
            f'-kerning {kerning}',
            f'-fill "{self.episode_text_color}"',
            f'label:"{index_text}"',
        ]

        return self.add_drop_shadow(
            base_commands, '95x2+0+12', x=0, y=y,
            shadow_color=self.shadow_color,
        )


    def create(self) -> None:
        """Create this object's defined Title Card."""

        style_commands = self.resize_and_style
        if self.deep_blur:
            style_commands = [
                *self.resize,
                # Optionally blur
                f'-blur {self.DEEP_BLUR_PROFILE}',
                # Optionally set gray colorspace
                f'-colorspace gray' if self.grayscale else '',
                # Reset to full colorspace
                f'-set colorspace sRGB',
            ]

        command = ' '.join([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *style_commands,
            # Add each layer
            *self.texture_commands,
            *self.logo_commands,
            *self.title_text_commands,
            *self.index_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])

        self.image_magick.run(command)


def get_validator_model() -> type[Base]:
    """Get the Pydantic validator class for this card type."""

    class CardModel(BaseCardTypeCustomFontAllText):
        season_text: str
        episode_text: str
        font_color: str = CalligraphyTitleCard.TITLE_COLOR
        font_file: FilePath = CalligraphyTitleCard.TITLE_FONT # type: ignore
        logo_file: Path
        watched: bool = False
        add_texture: bool = True
        deep_blur_if_unwatched: bool = True
        episode_text_color: str | None = None
        episode_text_font_size: Annotated[float, Field(ge=0.0)] = 1.0
        logo_size: Annotated[float, Field(ge=0.0)] = 1.0
        offset_titles: bool = True
        randomize_texture: bool = True
        separator: str = '-'
        shadow_color: str = 'black'

        @model_validator(mode='after')
        def assign_unassigned_color(self) -> Self:
            """Assign any unassigned colors to their default values."""

            if self.episode_text_color is None:
                self.episode_text_color = self.font_color

            return self

    return CardModel
