from pathlib import Path
from re import compile as re_compile
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Self

from app.cards.title import split_into_lines
from app.logging.logger import Logger, log
from app.utils.fstring import FormatString
from pydantic import Field, FilePath, StringConstraints, model_validator

from app.cards.base import (
    BaseCardType,
    CardTypeDescription,
    Coordinate,
    DefaultCardConfig,
    Dimensions,
    Extra,
    ImageMagickCommands,
    create_card_cli,
)
from app.schemas.base import BaseCardModel, BaseCardTypeAllText

if TYPE_CHECKING:
    from app.info.episode import EpisodeInfo
    from app.info.series import SeriesInfo
    from app.interfaces.tmdb import TMDbInterface


class DictionaryTitleCard(BaseCardType):
    """
    CardType that produces title cards featuring a dictionary-definition
    inspired layout.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Dictionary',
        identifier='dictionary',
        example='/public/cards/dictionary.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=True,
        supported_extras=[
            Extra(
                name='Background Color',
                identifier='background_color',
                description='Color of the background rectangle',
                tooltip='Default is <c>rgba(12,12,12,0.8)</c>.',
                default='rgba(12,12,12,0.8)',
            ),
            Extra(
                name='Definition Text',
                identifier='definition_text',
                description='Text to display as the definition',
                tooltip=(
                    'Extended text to diplay below the word and label text. '
                    'The default is <v>{episode_description}</v>, which means '
                    'the episode description will be pulled from TMDb (if '
                    'available). Disable this by specifying <v>""</v>.'
                ),
                default='{episode_description}',
            ),
            Extra(
                name='Definition Color',
                identifier='definition_color',
                description='Color of the definition text',
                tooltip='Default is to match the Font color.',
            ),
            Extra(
                name='Definition Font Size',
                identifier='definition_size',
                description='Size adjustment for the definition text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Definition Line Limit',
                identifier='definition_line_limit',
                description=(
                    'Maximum number of lines to display for the definition text'
                ),
                tooltip=(
                    'Number between <v>1</v> and <v>24</v>. Descriptions '
                    'longer than this many lines will be truncated. Default is '
                    '<v>4</v>.'
                ),
                default=4,
            ),
            Extra(
                name='Italicize Definition Toggle',
                identifier='italicize_definition',
                description='Whether to italicize the definition text',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>True</v>.'
                ),
                default='True',
            ),
            Extra(
                name='Quote Definition Toggle',
                identifier='quote_definition',
                description='Whether to add quotes around the definition text',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is <v>True</v>.'
                ),
                default='True',
            ),
            Extra(
                name='Position',
                identifier='position',
                description='Position of the definition text',
                tooltip=(
                    'X and Y coordinates to position the bottom left corner of '
                    'the text container. Default is <v>+100+100</v> - i.e. 100 '
                    'pixels from the left and 100 pixels from the bottom.'
                ),
                default='+100+100',
            ),
            Extra(
                name='Separator Character',
                identifier='separator',
                description=(
                    'Character to separate the title from the index text'
                ),
                tooltip='Default is <v>, </v>.',
                default=', ',
            ),
            Extra(
                name='Word Text',
                identifier='word_text',
                description='Text to display as the word',
                tooltip=(
                    'Default is the series name in lowercase - i.e. '
                    '<v>{series_name.lower()}</v>.'
                ),
                default='{series_name.lower()}',
            ),
            Extra(
                name='Word Text Color',
                identifier='word_color',
                description='Color of the word text',
                tooltip='Default is to match the Font color.',
            ),
            Extra(
                name='Word Text Font Size',
                identifier='word_size',
                description='Size adjustment for the word text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
        ],
        description=[
            'Card type designed to resemble a dictionary entry/definition. '
            'These cards feature a background rectangle, a "word" which '
            'defaults to the series name in lowercase, a "label" which is the '
            'episode title, and a "definition" which is the episode'
            'description.', 'This card is designed to automatically pull '
            'the episode description from TMDb, if possible.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    NEGATIVE_SPACE_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY /'negative_space'
    DICTIONARY_DIR = BaseCardType.BASE_REF_DIRECTORY / 'dictionary'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=DICTIONARY_DIR / 'Mencken-Std-Text-Extra-Bold.otf',
        font_color='white',
        font_case='lower',
        title_max_line_width=30,
        title_max_line_count=1,
        title_split_style='bottom',
        episode_text_format=': {episode_number}',
    )

    BACKGROUND_COLOR: ClassVar[str] = 'rgba(12,12,12,0.8)'
    DEFINITION_FONT: ClassVar[Path] = DICTIONARY_DIR / 'Georgia.ttf'
    DEFINITION_ITALIC_FONT: ClassVar[Path] = DICTIONARY_DIR / 'Georgia Italic.ttf'
    WORD_FONT: ClassVar[Path] = NEGATIVE_SPACE_DIRECTORY / 'Futura.ttc'
    POSITION_REGEX = re_compile(r'([-+]\d+.?\d*)([-+]\d+.?\d*)')

    __slots__ = (
        'background_color',
        'definition_color',
        '__definition_dimensions',
        'definition_line_limit',
        'definition_size',
        'definition_text',
        'episode_text',
        'font_file',
        'font_color',
        'font_interword_spacing',
        'font_kerning',
        'font_size',
        'hide_episode_text',
        'hide_season_text',
        'italicize_definition',
        '__label_dimensions',
        'output_file',
        'position',
        'quote_definition',
        '__reference',
        'season_text',
        'separator',
        'source_file',
        'title_text',
        'word_color',
        '__word_dimensions',
        'word_size',
        'word_text',
    )


    @staticmethod
    def SEASON_TEXT_FORMATTER(episode_info: 'EpisodeInfo') -> str:
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

        return '{season_number}'


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
            font_color: str = CardConfig.font_color,
            font_file: str = str(CardConfig.font_file),
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            # Builtins
            blur: bool = False,
            grayscale: bool = False,
            # Extras
            background_color: str = BACKGROUND_COLOR,
            definition_text: str = '',
            definition_color: str = CardConfig.font_color,
            definition_size: float = 1.0,
            definition_line_limit: int = 4,
            italicize_definition: bool = False,
            position: str = '+100+100',
            quote_definition: bool = True,
            separator: str = ', ',
            word_text: str = '',
            word_size: float = 1.0,
            word_color: str = CardConfig.font_color,
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
        self.font_interword_spacing = font_interword_spacing
        self.font_kerning = font_kerning
        self.font_size = font_size

        # Extras
        self.background_color = background_color
        self.definition_color = definition_color
        self.definition_line_limit = definition_line_limit
        self.definition_size = definition_size
        self.definition_text = self.image_magick.escape_chars(definition_text)
        self.italicize_definition = italicize_definition
        self.position = position
        self.quote_definition = quote_definition
        self.separator = separator
        self.word_text = self.image_magick.escape_chars(word_text)
        self.word_color = word_color
        self.word_size = word_size

        # Implementation variables
        self.__word_dimensions = Dimensions(0, 0)
        self.__label_dimensions = Dimensions(0, 0)

        x, y = 100, 100
        if (match := self.POSITION_REGEX.match(position)):
            x, y = match.groups()
        self.__reference = Coordinate(float(x), float(y))


    @staticmethod
    def enrich_card_data(
            series_info: 'SeriesInfo',
            episode_info: 'EpisodeInfo',
            *,
            episode_description: str = '{episode_description}',
            tmdb_interface: 'TMDbInterface | None' = None,
            log: Logger = log,
            **kwargs: Any,
        ) -> dict[str, Any]:
        """
        Enrich the card data with an episode description from TMDb.

        Args:
            series_info: SeriesInfo for the series being processed.
            episode_info: EpisodeInfo for the episode being processed.
            episode_description: The value of the episode description
                extra.
            tmdb_interface: TMDbInterface if available, None otherwise.
            **kwargs: Additional optional parameters.

        Returns:
            Dictionary of additional data to merge into card_settings.
        """

        description = ''

        # If the episode description is a format string, query
        if ('{' in episode_description
            and '}' in episode_description
            and 'episode_description' in episode_description
            and tmdb_interface # TMDb is required to query description
        ):
            description = tmdb_interface.get_episode_description(
                series_info, episode_info, log=log
            ) or '' # Coerce None to an empty string

        return {'episode_description': description}


    @property
    def background_dimensions(self) -> Dimensions:
        """
        Partial dimensions of the background rectangle. These are just
        the dimensions of the word and label texts, and does not include
        the definition text.
        """

        if not self.word_text:
            return Dimensions(0, 0)

        word_width, word_height = self.__word_dimensions
        label_width, label_height = self.__label_dimensions

        effective_width = max(word_width, label_width, 300) # 300px minimum

        return Dimensions(effective_width, word_height + label_height)


    def _fit_definition_text(self, max_width: int | float) -> Dimensions:
        """
        Attempt to fit the definition text to the given maximum width.

        Args:
            max_width: Maximum width of the definition text, in pixels.

        Returns:
            Dimensions of the definition text after it has been split
            into multiple lines.
        """

        # Get the starting dimensions of the unsplit definition text
        definition_dimensions = self.image_magick.get_text_label_dimensions(
            self.definition_text_commands,
            density=100,
        )

        # If the definition text is too wide, split into multiple lines
        # this loop will exit when the text is no longer too wide
        lines = 1
        while (
            definition_dimensions.width > max_width - 35 - 35 # 35px margin on each side
            and (lines := lines + 1) <= 24 # Do not apply user limit here
        ):
            # Split into specified number of lines
            self.definition_text = self.image_magick.escape_chars(
                '\n'.join(split_into_lines(self.definition_text, lines))
            )

            # Recalculate the dimensions of the definition text after each split
            definition_dimensions = self.image_magick.get_text_label_dimensions(
                self.definition_text_commands,
                density=100,
            )

        # If we're above the maximum line width, find the number of
        # lines which results in the best fit (closest to the maximum
        # width) and then truncate the text to that number of lines.
        if lines > self.definition_line_limit:
            # Truncate final line with (...)
            # TODO change to [...] when ImageMagick bug is fixed
            text_lines = (
                self.definition_text.splitlines()[:self.definition_line_limit]
            )
            text_lines[-1] = text_lines[-1].rsplit(' ', 1)[0] + ' (...)'
            self.definition_text = self.image_magick.escape_chars(
                '\n'.join(text_lines)
            )
            definition_dimensions = self.image_magick.get_text_label_dimensions(
                self.definition_text_commands,
                density=100,
            )

        return definition_dimensions


    @property
    def background_commands(self) -> ImageMagickCommands:
        """Subcommands to add the background to the image."""

        # Get the dimensions of the background rectangle
        top_width, top_height = self.background_dimensions

        # Get the dimensions of the definition text
        definition_dimensions = self._fit_definition_text(top_width)

        width = 35 + top_width + 35 # 35px padding on each side
        height = (
            # 35px padding between texts; need two because of the word,
            # label, and definition text
            35 + top_height + 35 + definition_dimensions.height
            # Remove part of the word height so the background stops in
            # the middle of the word
            - (self.__word_dimensions.height * 0.35)
        )

        return [
            fr'\(',
                f'-size {width}x{height}',
                f'xc:"{self.background_color}"',
            fr'\)',
            f'-gravity southwest',
            f'-geometry {self.__reference.x - 35:+}{self.__reference.y - 35:+}',
            f'-composite',
            f'+size',
        ]


    @property
    def word_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the word text to the image."""

        return [
            fr'\(',
                f'-background none',
                f'-gravity center',
                f'-interword-spacing 100',
                f'-kerning -10.0',
                f'-font "{self.WORD_FONT.resolve()}"',
                f'-fill "{self.word_color}"',
                f'-pointsize {250 * self.word_size:.1f}',
                f'label:"{self.word_text}"',
                f'-trim',
            fr'\)',
        ]


    @property
    def label_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the label text to the image."""

        label_text = ' '.join(
            text
            for text in [
                self.title_text + self.separator,
                '' if self.hide_season_text else self.season_text,
                '' if self.hide_episode_text else self.episode_text,
            ]
            if text
        )

        return [
            fr'\(',
                f'-background none',
                f'-gravity center',
                f'-interword-spacing {20 + self.font_interword_spacing}',
                f'-kerning {3 * self.font_kerning:.1f}',
                f'-font "{self.font_file}"',
                f'-fill "{self.font_color}"',
                f'-pointsize {50 * self.font_size:.1f}',
                f'label:"{label_text}"',
                f'-trim',
            fr'\)',
        ]


    @property
    def definition_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the title text to the image."""

        if not self.definition_text:
            return []

        file = self.DEFINITION_FONT
        if self.italicize_definition:
            file = self.DEFINITION_ITALIC_FONT

        text = self.definition_text
        if self.quote_definition:
            text = fr'\"{self.definition_text}\"'

        return [
            fr'\(',
                f'-background none',
                f'-gravity west',
                f'-font "{file.resolve()}"',
                f'-fill "{self.definition_color}"',
                f'-pointsize {45 * self.definition_size:.1f}',
                # Reset carry over font characteristics
                f'+interline-spacing',
                f'+interword-spacing',
                f'+kerning',
                fr'label:"{text}"',
                f'-trim',
            fr'\)',
        ]


    def create(self) -> None:
        """Create this object's defined Title Card."""

        self.__word_dimensions = self.image_magick.get_text_label_dimensions(
            self.word_text_commands,
            density=100,
        )

        self.__label_dimensions = self.image_magick.get_text_label_dimensions(
            self.label_text_commands,
            density=100,
        )

        self.image_magick.run([
            f'convert',
            f'-density 100',
            # Resize and style source image
            f'"{self.source_file.resolve()}"',
            *self.resize_and_style,
            *self.background_commands,
            fr'\(',
                *self.word_text_commands,
                *self.label_text_commands,
                *self.definition_text_commands,
                f'-gravity west',
                f'-smush 35',
            fr'\)',
            f'-gravity southwest',
            f'-geometry {self.__reference.x:+}{self.__reference.y:+}',
            f'-composite',
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            f'"{self.output_file.resolve()}"',
        ])


