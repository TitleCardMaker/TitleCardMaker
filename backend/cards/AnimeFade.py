from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal, Self

from pydantic import FilePath, PositiveFloat, model_validator

from app.logging.logger import log # noqa: F401
from app.schemas.base import Base, BaseCardTypeCustomFontAllText
from modules.BaseCardType import (
    BaseCardType,
    CardTypeDescription,
    Extra,
    ImageMagickCommands,
)

if TYPE_CHECKING:
    from app.yaml.font import Font

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
            
        ],
        description=[
            
        ]
    )

    """Directory where all reference files used by this card are stored"""
    ANIME_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'anime'
    FADE_REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'fade'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 12,
        'max_line_count': 6,
        'style': 'bottom',
    }

    ARCHIVE_NAME: Annotated[
        str,
        'How to name archive directories for this type of card'
    ] = 'Anime Fade Style'

    """Characteristics of the default title font"""
    TITLE_FONT = str((ANIME_REF_DIRECTORY / 'Flanker Griffo.otf').resolve())
    DEFAULT_FONT_CASE = 'source'
    TITLE_COLOR = 'white'
    FONT_REPLACEMENTS = {'♡': '', '☆': '', '＊': '', '✕': 'x', '♥': ''}

    USES_SEASON_TITLE: Annotated[
        bool,
        'Whether this card type uses season titles for the purpose of archives'
    ] = True

    OVERLAY_IMAGE: Annotated[
        Path,
        'Source path for the gradient image overlayed over all title cards'
    ] = FADE_REF_DIRECTORY / 'gradient_fade.png'

    KANJI_FONT: Annotated[
        Path,
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
        'kanji_vertical_shift',
        'logo_file',
        'logo_size',
        'omit_gradient',
        'output_file',
        'require_kanji',
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
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
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
            omit_gradient: bool = False,
            require_kanji: bool = False,
            kanji_color: str = TITLE_COLOR,
            kanji_font_size: float = 1.0,
            kanji_vertical_shift: float = 0.0,
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
        self.require_kanji = require_kanji
        self.kanji_vertical_shift = kanji_vertical_shift

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
        self.omit_gradient = omit_gradient
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
            f'-pointsize {67 * self.episode_text_size}',
            f'-interword-spacing 25',
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
                    f'-pointsize {85 * self.kanji_font_size}',
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
                    f'-pointsize {150 * self.font_size}',
                    f'-gravity southwest',
                    f'label:"{self.title_text}"',
                f'\)',
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


    @staticmethod
    def modify_extras(
            extras: dict,
            custom_font: bool,
            custom_season_titles: bool,
        ) -> None:
        """
        Modify the given extras base on whether font or season titles
        are custom.

        Args:
            extras: Dictionary to modify.
            custom_font: Whether the font are custom.
            custom_season_titles: Whether the season titles are custom.
        """

        if not custom_font:
            for extra in (
                'episode_text_color',
                'episode_text_size',
                'kanji_font_size',
                'kanji_vertical_shift',
                'logo_size',
            ):
                if extra in extras:
                    del extras[extra]


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determines whether the given arguments represent a custom font
        for this card.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = AnimeFadeTitleCard._is_custom_extras(
            extras,
            {
                'episode_text_color': AnimeFadeTitleCard.EPISODE_TEXT_COLOR,
                'episode_text_size': 1.0,
                'kanji_color': AnimeFadeTitleCard.TITLE_COLOR,
                'kanji_font_size': 1.0,
                'kanji_vertical_shift': 0,
            }
        )

        return custom_extras or AnimeFadeTitleCard._is_custom_font(font)


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Determines whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        return (
            custom_episode_map
            or episode_text_format != AnimeFadeTitleCard.EPISODE_TEXT_FORMAT
        )


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
        font_color: str = AnimeFadeTitleCard.TITLE_COLOR
        font_file: FilePath = AnimeFadeTitleCard.TITLE_FONT # type: ignore
        kanji: str | None = None
        require_kanji: bool = False
        kanji_color: str | None = AnimeFadeTitleCard.TITLE_COLOR
        kanji_font_size: PositiveFloat = 1.0
        kanji_vertical_shift: int = 0
        separator: str = '·'
        logo_file: Path | None = None
        logo_size: PositiveFloat = 1.0
        omit_gradient: bool = False
        episode_text_color: str = AnimeFadeTitleCard.EPISODE_TEXT_COLOR
        episode_text_font_size: PositiveFloat = 1.0
        logo_size: PositiveFloat = 1.0
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
