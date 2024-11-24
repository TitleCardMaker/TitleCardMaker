from pathlib import Path
from random import choice as random_choice
from typing import Literal, TYPE_CHECKING

from modules.BaseCardType import (
    BaseCardType,
    CardTypeDescription,
    Extra,
    ImageMagickCommands,
    Shadow,
)
from modules.Debug import log
from modules.Title import SplitCharacteristics

if TYPE_CHECKING:
    from app.models.preferences import Preferences
    from modules.Font import Font


LabelPlacement = Literal['above', 'below', 'random']
Placement = Literal['top', 'bottom', 'random']
Variation = Literal['left', 'surround', 'right', 'random']


class ScoreTitleCard(BaseCardType):
    """
    CardType that produces title cards ... TODO
    """

    """API Parameters"""
    API_DETAILS: CardTypeDescription = CardTypeDescription(
        name='Score',
        identifier='score',
        example='/internal_assets/cards/score.webp',
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
            'Card type which prominently features the title in the center top '
            'or bottom of the image, and the season and episode text in one '
            '(or more) of the corners.', 'All text is drawn with a drop shadow '
            'for better legibility.', 'Extras can be used to adjust the '
            'positions and colors of all the text.',
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'negative_space'

    """Characteristics for title splitting by this class"""
    TITLE_CHARACTERISTICS: SplitCharacteristics = {
        'max_line_width': 20,
        'max_line_count': 3,
        'style': 'bottom',
    }

    """Characteristics of the default title font"""
    TITLE_FONT: str = str((REF_DIRECTORY / 'Futura.ttc').resolve())
    TITLE_COLOR: str = 'white'
    DEFAULT_FONT_CASE = 'upper'
    FONT_REPLACEMENTS: dict[str, str] = {}

    """Characteristics of the episode text"""
    EPISODE_TEXT_FORMAT = 'EPISODE {episode_number}'
    EPISODE_TEXT_COLOR = TITLE_COLOR
    EPISODE_TEXT_FONT = TITLE_FONT

    """Whether this CardType uses season titles for archival purposes"""
    USES_SEASON_TITLE: bool = False

    """How to name archive directories for this type of card"""
    ARCHIVE_NAME: str = 'Score Style'

    """Default variables"""
    STROKE_COLOR: str = 'black'

    """Path to the gradient image to overlay"""
    _GRADIENT_IMAGE = REF_DIRECTORY.parent / 'anime' / 'GRADIENT.png'

    __slots__ = (
        'episode_text',
        'episode_text_color',
        'episode_text_font_size',
        'episode_text_horizontal_offset',
        'episode_text_vertical_offset',
        'font_file',
        'font_color',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_kerning',
        'font_size',
        'font_vertical_shift',
        'hide_episode_text',
        'hide_season_text',
        'label_placement',
        'omit_gradient',
        'output_file',
        'placement',
        'season_text',
        'season_text_color',
        'source_file',
        'stroke_color',
        'text_side',
        'title_text',
        'title_text_horizontal_offset',
        'variation',
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
            episode_text_color: str = EPISODE_TEXT_COLOR,
            episode_text_font_size: float = 1.0,
            episode_text_horizontal_offset: int = 0,
            episode_text_vertical_offset: int = 0,
            season_text_color: str = EPISODE_TEXT_COLOR,
            stroke_color: str = STROKE_COLOR,
            title_text_horizontal_offset: int = 0,
            label_placement: LabelPlacement = 'above',
            omit_gradient: bool = False,
            placement: Placement = 'bottom',
            variation: Variation = 'surround',
            preferences: 'Preferences | None' = None,
            **unused,
        ) -> None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale, preferences=preferences)

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
        self.episode_text_color = episode_text_color
        self.episode_text_font_size = episode_text_font_size
        self.episode_text_horizontal_offset = episode_text_horizontal_offset
        self.episode_text_vertical_offset = episode_text_vertical_offset
        self.season_text_color = season_text_color
        self.stroke_color = stroke_color
        self.title_text_horizontal_offset = title_text_horizontal_offset
        self.omit_gradient = omit_gradient
        if label_placement == 'random':
            label_placement = random_choice(['above', 'below'])
        self.label_placement = label_placement
        if placement == 'random':
            placement = random_choice(['bottom', 'top'])
        self.placement = placement
        if variation == 'random':
            variation = random_choice(['left', 'surround', 'right'])
        self.variation = variation


    @property
    def gradient_command(self) -> ImageMagickCommands:
        """Subcommands to add the gradient to the image."""

        # Gradient omitted, return empty commands
        if self.omit_gradient:
            return []

        # Rotate based on text placement
        rotation = 180 if self.placement == 'top' else 0

        return [
            fr'\( "{self._GRADIENT_IMAGE.resolve()}"',
            fr'-gravity center',
            fr'-rotate {rotation} \)',
            fr'-composite',
        ]


    @property
    def _season_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the season text to the image. This includes a
        drop shadow, but does not include composition commands.
        """

        # Season text hidden
        if self.hide_season_text:
            return []

        # Global font characteristics
        text_size = 70 * self.episode_text_font_size
        number_size = 325 * self.episode_text_font_size

        # Determine each color
        text_color = number_color = self.season_text_color
        if ' ' in self.season_text_color:
            text_color, number_color = self.season_text_color.split(' ', 1)

        # Parse label and number text
        prefix, number = '', self.season_text
        if ' ' in self.season_text:
            prefix, number = self.season_text.rsplit(' ', maxsplit=1)

        # Commands to draw the prefix (SEASON) text
        prefix_cmds = []
        if prefix:
            prefix_cmds = [
                fr'-fill "{text_color}"',
                fr'-pointsize {text_size:.1f}',
                fr'label:"{prefix}"',
            ]

        # Commands to draw the number text
        number_cmds = [
            fr'-fill "{number_color}"',
            fr'-pointsize {number_size:.1f}',
            fr'label:"{number}"',
        ]

        return self.add_drop_shadow(
            [
                fr'\( -background transparent',
                fr'-font "{self.EPISODE_TEXT_FONT}"',
                *(prefix_cmds if self.label_placement == 'above' else number_cmds),
                *(number_cmds if self.label_placement == 'above' else prefix_cmds),
                # Combine two text images (vertically)
                fr'-gravity center',
                fr'-smush 15' if prefix else fr'',
                fr'\)',
            ],
            Shadow(opacity=90, sigma=2, x=7, y=7),
            shadow_color=self.stroke_color,
            compose=False,
        )


    @property
    def _episode_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the episode text to the image. This includes
        a drop shadow, but does not include composition commands.
        """

        # Episode text hidden
        if self.hide_episode_text:
            return []

        # Global font characteristics
        text_size = 70 * self.episode_text_font_size
        number_size = 325 * self.episode_text_font_size

        # Determine each color
        text_color = number_color = self.episode_text_color
        if ' ' in self.episode_text_color:
            text_color, number_color = self.episode_text_color.split(' ', 1)

        # Parse label and number text
        prefix, number = '', self.episode_text
        if ' ' in self.episode_text:
            prefix, number = self.episode_text.rsplit(' ', maxsplit=1)

        # Commands to draw the prefix (SEASON) text
        prefix_cmds = []
        if prefix:
            prefix_cmds = [
                fr'-fill "{text_color}"',
                fr'-pointsize {text_size:.1f}',
                fr'label:"{prefix}"',
            ]

        # Commands to draw the number text
        number_cmds = [
            fr'-fill "{number_color}"',
            fr'-pointsize {number_size:.1f}',
            fr'label:"{number}"',
        ]

        return self.add_drop_shadow(
            [
                fr'\( -background transparent',
                fr'-font "{self.EPISODE_TEXT_FONT}"',
                *(prefix_cmds if self.label_placement == 'above' else number_cmds),
                *(number_cmds if self.label_placement == 'above' else prefix_cmds),
                # Combine two text images (vertically)
                fr'-gravity center',
                fr'-smush 15' if prefix else fr'',
                fr'\)',
            ],
            Shadow(opacity=90, sigma=2, x=7, y=7),
            shadow_color=self.stroke_color,
            compose=False,
        )


    @property
    def index_text_commands(self) -> ImageMagickCommands:
        """
        Subcommands to add the season and episode text to the image.
        """

        # All text hidden, return empty commands
        if self.hide_season_text and self.hide_episode_text:
            return []

        # Determine gravity prefix based on overall placement
        gravity_prefix = 'north' if self.placement == 'top' else 'south'

        # Determine coordinates
        x = 50 + self.episode_text_horizontal_offset
        y = self.episode_text_vertical_offset + {
            'top above': -25 + 50,
            'top below': -25 + 25,
            'bottom above': 25 - 50,
            'bottom below': 25 + 25,
        }[f'{self.placement} {self.label_placement}']

        # Surround style is [ season / title / episode ]
        if self.variation == 'surround':
            season_text, episode_text = [], []
            if not self.hide_season_text:
                season_text = [
                    *self._season_text_commands,
                    f'-gravity {gravity_prefix}west',
                    f'-geometry {x:+}{y:+}',
                    f'-composite',
                ]
            if not self.hide_episode_text:
                episode_text = [
                    *self._episode_text_commands,
                    f'-gravity {gravity_prefix}east',
                    f'-geometry {x:+}{y:+}',
                    f'-composite',
                ]
            return season_text + episode_text

        # Left style is [ season / episode / title ]
        if self.variation == 'left':
            return [
                fr'\(',
                *self._season_text_commands,
                *self._episode_text_commands,
                fr'-gravity west',
                fr'+smush 65 \)',
                fr'-gravity {gravity_prefix}west',
                fr'-geometry {x:+}{y:+}',
                fr'-composite',
            ]

        # Right style is [ title / season / episode ]
        return [
            fr'\(',
            *self._season_text_commands,
            *self._episode_text_commands,
            fr'-gravity east',
            fr'+smush 65 \)',
            fr'-gravity {gravity_prefix}east',
            fr'-geometry {x:+}{y:+}',
            fr'-composite',
        ]


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the title text to the image."""

        # No title text, return blank commands
        if not self.title_text:
            return []

        # Font characteristics
        interline_spacing = -30 + self.font_interline_spacing
        interword_spacing = 40 + self.font_interword_spacing
        kerning = 1 * self.font_kerning
        size = 135 * self.font_size

        # Text placement
        gravity = 'north' if self.placement == 'top' else 'south'
        y = 85 + self.font_vertical_shift

        # Assume each piece of text is 375px wide, half that since it's centered
        x = 0
        if self.variation != 'surround':
            text_count =(not self.hide_season_text)+(not self.hide_episode_text)
            width = 187 * text_count * self.episode_text_font_size
            width *= 1 if self.variation == 'left' else -1
            x = width
        x += self.title_text_horizontal_offset

        return self.add_drop_shadow(
            [
                f'-fill "{self.font_color}"',
                f'-font "{self.font_file}"',
                f'-interline-spacing {interline_spacing}',
                f'-interword-spacing {interword_spacing}',
                f'-kerning {kerning}',
                f'-pointsize {size}',
                f'-gravity {gravity}',
                f'label:"{self.title_text}"',
            ],
            shadow=Shadow(opacity=90, sigma=2, x=7, y=7),
            x=x, y=y,
            shadow_color=self.stroke_color,
        )


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

        # Generic font, reset episode text and box colors
        if not custom_font:
            for extra in (
                'episode_text_color',
                'episode_text_font_size',
                'episode_text_horizontal_offset',
                'episode_text_vertical_offset',
                'season_text_color',
                'stroke_color',
                'title_text_horizontal_offset',
            ):
                if extra in extras:
                    del extras[extra]


    @staticmethod
    def is_custom_font(font: 'Font', extras: dict) -> bool:
        """
        Determine whether the given font characteristics constitute a
        default or custom font.

        Args:
            font: The Font being evaluated.
            extras: Dictionary of extras for evaluation.

        Returns:
            True if a custom font is indicated, False otherwise.
        """

        custom_extras = (
            ('episode_text_color' in extras
                and extras['episode_text_color'] != \
                    ScoreTitleCard.EPISODE_TEXT_COLOR)
            or extras.get('episode_text_font_size', 1.0) != 1.0
            or extras.get('episode_text_horizontal_offset', 0) != 0
            or extras.get('episode_text_vertical_offset', 0) != 0
            or ('season_text_color' in extras
                and extras['season_text_color'] != \
                    ScoreTitleCard.EPISODE_TEXT_COLOR)
            or ('stroke_color' in extras
                and extras['stroke_color'] != ScoreTitleCard.STROKE_COLOR)
            or extras.get('title_text_horizontal_offset', 0) != 0
        )

        return (custom_extras
            or ((font.color != ScoreTitleCard.TITLE_COLOR)
            or (font.file != ScoreTitleCard.TITLE_FONT)
            or (font.interline_spacing != 0)
            or (font.interword_spacing != 0)
            or (font.kerning != 1.0)
            or (font.size != 1.0)
            or (font.vertical_shift != 0))
        )


    @staticmethod
    def is_custom_season_titles(
            custom_episode_map: bool,
            episode_text_format: str,
        ) -> bool:
        """
        Determine whether the given attributes constitute custom or
        generic season titles.

        Args:
            custom_episode_map: Whether the EpisodeMap was customized.
            episode_text_format: The episode text format in use.

        Returns:
            True if custom season titles are indicated, False otherwise.
        """

        return (
            custom_episode_map
            or episode_text_format != ScoreTitleCard.EPISODE_TEXT_FORMAT
        )


    def create(self) -> None:
        """Create this object's defined Title Card."""

        self.image_magick.run([
            fr'convert',
            # Resize and style source image
            fr'"{self.source_file.resolve()}"',
            *self.resize_and_style,
            # Overlay gradient
            *self.gradient_command,
            *self.index_text_commands,
            *self.title_text_commands,
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            fr'"{self.output_file.resolve()}"',
        ])