def get_validator_model() -> type[BaseCardModel]:
    """Get the Pydantic validator class for this card type."""

    class CardModel(BaseCardTypeAllText):
        season_text: str
        episode_text: str
        font_color: str = DictionaryTitleCard.CardConfig.font_color
        font_file: FilePath = DictionaryTitleCard.CardConfig.font_file
        font_interword_spacing: int = 0
        font_kerning: float = 1.0
        font_size: Annotated[float, Field(gt=0)] = 1.0
        background_color: str = DictionaryTitleCard.BACKGROUND_COLOR
        italicize_definition: bool = True
        quote_definition: bool = True
        definition_text: str = '{episode_description}'
        definition_color: str | None = None
        definition_line_limit: Annotated[int, Field(ge=1, le=24)] = 4
        definition_size: Annotated[float, Field(gt=0)] = 1.0
        position: Annotated[
            str,
            StringConstraints(pattern=DictionaryTitleCard.POSITION_REGEX.pattern)
        ] = '+100+100'
        separator: str = ', '
        word_text: str = '{series_name.lower()}'
        word_color: str | None = None
        word_size: Annotated[float, Field(gt=0)] = 1.0

        @model_validator(mode='after')
        def assign_unassigned_color(self) -> Self:
            """Assign any unassigned colors to their default values."""
            if self.definition_color is None:
                self.definition_color = self.font_color
            if self.word_color is None:
                self.word_color = self.font_color
            return self

        @model_validator(mode='before')
        @classmethod
        def validate_default_format_strings(cls, data: Any) -> Any:
            """Apply"""

            # Parse format strings in word and definition text
            if isinstance(data, dict):
                if ((word_text := data.get('word_text', '{series_name.lower()}'))
                    and isinstance(word_text, str)
                ):
                    data['word_text'] = FormatString(word_text, data=data).result
                if ((definition_text := data.get('definition_text', '{episode_description}'))
                    and isinstance(definition_text, str)
                ):
                    data['definition_text'] = FormatString(
                        definition_text, data=data
                    ).result

            return data

    return CardModel


create_card_cli(__name__, DictionaryTitleCard, get_validator_model())
