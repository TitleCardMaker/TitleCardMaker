from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import (
    Field,
    FilePath,
    StringConstraints,
    model_validator,
)

from app.schemas.base import Base, BaseCardTypeAllText
from modules.BaseCardType import (
    BaseCardType,
    CardTypeDescription,
    Extra,
    ImageMagickCommands,
)


Country = Literal[
    'Abu Dhabi', 'Australian', 'Austrian', 'Azerbaijan', 'Bahrain', 'Belgian',
    'British', 'Canadian', 'Chinese', 'Dutch', 'Hungarian', 'Italian',
    'Japanese', 'Las Vegas', 'Mexican', 'Miami', 'Monaco', 'Qatar', 'Sao Paulo',
    'Saudi Arabian', 'Singapore', 'Spanish', 'United Arab Emirates',
    'United States', 'generic',
]


class FormulaOneTitleCard(BaseCardType):
    """
    This class describes a CardType that produces Title Cards which are
    styled for Formula 1.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Formula 1',
        identifier='formula 1',
        example='/public/cards/formula.webp',
        creators=['CollinHeist', '/u/heeisenbeerg'],
        source='builtin',
        supports_custom_fonts=False,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Country',
                identifier='country',
                description='Which flag to utilize on the Title Card',
                tooltip=(
                    'One of <v>Abu Dhabi</v>, <v>Australian</v>, '
                    '<v>Austrian</v>, <v>Azerbaijan</v>, <v>Bahrain</v>, '
                    '<v>Belgian</v>, <v>British</v>, <v>Canadian</v>, '
                    '<v>Chinese</v>, <v>Dutch</v>, <v>Hungarian</v>, '
                    '<v>Italian</v>, <v>Japanese</v>, <v>Las Vegas</v>, '
                    '<v>Mexican</v>, <v>Miami</v>, <v>Monaco</v>, <v>Qatar</v>,'
                    ' <v>Sao Paulo</v>, <v>Saudi Arabian</v>, <v>Singapore</v>,'
                    ' <v>Spanish</v>, <v>United Arab Emirates</v>, or '
                    '<v>United States</v>. By default this is parsed from the '
                    'season title.'
                ),
            ),
            Extra(
                name='Race Name',
                identifier='race',
                description='Name of the race',
                tooltip='Default is <v>Grand Prix</v>.',
                default='Grand Prix',
            ),
            Extra(
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color to utilize for the episode text',
                tooltip='Default is <c>white</c>.',
                default='white',
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>',
                default=1.0,
            ),
            Extra(
                name='Flag',
                identifier='flag',
                description='Flag file to use on the left frame of the card',
                tooltip=(
                    'Path to the flag frame file. If omitted, the flag is '
                    'determined by the specified country.'
                ),
            ),
            Extra(
                name='Frame Year',
                identifier='frame_year',
                description='Which frame year to utilize',
                tooltip=(
                    'Default is the year the Episode aired - or, if that is '
                    'not available, <v>2024</v>.'
                ),
            ),
        ],
        description=[
            'Title Card designed for displaying race details for Formula 1. ',
            'The intention is that a custom seeason title of the relevant '
            'country/flag (e.g. japanese) is set, and then the appropriate '
            'flag will automatically be selected.', 'This card type is not '
            'widely applicable for non-F1 Series.',
        ],
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'formula'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS = {
        'max_line_width': 40,
        'max_line_count': 1,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT = str((REF_DIRECTORY / 'Formula1-Bold.otf').resolve())
    TITLE_COLOR = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FONT = REF_DIRECTORY / 'Formula1-Bold.otf'
    EPISODE_TEXT_FORMAT = 'ROUND {season_number}'
    EPISODE_TEXT_COLOR = 'white'

    """Implementation details"""
    DARKEN_COLOR = 'rgba(0,0,0,0.5)'
    FRAME = REF_DIRECTORY / 'frame.png'
    FRAME_FONT = REF_DIRECTORY / 'Formula1-Numbers.otf'
    _COUNTRY_FLAGS = {
        'ABU DHABI': REF_DIRECTORY / 'uae.webp',
        'AUSTRALIAN': REF_DIRECTORY / 'australia.webp',
        'AUSTRIAN': REF_DIRECTORY / 'austria.webp',
        'AZERBAIJAN': REF_DIRECTORY / 'azerbaijan.webp',
        'BAHRAIN': REF_DIRECTORY / 'bahrain.webp',
        'BELGIAN': REF_DIRECTORY / 'belgium.webp',
        'BRITISH': REF_DIRECTORY / 'british.webp',
        'CANADIAN': REF_DIRECTORY / 'canada.webp',
        'CHINESE': REF_DIRECTORY / 'chinese.webp',
        'DUTCH': REF_DIRECTORY / 'dutch.webp',
        'HUNGARIAN': REF_DIRECTORY / 'hungarian.webp',
        'ITALIAN': REF_DIRECTORY / 'italian.webp',
        'JAPANESE': REF_DIRECTORY / 'japan.webp',
        'LAS VEGAS': REF_DIRECTORY / 'unitedstates.webp',
        'MEXICAN': REF_DIRECTORY / 'mexico.webp',
        'MONACO': REF_DIRECTORY / 'monaco.webp',
        'QATAR': REF_DIRECTORY / 'qatar.webp',
        'SAO PAULO': REF_DIRECTORY / 'brazil.webp',
        'SAUDI ARABIAN': REF_DIRECTORY / 'saudiarabia.webp',
        'SINGAPORE': REF_DIRECTORY / 'singapore.webp',
        'SPANISH': REF_DIRECTORY / 'spain.webp',
        'MIAMI': REF_DIRECTORY / 'unitedstates.webp',
        'UNITED ARAB EMIRATES': REF_DIRECTORY / 'uae.webp',
        'UNITED STATES': REF_DIRECTORY / 'unitedstates.webp',
        'GENERIC': REF_DIRECTORY / 'generic.webp',
    }


    __slots__ = (
        'country',
        'episode_text',
        'episode_text_color',
        'episode_text_font_size',
        'font_color',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_file',
        'font_kerning',
        'font_size',
        'font_vertical_shift',
        'hide_season_text',
        'hide_episode_text',
        'output_file',
        'race',
        'season_text',
        'source_file',
        'title_text',
        'year',
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
            # font_interline_spacing: int = 0,
            # font_interword_spacing: int = 0,
            # font_kerning: float = 1.0,
            font_size: float = 1.0,
            # font_vertical_shift: int = 0,
            blur: bool = False,
            grayscale: bool = False,
            country: Country = 'Australian',
            episode_text_color: str = TITLE_COLOR,
            episode_text_font_size: float = 1.0,
            flag: Path | None = None,
            frame_year: int = 2024,
            race: str = 'GRAND PRIX',
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
        self.hide_season_text = hide_season_text
        self.episode_text = self.image_magick.escape_chars(episode_text)
        self.hide_episode_text = hide_episode_text

        # Font/card customizations
        self.font_color = font_color
        self.font_file = font_file
        # self.font_interline_spacing = font_interline_spacing
        # self.font_interword_spacing = font_interword_spacing
        # self.font_kerning = font_kerning
        self.font_size = font_size
        # self.font_vertical_shift = font_vertical_shift

        # Extras
        if flag is None or not flag.exists():
            self.country = self._COUNTRY_FLAGS.get(
                country.upper(), self.REF_DIRECTORY / 'generic.webp'
            )
        else:
            self.country = flag
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.year = frame_year
        self.race = race


    @property
    def static_commands(self) -> ImageMagickCommands:
        """
        Subcommmands to add the race name to the static overlay, frame,
        and country banner to the image.
        """

        return [
            # Create dark overlay
            f'-gravity center',
            fr'\(',
            f'-size {self.TITLE_CARD_SIZE}',
            f'xc:"{self.DARKEN_COLOR}"',
            fr'\)',
            f'-composite',
            # Add frame
            f'"{self.FRAME.resolve()}"',
            f'-composite',
            # Add country banner
            f'"{self.country.resolve()}"',
            f'-composite',
        ]


    @property
    def race_commands(self) -> ImageMagickCommands:
        """Subcommmands to add the race name to the image."""

        # No race, return empty commands
        if not self.race:
            return []

        # Base commands before text size modification
        font_size = 205 * self.font_size
        commands = [
            f'-gravity center',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {font_size}',
            f'-annotate +0-222 "{self.race}"',
        ]

        # Scale font size
        width, _ = self.image_magick.get_text_dimensions(commands)
        INNER_WIDTH = 1725 - (50 * 2) # 50px margin on either side
        if width > INNER_WIDTH:
            font_size *= INNER_WIDTH / width
            commands[-2] = f'-pointsize {font_size}'

        return commands


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands required to add the title text."""

        # No title text, return empty commands
        if not self.title_text:
            return []

        # Base commands before text size modification
        font_size = 155 * self.font_size
        commands = [
            f'-gravity north',
            f'-font "{self.font_file}"',
            f'-fill "{self.font_color}"',
            f'-pointsize {font_size}',
            f'-annotate +0+800 "{self.title_text}"',
        ]

        # Scale font size dynamically if text is too wide
        width, _ = self.image_magick.get_text_dimensions(commands)
        INNER_WIDTH = 1725 - (50 * 2) # 50px margin on either side
        if width > INNER_WIDTH:
            font_size *= INNER_WIDTH / width
            commands[-2] = f'-pointsize {font_size}'

        return commands


    @property
    def season_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the season text to the image."""

        # No season text, return empty commands
        if self.hide_season_text:
            return []

        return [
            f'-gravity north',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {170 * self.episode_text_font_size}',
            f'-annotate +0+390',
            f'"{self.season_text}"',
        ]


    @property
    def episode_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the episode text to the image."""

        # No episode text, return empty commands
        if self.hide_episode_text:
            return []

        return [
            f'-gravity north',
            f'-font "{self.EPISODE_TEXT_FONT.resolve()}"',
            f'-fill "{self.episode_text_color}"',
            f'-pointsize {82 * self.episode_text_font_size}',
            f'-annotate +0+275',
            f'"{self.episode_text}"',
        ]


    @property
    def year_commands(self) -> ImageMagickCommands:
        """Subcommands to add the race year to the image."""

        return [
            f'-gravity southeast',
            f'-font "{self.FRAME_FONT.resolve()}"',
            f'-fill white',
            f'-kerning -10',
            f'-pointsize 165',
            f'-annotate +1915+625 "{self.year}"',
            f'+kerning',
        ]


    def create(self) -> None:
        """Create this object's defined Title Card."""

        self.image_magick.run([
            f'convert "{self.source_file.resolve()}"',
            # Resize and apply styles to source image
            *self.resize_and_style,
            # Add all assets, and text
            *self.static_commands,
            *self.race_commands,
            *self.episode_text_commands,
            *self.season_text_commands,
            *self.title_text_commands,
            *self.year_commands,
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
        airdate: datetime | None = None
        font_color: str = FormulaOneTitleCard.TITLE_COLOR
        font_file: FilePath = FormulaOneTitleCard.TITLE_FONT # type: ignore
        font_size: Annotated[float, Field(gt=0)] = 1.0
        country: Country | None = None
        episode_text_color: str = FormulaOneTitleCard.EPISODE_TEXT_COLOR
        episode_text_font_size: Annotated[float, Field(gt=0)] = 1.0
        flag: Path | None = None
        frame_year: Annotated[int, Field(gt=0)] | None = None
        race: Annotated[
            str,
            StringConstraints(min_length=1, to_upper=True)
        ] = 'GRAND PRIX'

        @model_validator(mode='after')
        def parse_country(self) -> Self:
            """Parse the country from the season text, if none was provided"""
            if self.country is None:
                if self.season_text.upper() in FormulaOneTitleCard._COUNTRY_FLAGS:
                    self.country = self.season_text.upper() # type: ignore
                else:
                    self.country = 'generic'
            return self

        @model_validator(mode='after')
        def validate_flag(self) -> Self:
            """Validate any custom flag files exist"""
            if self.flag is not None:
                if not self.flag.exists():
                    raise ValueError('Specified Flag file does not exist')
            return self

        @model_validator(mode='after')
        def validate_frame_year(self) -> Self:
            """
            Parse the frame year from the airdate of the episode, if
            none was provided.
            """
            if self.frame_year is None:
                if self.airdate:
                    self.frame_year = self.airdate.year
                else:
                    self.frame_year = 2024
            return self

    return CardModel
