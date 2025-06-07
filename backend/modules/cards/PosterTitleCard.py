from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

from pydantic import FilePath, PositiveFloat, constr, model_validator

from app.schemas.base import Base, BaseCardModel
from modules.BaseCardType import BaseCardType, Extra, CardTypeDescription

if TYPE_CHECKING:
    from modules.preferences import Preferences
    from modules.Font import Font


class PosterTitleCard(BaseCardType):
    """
    This class describes a type of CardType that produces title cards in
    the style of the Gundam series of cards produced by Reddit user
    /u/battleoflight.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Poster',
        identifier='poster',
        example='/public/cards/poster.jpg',
        creators=['/u/battleoflight', 'CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=False,
        supported_extras=[
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is to match the Font color.',
            ),
        ],
        description=[
            'Title card featuring a vertical poster with a starry background, '
            'originally designed for the Gundam series.', 'This card is '
            'designed for vertical Source Images, and you will likely need to '
            'manually download and specify a poster as a Source Image.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'poster_card'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 16,
        'max_line_count': 5,
        'style': 'top',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Amuro.otf').resolve())
    TITLE_COLOR = '#FFFFFF'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'Ep. {episode_number}'
    EPISODE_TEXT_COLOR = '#FFFFFF'
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Amuro.otf'

    """Whether this class uses season titles for the purpose of archives"""
    USES_SEASON_TITLE = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME = 'Poster Style'

    """Custom blur profile for the poster"""
    BLUR_PROFILE = '0x30'

    """Path to the reference star image to overlay on all source images"""
    __GRADIENT_OVERLAY = REF_DIRECTORY / 'stars-overlay.png'

    __slots__ = (
        'episode_text',
        'episode_text_color',
        'font_color',
        'font_file',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_size',
        'logo',
        'output_file',
        'source_file',
        'title_text',
    )


    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            episode_text: str,
            font_color: str = TITLE_COLOR,
            font_file: str = TITLE_FONT,
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_size: float = 1.0,
            blur: bool = False,
            grayscale: bool = False,
            logo_file: Path | None = None,
            episode_text_color: str = EPISODE_TEXT_COLOR,
            preferences: 'Preferences | None' = None,
            **unused: Any,
        ) -> None:
        """Construct a new instance of this card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

        # Store indicated files
        self.source_file = source_file
        self.output_file = card_file
        self.logo = logo_file

        # Store text
        self.title_text = self.image_magick.escape_chars(title_text)
        self.episode_text = self.image_magick.escape_chars(episode_text)

        # Font characteristics
        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_size = font_size

        # Extras
        self.episode_text_color = episode_text_color


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

        # Generic font, reset custom episode text color
        if not custom_font:
            for extra in ('episode_text_color', ):
                if extra in extras:
                    del extras[extra]


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determines whether the given arguments represent a custom font
        for this card. This CardType does not use custom fonts, so this
        is always False.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        returns:
            False, as fonts are not customizable with this card.
        """

        custom_extras = (
            ('episode_text_color' in extras
                and extras['episode_text_color'] != \
                    PosterTitleCard.EPISODE_TEXT_COLOR)
        )

        return (
            custom_extras
            or font.color != PosterTitleCard.TITLE_COLOR
            or font.file != PosterTitleCard.TITLE_FONT
            or font.interline_spacing != 0
            or font.interword_spacing != 0
            or font.size != 1.0
        )


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Determines whether the given attributes constitute custom or
        generic season titles.

        Args:
            episode_text_format: The episode text format in use.
            args and kwargs: Generic arguments to permit  generalized
                function calls for any CardType.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        return episode_text_format != PosterTitleCard.EPISODE_TEXT_FORMAT


    def create(self) -> None:
        """Create the title card as defined by this object."""

        # If no logo is specified, create empty logo command
        if self.logo is None or not self.logo.exists():
            title_offset = 0
            logo_command = ''
        # Logo specified and exists, create command to resize and add image
        else:
            logo_command = [
                f'-gravity north',
                fr'\( "{self.logo.resolve()}"',
                f'-resize x450',
                fr'-resize 1775x450\> \)',
                f'-geometry +649+50',
                f'-composite',
            ]

            # Adjust title offset to center in smaller space (due to logo)
            title_offset = (450 / 2) - (50 / 2)

        # Single command to create card
        self.image_magick.run([
            f'convert',
            # Resize poster
            f'"{self.source_file.resolve()}"',
            f'-resize "x1800"',
            # Extend image canvas to full size
            f'-extent "{self.TITLE_CARD_SIZE}"',
            # Apply style modifiers
            *self.style,
            # Add gradient overlay
            f'"{self.__GRADIENT_OVERLAY.resolve()}"',
            f'-flatten',
            # Optionally add logo
            *logo_command,
            # Add episode text
            f'-gravity south',
            f'-font "{self.font_file}"',
            f'-pointsize {75 * self.font_size}',
            f'-fill "{self.episode_text_color}"',
            f'-annotate +649+50 "{self.episode_text}"',
            # Add title text
            f'-gravity center',
            f'-pointsize {165 * self.font_size}',
            f'-interline-spacing {-40 + self.font_interline_spacing}',
            f'-interword-spacing {self.font_interword_spacing}',
            f'-fill "{self.font_color}"',
            f'-annotate +649+{title_offset} "{self.title_text}"',
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[Base]:
    """Get the Pydantic validator class for this card type."""
    
    # pyright: reportInvalidTypeForm=false
    class CardModel(BaseCardModel):
        title_text: str
        episode_text: constr(to_upper=True)
        hide_episode_text: bool = False
        font_color: str = PosterTitleCard.TITLE_COLOR
        font_file: FilePath = PosterTitleCard.TITLE_FONT # type: ignore
        font_interline_spacing: int = 0
        font_interword_spacing: int = 0
        font_size: PositiveFloat = 1.0
        logo_file: Path | None = None
        episode_text_color: str | None = None

        @model_validator(mode='after')
        def toggle_text_hiding(self) -> Self:
            """Set the hide episode text flag if the episode text is blank"""

            self.hide_episode_text |= (len(self.episode_text) == 0)

            return self

        @model_validator(mode='after')
        def assign_episode_text_color(self) -> Self:
            """Assign any unassigned colors to their default values."""

            if self.episode_text_color is None:
                self.episode_text_color = self.font_color

            return self

    return CardModel
