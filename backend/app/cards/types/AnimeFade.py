from pathlib import Path
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import Field, FilePath, model_validator

from app.cards.base import (
    BaseCardType,
    CardTypeDescription,
    DefaultCardConfig,
    Extra,
    ImageMagickCommands,
)
from app.schemas.base import Base, BaseCardTypeCustomFontAllText


TextPosition = Literal['bottom', 'center']


class AnimeFadeTitleCard(BaseCardType):
    """
    This class describes a type of card type which is a funcional mix of
    the Anime and Fade styles.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Anime Fade',
        identifier='anime fade',
        example='/public/cards/anime_fade.webp',
        creators=[
            '/u/Recker_Man',
            'CollinHeist',
            'Reicha7',
            'Yozora',
            'drewstopherlee',
        ],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>rgb(163,163,163)</c>.',
                default='rgb(163,163,163)',
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the season and episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Season Text Color',
                identifier='season_text_color',
                description='Color of the season text and separator charactor',
                tooltip='Default is to match the Episode Text Color.',
            ),
            Extra(
                name='Text Position',
                identifier='text_position',
                description='Where on the image to position the text',
                tooltip=(
                    'Either <v>bottom</v> or <v>center</v>. Default is '
                    '<v>bottom</v>.'
                ),
                default='bottom',
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description='Character to separate season and episode text',
                tooltip='Default is <v>·</v>.',
                default='·',
            ),
            Extra(
                name='Logo Size',
                identifier='logo_size',
                description='Scalar for how much to scale the size of the logo',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Kanji Color',
                identifier='kanji_color',
                description='Color of the kanji text',
                tooltip='Default is <c>white</c>.',
                default='white',
            ),
            Extra(
                name='Kanji Font Size',
                identifier='kanji_font_size',
                description='Font size of the kanji text',
                tooltip='Number ≥<v>0.0</v>. Defaults to <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Require Kanji Text',
                identifier='require_kanji',
                description='Whether to require kanji text for card creation',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, cards '
                    'without Kanji will not be created. Default is <v>False</v>.'
                ),
                default='False',
            ),
        ],
        description=[
            'A functional mix of the Anime and Fade card types.', 'This card '
            'is intended for use with older 4:3 aspect-ratio images/shows.',
            'Like with the Anime card type, Japanese text (kanji) can be added '
            'above the title text.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    ANIME_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'anime'
    FADE_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'fade'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=ANIME_REF_DIRECTORY / 'Flanker Griffo.otf',
        font_color='white',
        font_case='source',
        font_replacements={'♡': '', '☆': '', '＊': '', '✕': 'x', '♥': ''},
        title_max_line_width=16,
        title_max_line_count=6,
        title_split_style='bottom',
    )

    OVERLAY_IMAGE: Annotated[
        ClassVar[Path],
        'Source path for the gradient image overlayed over all title cards'
    ] = FADE_REF_DIRECTORY / 'gradient_fade.png'

    KANJI_FONT: Annotated[
        ClassVar[Path],
        'Path to the font to use for kanji text'
    ] = ANIME_REF_DIRECTORY / 'hiragino-mincho-w3.ttc'

    """Font characteristics for the series count text"""
    SERIES_COUNT_FONT = ANIME_REF_DIRECTORY / 'Avenir.ttc'
    EPISODE_TEXT_COLOR = 'rgb(163,163,163)'

    __slots__ = (
        'episode_text',
        'episode_text_color',
        'episode_text_size',
        'font_color',
        'font_file',
        'font_kerning',
        'font_size',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_vertical_shift',
        'hide_season_text',
        'hide_episode_text',
        'kanji',
        'kanji_color',
        'kanji_font_size',
        'logo_file',
        'logo_size',
        'output_file',
        'season_text',
        'season_text_color',
        'separator',
        'source_file',
        'text_position',
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
            font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            kanji: str | None = None,
            episode_text_font_size: float = 1.0,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            separator: str = '·',
            logo_file: Path | None = None,
            logo_size: float = 1.0,
            kanji_color: str = CardConfig.font_color,
            kanji_font_size: float = 1.0,
            season_text_color: str | None = None,
            text_position: TextPosition = 'bottom',
            **unused: Any,
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
        self.hide_season_text = hide_season_text or not season_text
        self.hide_episode_text = hide_episode_text or not episode_text

        # Store kanji, set bool for whether to use it or not
        self.kanji = self.image_magick.escape_chars(kanji)
        self.use_kanji = kanji is not None

        # Font customizations
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = -30 + font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = 2.0 * font_kerning
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift

        # Optional extras
        self.episode_text_size = episode_text_font_size
        self.episode_text_color = episode_text_color
        self.logo_file = logo_file
        self.logo_size = logo_size
        self.kanji_color = kanji_color
        self.kanji_font_size = kanji_font_size
        self.separator = separator
        self.season_text_color = season_text_color or episode_text_color
        self.text_position: TextPosition = text_position


    @property
    def index_text_command(self) -> ImageMagickCommands:
        """Subcommand for adding the index text to the source image."""

        if self.hide_season_text and self.hide_episode_text:
            return []

        base_commands = [
            f'-kerning 2',
            f'-pointsize {60 * self.episode_text_size}',
            f'-interword-spacing 22',
            f'-font "{self.SERIES_COUNT_FONT.resolve()}"',
        ]

        if self.hide_episode_text:
            return [
                fr'\(',
                    *base_commands,
                    f'-fill "{self.season_text_color}"',
                    f'-stroke "{self.season_text_color}"',
                    f'-strokewidth 2',
                    f'label:"{self.season_text}"',
                fr'\)',
            ]

        if self.hide_season_text:
            return [
                fr'\(',
                    *base_commands,
                    f'-fill "{self.episode_text_color}"',
                    f'-stroke "{self.episode_text_color}"',
                    f'-strokewidth 0',
                    f'label:"{self.episode_text}"',
                fr'\)',
            ]

        return [
            fr'\(',
                *base_commands,
                f'-fill "{self.season_text_color}"',
                f'-stroke "{self.season_text_color}"',
                f'-strokewidth 2',
                f'label:"{self.season_text} {self.separator}"',
                f'-strokewidth 0',
                f'-fill "{self.episode_text_color}"',
                f'-stroke "{self.episode_text_color}"',
                f'label:"{self.episode_text}"',
                fr'+smush 30',
            fr'\)',
        ]


    @property
    def text_stack_commands(self) -> ImageMagickCommands:
        """
        Subcommands for adding title and kanji text to the source image.
        """

        gravity = 'southwest' if self.text_position == 'bottom' else 'west'

        # Subcommands for kanji text
        kanji_commands = []
        if self.use_kanji:
            kanji_commands = [
                fr'\(',
                    f'-font "{self.KANJI_FONT.resolve()}"',
                    f'-kerning 2',
                    f'-pointsize {68 * self.kanji_font_size}',
                    f'-fill "{self.kanji_color}"',
                    f'label:"{self.kanji}"',
                fr'\)',
            ]

        return [
            # Create image stack from top to bottom
            fr'\(',
                f'-gravity southwest',
                # Ensure all label images are transparent and dynamically sized
                f'-background transparent',
                f'+size',
                # Kanji Text
                *kanji_commands,
                # Title Text
                fr'\(',
                    f'-fill "{self.font_color}"',
                    f'-font "{self.font_file}"',
                    f'-kerning {self.font_kerning}',
                    f'-interline-spacing {self.font_interline_spacing}',
                    f'-interword-spacing {self.font_interword_spacing}',
                    f'-pointsize {112 * self.font_size}',
                    f'-gravity southwest',
                    f'label:"{self.title_text}"',
                fr'\)',
                # Index Text
                *self.index_text_command,
                # Vertically stack kanji / title / index
                f'-smush 45',
            fr'\)',
            f'-gravity {gravity}',
            f'-geometry +75+175',
            f'-composite',
        ]


    @property
    def logo_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the logo file to the image (if indicated).
        """

        # Logo not provided, does not exist, or unplaced
        if (self.logo_size <= 0.0
            or not self.logo_file
            or not self.logo_file.exists()):
            return []

        logo_size = 500 * self.logo_size

        return [
            fr'\(',
                f'"{self.logo_file.resolve()}"',
                f'-resize 900x',
                fr'-resize x{logo_size}\>',
            fr'\)',
            f'-gravity west',
            f'-geometry +100-550',
            f'-composite',
        ]


    def create(self) -> None:
        """Create this object's defined Title Card."""

        contrast = [f'-modulate 100,125']
        self.image_magick.run([
            f'convert',
            # Create blank transparent image for composite sequencing
            f'-size "{self.TITLE_CARD_SIZE}"',
            f'xc:None',
            # Resize source to subsection of card
            fr'\(',
                f'"{self.source_file.resolve()}"',
                f'-resize x1525',
                *self.style,
            fr'\)',
            # Compose source onto proper place on canvas (100px from right)
            f'-gravity east',
            f'-geometry +100+0',
            f'-composite',
            # Overlay gradient frame
            f'"{self.OVERLAY_IMAGE.resolve()}"',
            f'-composite',
            *self.logo_commands,
            *self.text_stack_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(
                self.source_file,
                pre_processing=self.resize_and_style + contrast,
            ),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[Base]:
    """Get the Pydantic validator class for this card type."""

    # pyright: reportInvalidTypeForm=false
    class CardModel(BaseCardTypeCustomFontAllText):
        font_color: str = AnimeFadeTitleCard.CardConfig.font_color
        font_file: FilePath = AnimeFadeTitleCard.CardConfig.font_file
        kanji: str | None = None
        require_kanji: bool = False
        kanji_color: str | None = AnimeFadeTitleCard.CardConfig.font_color
        kanji_font_size: Annotated[float, Field(ge=0.0)] = 1.0
        separator: str = '·'
        logo_file: Path | None = None
        logo_size: Annotated[float, Field(ge=0.0)] = 1.0
        episode_text_color: str = AnimeFadeTitleCard.EPISODE_TEXT_COLOR
        episode_text_font_size: Annotated[float, Field(ge=0.0)] = 1.0
        logo_size: Annotated[float, Field(ge=0.0)] = 1.0
        season_text_color: str | None = None
        text_position: TextPosition = 'bottom'

        @model_validator(mode='after')
        def validate_kanji(self) -> Self:
            """Validate that kanji has been provided if it is required"""
            if self.require_kanji and not self.kanji:
                raise ValueError('Kanji is required, but not specified')
            return self

        @model_validator(mode='after')
        def require_logo(self) -> Self:
            """Require a logo file if it is specified."""

            # Set the logo file to None so that existing Cards are not
            # remade by assigning an unused logo file
            if self.logo_size <= 0.0:
                self.logo_file = None
            # Logo file specified, verify the file exists
            elif self.logo_file is None or not self.logo_file.exists():
                raise ValueError('Logo file not provided')

            return self

    return CardModel
