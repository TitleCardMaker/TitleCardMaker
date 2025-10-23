from collections import namedtuple
from pathlib import Path
from re import match as re_match
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import (
    Field,
    FilePath,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.cards.base import (
    BaseCardType,
    CardTypeDescription,
    DefaultCardConfig,
    Extra,
    ImageMagickCommands,
    Shadow,
)
from app.schemas.base import Base, BaseCardModel


DarkenOption = Literal['all', 'box'] | bool
BoxCoordinates = namedtuple('BoxCoordinates', ('x0', 'y0', 'x1', 'y1'))


class LandscapeTitleCard(BaseCardType):
    """
    This class defines a type of CardType that produces title-centric
    cards that do not feature any index text (i.e. season or episode
    text). The title is prominently featured in the center of the image,
    and is intended for landscape-centric images (hence the name) such
    as Planet Earth - as it well likely cover faces in a "typical"
    image. A bounding box around the title can be added/adjusted via
    extras.
    """

    """API Parameters"""
    API_DETAILS = CardTypeDescription(
        name='Landscape',
        identifier='landscape',
        example='/public/cards/landscape.webp',
        creators=['CollinHeist'],
        source='builtin',
        supports_custom_fonts=True,
        supports_custom_seasons=False,
        supported_extras=[
            Extra(
                name='Box Toggle',
                identifier='add_bounding_box',
                description='Whether to add a bounding box around the title text',
                tooltip=(
                    'Either <v>True</v>, or <v>False</v>. Default is '
                    '<v>True</v>.'
                ),
                default='True',
            ),
            Extra(
                name='Box Color',
                identifier='box_color',
                description='Color of the bounding box around the title text',
                tooltip='Default is to match the Font color.',
            ),
            Extra(
                name='Box Adjustments',
                identifier='box_adjustments',
                description='Manual adjustments to the bounds of the bounding box',
                tooltip=(
                    'Specifiy as <v>{top} {right} {bottom} {left}</v> - e.g. '
                    '<v>-20 10 0 5</v>. Positive values move that face out, '
                    'negative values move the face in. Default is '
                    '<v>0 0 0 0</v>. Unit is pixels.'
                ),
                default='0 0 0 0',
            ),
            Extra(
                name='Box Width',
                identifier='box_width',
                description='Thickness of the bounding box',
                tooltip=(
                    'Number ><v>0</v>. Default is <v>10</v>. Unit is pixels.'
                ),
                default=10,
            ),
            Extra(
                name='Box Blurring',
                identifier='blur_box',
                description='Whether to blur behind the bounding box',
                tooltip=(
                    'Either <v>True</v> or <v>False</v>. Default is '
                    '<v>False</v>.'
                ),
                default='False',
            ),
            Extra(
                name='Box Rounding Radius',
                identifier='rounding_radius',
                description='Radius of the rounded corners',
                tooltip=(
                    'Value between <v>0</v> and <v>500</v>.Default is '
                    '<v>0</v>. Unit is pixels.'
                ),
                default=0,
            ),
            Extra(
                name='Blur Profile',
                identifier='blur_profile',
                description='How to blur the area behind the bounding box',
                tooltip=(
                    'Blur formatted as <v>{radius}x{sigma}</v>. Higher '
                    '<v>{sigma}</v> values has the effect of a "stronger" '
                    'blur. Default is <v>0x12</v>.'
                ),
                default='0x12',
            ),
            Extra(
                name='Image Darkening',
                identifier='darken',
                description='Whether to dark all or parts of the image',
                tooltip=(
                    'Either <v>all</v> to darken the entire image, <v>box</v> '
                    'to darken only the bounding box, or <v>False</v> to not'
                    'darken the image at all. This is to improve text '
                    'legibility on very bright images. Default is <v>box</v>.'
                ),
                default='box',
            ),
            Extra(
                name='Darken Color',
                identifier='darken_color',
                description='Color to use for image darkening',
                tooltip='Default is <c>#00000030</c>.',
                default='#00000030',
            ),
            Extra(
                name='Shadow Color',
                identifier='shadow_color',
                description='Color of the text drop shadow.',
                tooltip='Default is <c>black</c>.',
                default='black',
            ),
        ],
        description=[
            'Title-centric title cards that do not feature any text except a '
            'title.', 'These cards are intended for landscape-centric images.',
            'A bounding box around the title text can be added and adjusted '
            'via extras.'
        ]
    )

    """Directory where all reference files used by this card are stored"""
    REF_DIRECTORY = BaseCardType.BASE_REF_DIRECTORY / 'landscape'

    """Default configuration for this card type"""
    CardConfig = DefaultCardConfig(
        font_file=REF_DIRECTORY / 'Geometos.ttf',
        font_color='white',
        title_max_line_width=15,
        title_max_line_count=5,
        title_split_style='top',
        episode_text_format='',
    )

    BOUNDING_BOX_SPACING: Annotated[
        ClassVar[int],
        'Additional spacing between bounding box and title text'
    ] = 150

    BOX_WIDTH: Annotated[ClassVar[int], 'Default box width (in pixels)'] = 10

    DARKEN_COLOR: Annotated[
        ClassVar[str],
        'Color for darkening is black at 30% transparency'
    ] = '#00000030'

    DEFAULT_BOX_COLOR: Annotated[
        ClassVar[str],
        'Default color for the bounding box'
    ] = CardConfig.font_color

    SHADOW_COLOR: Annotated[ClassVar[str], 'Color of the drop shadow'] = 'black'

    BOX_BLUR_PROFILE: Annotated[
        ClassVar[str],
        'Blur profile for the box'
    ] = '0x12'

    ROUNDING_RADIUS: Annotated[
        ClassVar[int],
        'Radius of the rounded corners'
    ] = 0

    __slots__ = (
        'add_bounding_box',
        'blur_box',
        'box_adjustments',
        'box_blur_profile',
        'box_color',
        'box_width',
        'darken',
        'darken_color',
        'font_color',
        'font_file',
        'font_interline_spacing',
        'font_interword_spacing',
        'font_kerning',
        'font_size',
        'font_vertical_shift',
        'output_file',
        'rounding_radius',
        'shadow_color',
        'source_file',
        'title_text',
    )

    def __init__(self, *,
            source_file: Path,
            card_file: Path,
            title_text: str,
            font_color: str = CardConfig.font_color,
            font_file: str = str(CardConfig.font_file),
            font_interline_spacing: int = 0,
            font_interword_spacing: int = 0,
            font_size: float = 1.0,
            font_kerning: float = 1.0,
            font_vertical_shift: float = 0,
            blur: bool = False,
            grayscale: bool = False,
            add_bounding_box: bool = True,
            blur_box: bool = False,
            box_adjustments: tuple[int, int, int, int] = (0, 0, 0, 0),
            box_blur_profile: str = BOX_BLUR_PROFILE,
            box_color: str = DEFAULT_BOX_COLOR,
            box_width: int = BOX_WIDTH,
            darken: DarkenOption = 'box',
            darken_color: str = DARKEN_COLOR,
            rounding_radius: int = 0,
            shadow_color: str = SHADOW_COLOR,
            **unused: Any,
        ) ->None:
        """Construct a new instance of this Card."""

        # Initialize the parent class - this sets up an ImageMagickInterface
        super().__init__(blur, grayscale)

        # Store object attributes
        self.source_file = source_file
        self.output_file = card_file
        self.title_text = self.image_magick.escape_chars(title_text)

        self.font_color = font_color
        self.font_file = font_file
        self.font_interline_spacing = font_interline_spacing
        self.font_interword_spacing = font_interword_spacing
        self.font_size = font_size
        self.font_kerning = font_kerning
        self.font_vertical_shift = font_vertical_shift

        # Store extras
        self.add_bounding_box = add_bounding_box
        self.blur_box = blur_box
        self.box_adjustments = box_adjustments
        self.box_blur_profile = box_blur_profile
        self.box_color = box_color
        self.box_width = box_width
        self.darken = darken
        self.darken_color = darken_color
        self.shadow_color = shadow_color
        self.rounding_radius = rounding_radius


    def darken_commands(self,
            coordinates: BoxCoordinates | tuple[int, int, int, int],
        ) -> ImageMagickCommands:
        """
        Subcommand to darken the image if indicated.

        Args:
            coordinates: Tuple of coordinates to that indicate where to
                darken.

        Returns:
            List of ImageMagick commands.
        """

        # Don't darken if blurring or not enabled
        if self.blur or not self.darken:
            return []

        # Darken only the bounding box coorindates
        if self.darken == 'box':
            x_start, y_start, x_end, y_end = coordinates
            if self.rounding_radius > 0:
                rect = (
                    f'roundrectangle {x_start},{y_start},{x_end},{y_end} '
                    f'{self.rounding_radius},{self.rounding_radius}'
                )
            else:
                rect = f'rectangle {x_start},{y_start},{x_end},{y_end}'

            return [
                fr'-fill "{self.darken_color}"',
                fr'-draw "{rect}"',
            ]

        return [
            # Create image the size of the title card filled with darken color
            fr'\(',
                f'-size "{self.TITLE_CARD_SIZE}"',
                f'xc:"{self.darken_color}"',
            fr'\)',
            # Compose atop of source image
            f'-gravity center',
            f'-composite',
        ]


    def blur_commands(self,
            coordinates: BoxCoordinates,
        ) -> ImageMagickCommands:
        """
        Subcommand to add the blurred image behind the bounding box.

        Args:
            coordinates: Tuple of coordinates to that indicate where to
                darken.

        Returns:
            List of ImageMagick commands.
        """

        if self.blur or not self.blur_box:
            return []

        x_start, y_start, x_end, y_end = coordinates

        return  [
            fr'\(',
                f'-clone 0',
                f'-crop {x_end - x_start}x{y_end - y_start}+0+0',
                f'-blur {self.box_blur_profile}',
            fr'\)',
            f'-geometry -{self.box_width / 2}-20',
            f'-composite',
        ]


    @property
    def bounding_box_coordinates(self) -> BoxCoordinates:
        """The coordinates of the bounding box around the title."""

        # If no bounding box indicated, return blank command
        if not self.add_bounding_box:
            return BoxCoordinates(0, 0, 0, 0)

        font_size = 150 * self.font_size
        interline_spacing = 60 + self.font_interline_spacing
        interword_spacing = 40 + self.font_interword_spacing
        kerning = 40 * self.font_kerning

        # Text-relevant commands
        text_command = [
            f'-font "{self.font_file}"',
            f'-gravity center',
            f'-pointsize {font_size:.1f}',
            f'-interline-spacing {interline_spacing:.1f}',
            f'-interword-spacing {interword_spacing:.1f}',
            f'-kerning {kerning:.2f}',
            f'-fill "{self.font_color}"',
            f'label:"{self.title_text}"',
        ]

        # Get dimensions of text - since text is stacked, do max/sum operations
        width, height = self.image_magick.get_text_label_dimensions(
            ['-background none'] + text_command
        )
        height += 20 # Add 20px margin

        # Get start coordinates of the bounding box
        x_start, x_end = (self.WIDTH - width) / 2, (self.WIDTH + width) / 2
        y_start, y_end = (self.HEIGHT - height) / 2, (self.HEIGHT + height) / 2
        y_end -= 35 # Additional offset necessary for asymmetrical text bounds

        # Shift y coordinates by vertical shift
        y_start += self.font_vertical_shift
        y_end += self.font_vertical_shift

        # Adjust corodinates by spacing and manual adjustments
        x_start -= self.BOUNDING_BOX_SPACING + self.box_adjustments[3]
        x_end   += self.BOUNDING_BOX_SPACING + self.box_adjustments[1]
        y_start -= self.BOUNDING_BOX_SPACING + self.box_adjustments[0]
        y_end   += self.BOUNDING_BOX_SPACING + self.box_adjustments[2]

        return BoxCoordinates(x_start, y_start, x_end, y_end)


    def add_bounding_box_commands(self,
            coordinates: BoxCoordinates,
        ) -> ImageMagickCommands:
        """
        Subcommand to add the bounding box around the title text.

        Args:
            coordinates: Tuple of coordinates to that indicate where to
                darken.

        Returns:
            List of ImageMagick commands.
        """

        # No bounding box, return empty command
        if not self.add_bounding_box:
            return []

        x_start, y_start, x_end, y_end = coordinates
        if self.rounding_radius > 0:
            rect = (
                f'roundrectangle {x_start},{y_start},{x_end},{y_end} '
                f'{self.rounding_radius},{self.rounding_radius}'
            )
        else:
            rect = f'rectangle {x_start},{y_start},{x_end},{y_end}'

        return self.add_drop_shadow(
            [
                f'-size {self.TITLE_CARD_SIZE}',
                f'xc:None',
                f'-fill transparent',
                f'-strokewidth {self.box_width}',
                f'-stroke "{self.box_color}"',
                f'-draw "{rect}"',
            ],
            Shadow(opacity=85, sigma=3, x=10, y=10),
            x=0, y=0,
            shadow_color=self.shadow_color,
        )


    @property
    def title_text_commands(self) -> ImageMagickCommands:
        """Subcommands to add the title text to the image."""

        font_size = 150 * self.font_size
        interline_spacing = 60 + self.font_interline_spacing
        interword_spacing = 40 + self.font_interword_spacing
        kerning = 40 * self.font_kerning

        return self.add_drop_shadow(
            [
                fr'-font "{self.font_file}"',
                fr'-gravity center',
                fr'-pointsize {font_size:.1f}',
                fr'-interline-spacing {interline_spacing:.1f}',
                fr'-interword-spacing {interword_spacing:.1f}',
                fr'-kerning {kerning:.2f}',
                fr'-fill "{self.font_color}"',
                fr'label:"{self.title_text}"',
            ],
            Shadow(opacity=85, sigma=3, x=10, y=10),
            x=0, y=self.font_vertical_shift,
            shadow_color=self.shadow_color,
        )


    def create(self):
        """Create this object's defined Title Card."""

        # If title is blank, just stylize
        if not self.title_text:
            self.image_magick.run([
                fr'convert "{self.source_file.resolve()}"',
                *self.resize_and_style,
                *self.darken_commands((0, 0, 0, 0)),
                fr'"{self.output_file.resolve()}"',
            ])
            return None

        # Get coordinates for bounding box
        bounding_box = self.bounding_box_coordinates

        self.image_magick.run([
            f'convert',
            f'"{self.source_file.resolve()}"',
            # Resize and apply any style modifiers
            *self.resize_and_style,
            # Add box or image darkening
            *self.darken_commands(bounding_box),
            # Add blurred image behind bounding box
            *self.blur_commands(bounding_box),
            # Add title text
            *self.title_text_commands,
            # Optionally add bounding box
            *self.add_bounding_box_commands(bounding_box),
            # Attempt to overlay mask
            *self.add_overlay_mask(self.source_file),
            # Create card
            *self.resize_output,
            fr'"{self.output_file.resolve()}"',
        ])
        return None


def get_validator_model() -> type[Base]:
    """Get the Pydantic validator class for this card type."""

    BoxAdjustmentRegex = r'^([-+]?\d+)\s+([-+]?\d+)\s+([-+]?\d+)\s+([-+]?\d+)$'
    BoxAdjustments = Annotated[str, StringConstraints(pattern=BoxAdjustmentRegex)]

    # pyright: reportInvalidTypeForm=false
    class CardModel(BaseCardModel):
        title_text: str
        font_color: str = LandscapeTitleCard.CardConfig.font_color
        font_file: FilePath = LandscapeTitleCard.CardConfig.font_file
        font_interline_spacing: int = 0
        font_interword_spacing: int = 0
        font_kerning: float = 1.0
        font_size: Annotated[float, Field(gt=0)] = 1.0
        font_vertical_shift: int = 0
        add_bounding_box: bool = True
        blur_box: bool = False
        box_adjustments: BoxAdjustments = (0, 0, 0, 0)
        box_blur_profile: Annotated[
            str,
            StringConstraints(pattern=r'^\d+x\d+$')
        ] = LandscapeTitleCard.BOX_BLUR_PROFILE
        box_color: str | None = None
        box_width: Annotated[int, Field(ge=0)] = LandscapeTitleCard.BOX_WIDTH
        darken: DarkenOption = 'box'
        darken_color: str = LandscapeTitleCard.DARKEN_COLOR
        rounding_radius: Annotated[
            int,
            Field(ge=0, le=500)
        ] = LandscapeTitleCard.ROUNDING_RADIUS
        shadow_color: str = LandscapeTitleCard.SHADOW_COLOR

        @field_validator('box_adjustments', mode='after')
        @classmethod
        def parse_box_adjustments(cls, value: str) -> tuple[int, int, int, int]:
            """Convert box adjustment strings to a tuple of integers"""

            return tuple(map(int, re_match(BoxAdjustmentRegex, value).groups()))

        @model_validator(mode='after')
        def assign_unassigned_color(self) -> Self:
            """Assign any unassigned colors to their default values."""
            if self.box_color is None:
                self.box_color = self.font_color
            return self

    return CardModel
