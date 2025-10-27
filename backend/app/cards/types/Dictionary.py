from pathlib import Path
from re import compile as re_compile
from typing import Annotated, Any, ClassVar, Self

from app.cards.title import split_into_lines
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
                name='Episode Text Color',
                identifier='episode_text_color',
                description='Color of the season and episode text',
                tooltip=(
                    'Either a single color or two space-separated colors to '
                    'separately color the text and number (in that order). '
                    'Default is to match the Font color.'
                ),
            ),
            Extra(
                name='Episode Text Font Size',
                identifier='episode_text_font_size',
                description='Size adjustment for the season and episode text',
                tooltip='Number ≥<v>0.0</v>. Default is <v>1.0</v>.',
                default=1.0,
            ),
            Extra(
                name='Episode Text Horizontal Shift',
                identifier='episode_text_horizontal_offset',
                description=(
                    'Additional horizontal shift to apply to the episode text.'
                ),
                tooltip='Default is <v>0</v>. Unit is pixels.',
                default=0,
            ),
            Extra(
                name='Episode Text Vertical Shift',
                identifier='episode_text_vertical_offset',
                description=(
                    'Additional vertical shift to apply to the episode text.'
                ),
                tooltip='Default is <v>0</v>. Unit is pixels.',
                default=0,
            ),
            Extra(
                name='Season Text Color',
                identifier='season_text_color',
                description='Color of the season text',
                tooltip=(
                    'Either a single color or two space-separated colors to '
                    'separately color the text and number (in that order). '
                    'Defaults to the episode text color.'
                )
            ),
            Extra(
                name='Stroke Color',
                identifier='stroke_color',
                description='Color of the shadow/stroke',
                tooltip='Defaults to <c>black</c>.',
                default='black',
            ),
            Extra(
                name='Title Text Horizontal Shift',
                identifier='title_text_horizontal_offset',
                description=(
                    'Additional horizontal shift to apply to the title text.'
                ),
                tooltip='Default is <v>0</v>. Unit is pixels.',
                default=0,
            ),
            Extra(
                name='Label Placement',
                identifier='label_placement',
                description=(
                    'Where to position the season/episode label relative to '
                    'the number'
                ),
                tooltip=(
                    'Either <v>above</v>, <v>below</v> or <v>random</v> to '
                    'randomly select a placement. Default is <v>above</v>.'
                ),
                default='above',
            ),
            Extra(
                name='Text Placement',
                identifier='placement',
                description='Position of all text',
                tooltip=(
                    'Either <v>top</v>, <v>bottom</v>, or <v>random</v> to '
                    'randomly select a placement. Default is <v>bottom</v>.'
                ),
                default='bottom',
            ),
            Extra(
                name='Variation',
                identifier='variation',
                description='Which variation of text arrangement to use',
                tooltip=(
                    'Either <v>left</v> to have the season and episode text on '
                    'the left side of the image; <v>right</v> to have it on '
                    'the right; <v>surround</v> to have the text on either side;'
                    ' or <v>random</v> to randomly select a variation. Default '
                    'is <v>surround</v>.'
                ),
                default='surround',
            ),
            Extra(
                name='Remove Gradient',
                identifier='omit_gradient',
                description='Whether to omit the gradient overlay',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. If <v>True</v>, text '
                    'may appear less legible on brighter images. Default is '
                    '<v>False</v>.'
                ),
                default='False',
            ),
        ],
        description=[
            ''
        ]
    )

    """Directory where all reference files used by this card are stored"""
    NEGATIVE_SPACE_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY /'negative_space'
    DICTIONARY_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'dictionary'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=DICTIONARY_DIRECTORY / 'Mencken-Std-Text-Extra-Bold.otf',
        font_color='white',
        font_case='lower',
        title_max_line_width=30,
        title_max_line_count=1,
        title_split_style='bottom',
    )

    BACKGROUND_COLOR: ClassVar[str] = 'black'
    DEFINITION_FONT: ClassVar[Path] = DICTIONARY_DIRECTORY / 'Georgia.ttf'
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
        'font_interline_spacing',
        'font_interword_spacing',
        'font_kerning',
        'font_size',
        'font_vertical_shift',
        'hide_episode_text',
        'hide_season_text',
        '__label_dimensions',
        'output_file',
        'position',
        'season_text',
        'separator',
        'source_file',
        'title_text',
        'word_color',
        '__word_dimensions',
        'word_size',
        'word_text',

        '__reference',
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
            font_color: str = CardConfig.font_color,
            font_file: str = str(CardConfig.font_file),
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_kerning: float = 1.0,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            # Builtins
            blur: bool = False,
            grayscale: bool = False,
            # Extras
            background_color: str = BACKGROUND_COLOR,
            definition_text: str = '',
            definition_color: str = CardConfig.font_color,
            definition_size: float = 1.0,
            definition_line_limit: int = 4,
            position: str = '+100+100',
            separator: str = '-',
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
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = 0 + font_interword_spacing
        self.font_kerning = 1.0 * font_kerning
        self.font_size = font_size
        self.font_vertical_shift = 0 + font_vertical_shift

        # Extras
        self.background_color = background_color
        self.definition_color = definition_color
        self.definition_line_limit = definition_line_limit
        self.definition_size = definition_size
        self.definition_text = self.image_magick.escape_chars(definition_text)
        self.position = position
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


    @property
    def background_commands(self) -> ImageMagickCommands:
        """Subcommands to add the background to the image."""

        # Get the dimensions of the background rectangle
        top_width, top_height = self.background_dimensions

        # Get the dimensions of the definition text
        definition_dimensions = self.image_magick.get_text_label_dimensions(
            self.definition_text_commands,
            density=100,
        )

        # If the definition text is too wide, split into multiple lines
        lines = 1
        while (
            definition_dimensions.width > top_width - 40 # 40px margin
            and (lines := lines + 1) <= 50 # Do not apply limit here
        ):
            # Split into specified number of lines
            self.definition_text = self.image_magick.escape_chars(
                '\n'.join(split_into_lines(self.definition_text, lines))
            )

            # Recalculate the dimensions of the definition text
            definition_dimensions = self.image_magick.get_text_label_dimensions(
                self.definition_text_commands,
                density=100,
            )
            print(f'Split into {lines} lines')

        # If we're above the line limit, truncate with [...]
        if lines > self.definition_line_limit:
            text_lines = self.definition_text.split('\n')[:self.definition_line_limit]
            text_lines[-1] = text_lines[-1][:-4] + ' [...]' # ImageMagick bug breaks this currently
            self.definition_text = self.image_magick.escape_chars(
                '\n'.join(text_lines)
            )
            # Recalculate the dimensions of the definition text
            definition_dimensions = self.image_magick.get_text_label_dimensions(
                self.definition_text_commands,
                density=100,
            )

        width = 35 + top_width + 35 # 35px padding on each side
        height = (
            # 35px padding between texts; need two because of the word,
            # label, and definition text
            35 + top_height + 35 + definition_dimensions.height
            # Remove part of the word height so the background stops in
            # the middle of the word
            - (self.__word_dimensions.height * 0.6)
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
                self.title_text,
                self.separator,
                self.season_text,
                self.episode_text
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

        return [
            fr'\(',
                f'-background none',
                f'-gravity west',
                f'-font "{self.DEFINITION_FONT}"',
                f'-fill "{self.definition_color}"',
                f'-pointsize {45 * self.definition_size:.1f}',
                f'-interline-spacing 5',
                f'label:"{self.definition_text}"',
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
        font_color: str = DictionaryTitleCard.CardConfig.font_color
        font_file: FilePath = DictionaryTitleCard.CardConfig.font_file
        font_interline_spacing: int = 0
        font_interword_spacing: int = 0
        font_kerning: float = 1.0
        font_size: Annotated[float, Field(gt=0)] = 1.0
        font_vertical_shift: int = 0
        background_color: str = DictionaryTitleCard.BACKGROUND_COLOR
        definition_text: str = '{series_name}'
        definition_color: str | None = None
        definition_line_limit: Annotated[int, Field(ge=1, le=12)] = 4
        definition_size: Annotated[float, Field(gt=0)] = 1.0
        position: Annotated[
            str,
            StringConstraints(pattern=DictionaryTitleCard.POSITION_REGEX.pattern)
        ] = '+100+100'
        separator: str = '-'
        word_text: str = '{series_name}'
        word_color: str | None = None

        @model_validator(mode='after')
        def assign_unassigned_color(self) -> Self:
            """Assign any unassigned colors to their default values."""
            if self.definition_color is None:
                self.definition_color = self.font_color
            if self.word_color is None:
                self.word_color = self.font_color
            return self

    return CardModel


create_card_cli(__name__, DictionaryTitleCard, get_validator_model())
