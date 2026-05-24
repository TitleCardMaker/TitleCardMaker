from pathlib import Path
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import Field, FilePath, model_validator

from app.cards.base import (
    BaseCardType,
    CardTypeDescription,
    DefaultCardConfig,
    Extra,
    ImageMagickCommands,
    ImageStack,
    Shadow,
    get_extra_validation_error,
)
from app.magick.cli import CardDocumentation, PreviewCard, add_card_cli
from app.schemas.base import (
    BaseCardModel,
    BaseCardTypeCustomFontAllText,
    FontSize,
)

LogoPosition = Literal['omit', 'top left', 'top right', 'bottom right']


class AnimeTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards in
    the anime-styled cards designed by Reddit user /u/Recker_Man. These
    cards support custom fonts, and optional kanji text.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Anime',
        identifier='anime',
        example='/public/cards/anime.webp',
        creators=['/u/Recker_Man', 'CollinHeist', 'Reicha7'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Stroke Color',
                identifier='episode_stroke_color',
                description='Color of the text stroke for the episode text',
                tooltip='Default is <c>black</c>.',
                default='black',
            ),
            Extra(
                name='Kanji Text',
                identifier='kanji',
                description='Japanese text placed above title text',
                tooltip=(
                    'Usually provided automatically when specifing a Japanese '
                    'to Kanji Translation.'
                ),
            ),
            Extra(
                name='Kanji Vertical Shift',
                identifier='kanji_vertical_shift',
                description=(
                    'Additional vertical offset to apply only to kanji text'
                ),
                tooltip=(
                    'Positive values shift the Kanji up, negative values shift '
                    'Kanji down. Default is <v>0</v>. Unit is pixels.'
                ),
                default=0,
            ),
            Extra(
                name='Kanji Color',
                identifier='kanji_color',
                description='Color of the kanji text',
                tooltip='Default is <c>white</c>.',
                default='white',
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
                name='Logo Position',
                identifier='logo_position',
                description='Where to position a logo',
                tooltip=(
                    'Either <v>top left</v>, <v>top right</v>, <v>bottom right'
                    '</v> to position the logo; or <v>omit</v> to not add the '
                    'logo. Default is <v>omit</v>.'
                ),
                default='omit',
                allowed_values=['top left', 'top right', 'bottom right', 'omit']
            ),
            Extra(
                name='Logo Size',
                identifier='logo_size',
                description='Scalar for how much to scale the size of the logo',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
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
                name='Require Kanji Text',
                identifier='require_kanji',
                description='Whether to require kanji text for card creation',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, cards '
                    'without Kanji will not be created. Default is <v>False</v>.'
                ),
                allowed_values=['True', 'False'],
                default='False',
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
                tooltip='Default is <v>·</v>.',
                default='·',
            ),
            Extra(
                name='Stroke Text Color',
                identifier='stroke_color',
                description='Color of the text stroke',
                tooltip='Default is <c>black</c>.',
                default='black',
            ),
            Extra(
                name='Kanji Font Size',
                identifier='kanji_font_size',
                description='Font size of the kanji text',
                tooltip='Number ≥<v>0.0</v>. Defaults to <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Kanji Stroke Color',
                identifier='kanji_stroke_color',
                description='Color of the stroke used on the Kanji text',
                tooltip='Defaults to match the title stroke color.',
            ),
            Extra(
                name='Kanji Stroke Width',
                identifier='kanji_stroke_width',
                description='Stroke width used on the Kanji text',
                tooltip='Number greater than <v>0</v>. Defaults to <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Season Text Color',
                identifier='season_text_color',
                description='Color of the season text and separator charactor',
                tooltip='Default is to match the Episode Text Color.',
            ),
        ],
        description=[
            'Title card with all text aligned in the lower left of the image.',
            'Although it is referred to as the "anime" card style, the only '
            'Anime specific feature is the ability to add Kanji (Japanese) '
            'text above the title text.',
        ]
    )

    REF_DIRECTORY: Annotated[
        Path,
        'Directory where all reference files used by this card are stored'
    ] = BaseCardType.BASE_REF_DIRECTORY / 'anime'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file = REF_DIRECTORY / 'Flanker Griffo.otf',
        font_color='white',
        font_case='source',
        font_replacements={'♡': '', '☆': '', '＊': '', '✕': 'x', '♥': ''},
        title_max_line_width=25,
        title_max_line_count=6,
        title_split_style='bottom',
    )

    EPISODE_TEXT_COLOR: ClassVar[str] = '#CFCFCF'
    EPISODE_STROKE_COLOR: ClassVar[str] = 'black'

    """Source path for the gradient image overlayed over all title cards"""
    __GRADIENT_IMAGE = REF_DIRECTORY / 'gradient.png'

    """Path to the font to use for the kanji font"""
    KANJI_FONT = REF_DIRECTORY / 'hiragino-mincho-w3.ttc'

    """Font characteristics for the series count text"""
    SERIES_COUNT_FONT = REF_DIRECTORY / 'Avenir.ttc'

    __slots__ = (
        'episode_stroke_color',
        'episode_text',
        'episode_text_color',
        'episode_text_size',
        'font_color',
        'font_file',
        'font_kerning',
        'font_size',
        'font_stroke_width',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_vertical_shift',
        'hide_season_text',
        'hide_episode_text',
        'kanji',
        'kanji_color',
        'kanji_font_size',
        'kanji_stroke_color',
        'kanji_stroke_width',
        'kanji_vertical_shift',
        'logo_file',
        'logo_position',
        'logo_size',
        'omit_gradient',
        'output_file',
        'season_text',
        'season_text_color',
        'separator',
        'source_file',
        'stroke_color',
        'title_text',
        'use_kanji',
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
            kanji: str | None = None,
            episode_text_font_size: float = 1.0,
            episode_stroke_color: str = EPISODE_STROKE_COLOR,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            separator: str = '·',
            logo_file: Path | None = None,
            logo_position: LogoPosition = 'omit',
            logo_size: float = 1.0,
            omit_gradient: bool = False,
            kanji_color: str = CardConfig.font_color,
            kanji_font_size: float = 1.0,
            kanji_stroke_color: str = 'black',
            kanji_stroke_width: float = 1.0,
            kanji_vertical_shift: float = 0.0,
            season_text_color: str | None = None,
            stroke_color: str = 'black',
            **unused: Any
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store source and output file
        self.source_file = source_file
        self.output_file = card_file

        # Escape title, season, and episode text
        self.title_text = self.image_magick.escape_chars(title_text)
        self.season_text = self.image_magick.escape_chars(season_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_season_text = hide_season_text
        self.hide_episode_text = hide_episode_text

        # Store kanji, set bool for whether to use it or not
        self.kanji = self.image_magick.escape_chars(kanji)
        self.use_kanji = kanji is not None
        self.kanji_vertical_shift = kanji_vertical_shift

        # Font customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = -30 + font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = 2.0 * font_kerning
        self.font_size = font_size
        self.font_stroke_width = font_stroke_width
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_text_size = episode_text_font_size
        self.episode_stroke_color = episode_stroke_color
        self.episode_text_color = episode_text_color
        self.logo_file = logo_file
        self.logo_position: LogoPosition = logo_position
        self.logo_size = logo_size
        self.omit_gradient = omit_gradient
        self.kanji_color = kanji_color
        self.kanji_font_size = kanji_font_size
        self.kanji_stroke_color = kanji_stroke_color
        self.kanji_stroke_width = kanji_stroke_width
        self.separator = separator
        self.season_text_color = season_text_color or episode_text_color
        self.stroke_color = stroke_color


    @property
    def __title_text_global_effects(self) -> ImageMagickCommands:
        """
        ImageMagick commands to implement the title text's global
        effects. Specifically the the font, kerning, fontsize, and
        southwest gravity.
        """

        font_size = 150 * self.font_size

        return [
            f'-font "{self.font_file}"',
            f'-kerning {self.font_kerning}',
            f'-interline-spacing {self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-pointsize {font_size}',
            f'-gravity southwest',
        ]


    @property
    def __title_text_black_stroke(self) -> ImageMagickCommands:
        """
        ImageMagick commands to implement the title text's black stroke.
        """

        # No stroke, return empty command
        if self.font_stroke_width == 0:
            return []

        stroke_width = 5 * self.font_stroke_width

        return [
            f'-fill "{self.stroke_color}"',
            f'-stroke "{self.stroke_color}"',
            f'-strokewidth {stroke_width}',
        ]


    @property
    def __title_text_effects(self) -> ImageMagickCommands:
        """Subcommands to implement the title text's standard effects."""

        return [
            f'-fill "{self.font_color}"',
            f'-stroke "{self.font_color}"',
            f'-strokewidth 0.5',
        ]


    @property
    def __series_count_text_global_effects(self) -> ImageMagickCommands:
        """
        Subcommands for global text effects applied to all series count
        text (season/episode count and dot).
        """

        size = 67 * self.episode_text_size

        return [
            f'-font "{self.SERIES_COUNT_FONT.resolve()}"',
            f'-kerning 2',
            f'-pointsize {size}',
            f'-interword-spacing 25',
            f'-gravity southwest',
        ]


    @property
    def title_text_command(self) -> ImageMagickCommands:
        """
        Subcommands for adding title and kanji text to the source image.
        """

        # Base offset for the title text
        base_offset = 175 + self.font_vertical_shift

        title_commands = [
            *self.__title_text_global_effects,
            *self.__title_text_black_stroke,
            f'-annotate +75+{base_offset} "{self.title_text}"',
            *self.__title_text_effects,
            f'-annotate +75+{base_offset} "{self.title_text}"',
        ]

        if not self.use_kanji:
            return title_commands

        # Determine kanji positioning based on height of title text
        _, title_height = self.image_magick.get_text_dimensions(
            [
                *self.__title_text_global_effects,
                *self.__title_text_effects,
                f'-annotate +75+{base_offset} "{self.title_text}"',
            ],
            interline_spacing=self.font_interline_spacing,
            line_count=len(self.title_text.splitlines()),
            width='max',
        )
        kanji_offset = base_offset + title_height + self.kanji_vertical_shift

        return [
            *title_commands,
            f'-font "{self.KANJI_FONT.resolve()}"',
            f'-kerning 2',
            f'-pointsize {85 * self.kanji_font_size}',
            f'-strokewidth {5 * self.kanji_stroke_width:.2f}',
            f'-fill "{self.kanji_stroke_color}"',
            f'-stroke "{self.kanji_stroke_color}"',
            f'-annotate +75+{kanji_offset} "{self.kanji}"',
            f'-fill "{self.kanji_color}"',
            f'-stroke "{self.kanji_stroke_color}"',
            f'-strokewidth 0.5',
            f'-annotate +75+{kanji_offset} "{self.kanji}"',
        ]


    @property
    def index_text_command(self) -> ImageMagickCommands:
        """Subcommand for adding the index text to the source image."""

        # Hiding all index text, return blank commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Add only season OR episode text
        if self.hide_season_text or self.hide_episode_text:
            if self.hide_season_text:
                color = self.episode_text_color
                text = self.episode_text
            else:
                color = self.season_text_color
                text = self.season_text

            return [
                *self.__series_count_text_global_effects,
                f'-fill "{self.episode_stroke_color}"',
                f'-stroke "{self.episode_stroke_color}"',
                f'-strokewidth 6',
                f'-annotate +75+90 "{text}"',
                f'-fill "{color}"',
                f'-stroke "{color}"',
                f'-strokewidth 0',
                f'-annotate +75+90 "{text}"',
            ]

        # Add season and episode text
        return [
            f'-background transparent',
            *self.__series_count_text_global_effects,
            f'-fill "{self.episode_stroke_color}"',
            f'-stroke "{self.episode_stroke_color}"',
            f'-strokewidth 6',
            # Stroke behind season and episode text
            *ImageStack(
                f'-gravity center',
                # Stroke uses same font for season/episode text
                f'label:"{self.season_text} {self.separator}"',
                f'label:"{self.episode_text}"',
                # Combine season and episode text into one "image"
                f'+smush 30',
            ),
            f'-gravity southwest',
            # Overlay stroke "image" - use different offset for stroke
            f'-geometry +73+88',
            f'-composite',
            # Primary season and episode text
            *self.__series_count_text_global_effects,
            f'-fill "{self.season_text_color}"',
            f'-stroke "{self.season_text_color}"',
            *ImageStack(
                f'-gravity center',
                # Season text and separator uses larger stroke
                f'-strokewidth 2',
                f'label:"{self.season_text} {self.separator}"',
                # Zero-width stroke for episode text
                f'-strokewidth 0',
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'label:"{self.episode_text}"',
                # Combine season+episode text images
                f'+smush 35',
            ),
            # Add text to source image
            f'-gravity southwest',
            f'-geometry +75+90',
            f'-composite',
        ]


    @property
    def logo_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the logo file to the image (if indicated).
        """

        # Logo not provided, does not exist, or unplaced
        if (self.logo_position == 'omit'
            or not self.logo_file or not self.logo_file.exists()):
            return []

        # Determine logo gravity by position
        if self.logo_position == 'bottom right':
            gravity = 'southeast'
        elif self.logo_position == 'top left':
            gravity = 'northwest'
        else:
            gravity = 'northeast'

        return self.add_drop_shadow(
            [
                *ImageStack(
                    f'"{self.logo_file.resolve()}"',
                    f'-resize x{100 * self.logo_size}',
                ),
                f'-gravity {gravity}',
            ],
            shadow=Shadow(opacity=85, sigma=4),
            x=75, y=75,
        )


    def create(self) -> None:
        """Create this object's defined Title Card."""

        # Sub-command to optionally add gradient
        gradient_command = []
        if not self.omit_gradient:
            gradient_command = [
                f'"{self.__GRADIENT_IMAGE.resolve()}"',
                f'-composite',
            ]

        contrast = [f'-modulate 100,125']
        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            # Resize and optionally blur source image
            *self.resize_and_style,
            # Increase contrast of source image
            *contrast,
            # Overlay gradient
            *gradient_command,
            *self.logo_commands,
            # Add title and/or kanji
            *self.title_text_command,
            # Add index text
            *self.index_text_command,
            # Attempt to overlay mask
            *self.add_overlay_mask(
                self.source_file,
                pre_processing=self.resize_and_style + contrast,
            ),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[BaseCardModel]:
    """Get the Pydantic validator class for this card type."""

    class CardModel(BaseCardTypeCustomFontAllText):
        font_color: str = AnimeTitleCard.CardConfig.font_color
        font_file: FilePath = AnimeTitleCard.CardConfig.font_file
        kanji: str | None = None
        require_kanji: bool = False
        kanji_color: str | None = AnimeTitleCard.CardConfig.font_color
        kanji_font_size: FontSize = 1.0
        kanji_stroke_color: str | None = None
        kanji_stroke_width: Annotated[float, Field(ge=0)] = 1.0
        kanji_vertical_shift: int = 0
        separator: str = '·'
        logo_file: Path | None = None
        logo_position: LogoPosition = 'omit'
        logo_size: FontSize = 1.0
        omit_gradient: bool = False
        episode_stroke_color: str = AnimeTitleCard.EPISODE_STROKE_COLOR
        episode_text_color: str = AnimeTitleCard.EPISODE_TEXT_COLOR
        episode_text_font_size: FontSize = 1.0
        season_text_color: str | None = None
        stroke_color: str = 'black'

        @model_validator(mode='after')
        def validate_kanji(self) -> Self:
            """Validate that kanji has been provided if it is required"""
            if self.require_kanji and not self.kanji:
                raise get_extra_validation_error(
                    title='Kanji is required but not specified',
                    error_name='missing_kanji',
                    error_template='Kanji is required but not specified',
                    error_context={},
                    error_location='kanji',
                    input=self.kanji,
                )
            return self

        @model_validator(mode='after')
        def assign_unassigned_values(self) -> Self:
            """Assign any unassigned colors to their default values."""
            if self.kanji_stroke_color is None:
                self.kanji_stroke_color = self.stroke_color
            return self

        @model_validator(mode='after')
        def require_logo(self) -> Self:
            """Require a logo file if it is specified."""

            # Set the logo file to None so that existing Cards are not
            # remade by assigning an unused logo file
            if self.logo_position == 'omit':
                self.logo_file = None
            # Logo file specified, verify the file exists
            elif (self.logo_position != 'omit'
                and (self.logo_file is None or not self.logo_file.exists())
            ):
                raise get_extra_validation_error(
                    title='Logo required but not provided',
                    error_name='missing_logo',
                    error_template='Logo required but not provided',
                    error_context={},
                    error_location='logo_file',
                    input=self.logo_file,
                )

            return self

    return CardModel


add_card_cli(
    __name__,
    AnimeTitleCard,
    get_validator_model(),
    documentation=CardDocumentation(
        static_variables={
            'title_text': 'Never Give Up',
            'season_text': 'ENTERTAINMENT DISTRICT',
            'episode_text': 'EPISODE 10',
            'kanji': '絶対諦めない',
        },
        cards=[
            PreviewCard(
                filename='episode_text_color',
                variables={'episode_text_color': 'rgb(233,20,35)'},
            ),
            PreviewCard(
                filename='episode_text_font_size',
                variables={'episode_text_font_size': 1.3},
            ),
            PreviewCard(
                filename='episode_stroke_color',
                variables={'episode_stroke_color': 'crimson'},
            ),
            PreviewCard(
                filename='omit_gradient',
                variables={'omit_gradient': True},
            ),
            PreviewCard(
                filename='logo_position',
                variables={'logo_position': 'top left'},
            ),
            PreviewCard(
                filename='logo_size',
                variables={'logo_position': 'top left', 'logo_size': 3.0},
            ),
            PreviewCard(
                filename='kanji_color',
                variables={'kanji_color': 'skyblue'},
            ),
            PreviewCard(
                filename='kanji_size',
                variables={'kanji_size': 1.5},
            ),
            PreviewCard(
                filename='kanji_stroke_color',
                variables={'kanji_stroke_color': 'crimson'},
            ),
            PreviewCard(
                filename='kanji_stroke_width',
                variables={'kanji_stroke_width': 1.4},
            ),
            PreviewCard(
                filename='kanji_vertical_shift',
                variables={'kanji_vertical_shift': 20},
            ),
            PreviewCard(
                filename='season_text_color',
                variables={'season_text_color': '#CFCFCF'},
            ),
            PreviewCard(
                filename='separator',
                variables={'separator': '//'},
            ),
            PreviewCard(
                filename='stroke_color',
                variables={'stroke_color': 'red'},
            ),
        ]
    )
)
