from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Callable, ClassVar, Literal

from pydantic import BaseModel, BeforeValidator, Field, FilePath, ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError
from titlecase import titlecase

from app.logging.logger import log
from app.magick.base import (
    Dimensions,
    ImageMaker,
    ImageMagickCommands,
    ImageStack,
)
from app.schemas.base import BaseCardModel
from app.schemas.card import CardTypeDescription, Extra

if TYPE_CHECKING:
    from app.info.episode import EpisodeInfo
    from app.info.series import SeriesInfo

CardDescription = CardTypeDescription
type SplitStyle = Literal['top', 'bottom', 'even', 'forced even']
type TextCase = Literal['blank', 'lower', 'source', 'title', 'upper']


class Coordinate:
    """Class that defines a single Coordinate on an x/y plane."""

    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float) -> None:
        """Initialize this Coordinate with the given x/y coordinates."""

        self.x = x
        self.y = y


    def __iter__(self) -> Iterable[tuple[float, float]]:
        """
        Iterate through this object. This can be used to unpack the
        Coordinate, for example:

        >>> x, y = Coordinate(1, 2) # x=1, y=2
        """

        return iter((self.x, self.y))


    def __add__(self,
            other: 'Coordinate | tuple[float | int, float | int]',
        ) -> 'Coordinate':
        """
        Add the given coordinates to this object, returning a new
        combination of the two.

        Args:
            other: The Coordinate to add.

        Returns:
            Newly constructed Coordinate object of these coordinates.
        """

        if isinstance(other, Coordinate):
            return Coordinate(self.x + other.x, self.y + other.y)

        return Coordinate(self.x + other[0], self.y + other[1])


    def __sub__(self,
            other: 'Coordinate | tuple[float | int, float | int]',
        ) -> 'Coordinate':
        """
        Subtract the given coordinates to this object, returning a new
        combination of the two.

        Args:
            other: The Coordinate to subtract.

        Returns:
            Newly constructed Coordinate object of these coordinates.
        """

        if isinstance(other, Coordinate):
            return Coordinate(self.x - other.x, self.y - other.y)

        return Coordinate(self.x - other[0], self.y - other[1])


    def __iadd__(self,
            other: 'Coordinate | tuple[float | int, float | int]',
        ) -> 'Coordinate':
        """
        Add the given Coordinate to this one. This adds the x/y
        positions individually.

        Args:
            other: The Coordinate to add.

        Returns:
            This object.
        """

        if isinstance(other, Coordinate):
            self.x += other.x
            self.y += other.y
        else:
            self.x += other[0]
            self.y += other[1]

        return self


    def __repr__(self) -> str:
        """
        Detailed object representation.
        
        >>> repr(Coordinate(2, 3))
        'Coordinate(2, 3)'
        """
        return f'Coordinate({self.x}, {self.y})'


    def __str__(self) -> str:
        """
        Represent this Coordinate as a string.

        >>> str(Coordinate(1.2, 3.4))
        '1,2'
        """

        return f'{self.x:.0f},{self.y:.0f}'

    @property
    def as_svg(self) -> str:
        """SVG representation of this Coordinate."""

        return f'{self.x:.1f} {self.y:.1f}'


class Line:
    """Class that defines a drawable SVG line."""

    __slots__ = ('start', 'end')

    def __init__(self,
            start: Coordinate | tuple[int | float, int | float],
            end: Coordinate | tuple[int | float, int | float],
        ) -> None:
        """
        Initialize a Line which spans between the given start and end
        Coordinates.

        Args:
            start: Coordinate which defines one end of this line.
            end: Coordinate which defines the other end of this line.
        """

        if isinstance(start, tuple):
            start = Coordinate(*start)
        self.start = start

        if isinstance(end, tuple):
            end = Coordinate(*end)
        self.end = end


    def __str__(self) -> str:
        """Represent this Line as a string. This is a SVG-command."""

        return f'M {str(self.start)} L {str(self.end)}'


    def draw(self) -> str:
        """Draw this line."""

        return f'-draw "path \'{str(self)}\'"'


class Rectangle:
    """Class that defines movable SVG rectangle."""

    __slots__ = ('start', 'end')

    def __init__(self, start: Coordinate, end: Coordinate) -> None:
        """
        Initialize this Rectangle that encompasses the given start and
        end Coordinates. These Coordinates are the opposite corners of
        the rectangle.

        Args:
            start: Coordinate which defines one starting corner of the
                rectangle.
            end: Coordinate which opposites the `start` coordinate of
                this rectangle.
        """

        self.start = start
        self.end = end


    def __repr__(self) -> str:
        """Unambiguous representation of this object."""

        return f'Rectangle({self.start!r}, {self.end!r})'


    def __str__(self) -> str:
        """
        Represent this Rectangle as a string. This is the joined string
        representation of the start and end coordinate.
        """

        return f'{str(self.start)},{str(self.end)}'


    @property
    def width(self) -> float:
        """Width of this Rectangle."""

        return abs(self.start.x - self.end.x)

    @property
    def height(self) -> float:
        """Height of this Rectangle."""

        return abs(self.start.y - self.end.y)


    def draw(self) -> str:
        """Draw this Rectangle."""

        return f'-draw "rectangle {str(self)}"'


class Shadow:
    """Class which defines a shadow string."""

    __slots__ = ('opacity', 'sigma', 'x', 'y')

    def __init__(self,
            *,
            opacity: int = 95,
            sigma: int = 2,
            x: int = 10,
            y: int = 10,
        ) -> None:
        """Construct a shadow with the given parameters."""

        self.opacity = opacity
        self.sigma = sigma
        self.x = x
        self.y = y


    def __str__(self) -> str:
        """String representation of this shadow effect."""

        return f'{self.opacity}x{self.sigma}{self.x:+}{self.y:+}'


    @property
    def as_command(self) -> str:
        """Wrapper for `__str__`."""

        return str(self)


def coerce_path(v: Path | Any) -> str | Any:
    return str(v.resolve()) if isinstance(v, Path) else v


class DefaultCardConfig(BaseModel):
    """
    Base configuration class for card types. Card-specific Config
    classes should instantiate this class.
    
    This consolidates all user-facing default settings into a single
    configuration object for better organization and maintainability.
    """

    font_file: Annotated[FilePath, BeforeValidator(coerce_path)]
    """Path to the default font file for this card type"""

    font_color: str
    """Default color for title text"""

    font_case: TextCase = 'upper'
    """Default text case transformation for title text"""

    font_replacements: dict[str, str] = {}
    """Character replacements to apply to text (e.g., Unicode → ASCII)"""

    title_max_line_width: Annotated[int, Field(ge=1)]
    """Maximum number of characters on one line of title text"""

    title_max_line_count: Annotated[int, Field(ge=1)]
    """Maximum number of lines a title can take up"""

    title_split_style: SplitStyle
    """How to dynamically split title text into multiple lines"""

    episode_text_format: str = 'Episode {episode_number}'
    """How to format episode text"""

    uses_source_images: bool = True
    """Whether this card type requires source images for card creation"""


class BaseCardType(ImageMaker, ABC):
    """
    This class describes an abstract card type. A BaseCardType is a
    subclass of ImageMaker, because all CardTypes are designed to create
    title cards. This class outlines the requirements for creating a
    custom type of title card.

    All implementations of BaseCardType must implement this class's
    abstract properties and methods in order to work with TCM.
    """

    CardConfig: Annotated[
        DefaultCardConfig,
        'Default card configuration class for this card type'
    ]

    """Mapping of 'case' strings to format functions"""
    CASE_FUNCTIONS: ClassVar[dict[TextCase, Callable[[Any], str]]] = {
        'blank': lambda _: '',
        'lower': str.lower,
        'source': str,
        'title': titlecase,
        'upper': str.upper,
    }

    """Standard size for all title cards"""
    WIDTH: ClassVar[int] = 3200
    HEIGHT: ClassVar[int] = 1800
    TITLE_CARD_SIZE: ClassVar[str] = f'{WIDTH}x{HEIGHT}'

    BLUR_PROFILE: Annotated[
        ClassVar[str],
        'Default blur effect to apply to blurred images'
    ] = '0x60'

    API_DETAILS: Annotated[
        ClassVar[CardTypeDescription],
        'Front-end description of this card type and its customization'
    ]

    __slots__ = ('valid', 'blur', 'grayscale')


    @abstractmethod
    def __init__(self,
            blur: bool = False,
            grayscale: bool = False,
            **unused: Any,
        ) -> None:
        """
        Construct a new CardType. Must call super().__init__() to
        initialize the parent ImageMaker class (for ImageMagickInterface
        objects).

        Args:
            blur: Whether to blur the source image. Defaults to False.
            grayscale: Whether to convert the source image to grayscale.
                Defaults to False.
        """

        # Initialize parent ImageMaker
        super().__init__()

        self.valid = True

        self.blur = blur
        self.grayscale = grayscale


    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Initialize the subclass CardType. After initialization, this
        performs basic validations on the class for required
        implementations. This is done on the class itself, not an
        instance of the class.
        """

        super().__init_subclass__(**kwargs)
        ClsName = cls.__name__

        if not isinstance(cls.API_DETAILS, CardTypeDescription):
            raise TypeError(
                f'{ClsName}.API_DETAILS must be a CardTypeDescription '
                f'object'
            )

        if not hasattr(cls, 'CardConfig'):
            raise TypeError(f'{ClsName} must define a CardConfig class')

        if not isinstance(cls.CardConfig, DefaultCardConfig):
            raise TypeError(
                f'{ClsName}.CardConfig must be a DefaultCardConfig object'
            )

        # Register card type descriptions and blur profiles into global lists
        from app.core.card_registry import (
            CARD_CLASSES, DEFAULT_BLUR_PROFILES, LocalCards
        )
        DEFAULT_BLUR_PROFILES[cls.API_DETAILS.identifier] = cls.BLUR_PROFILE
        CARD_CLASSES[cls.API_DETAILS.identifier] = cls
        if cls.API_DETAILS.source == 'builtin':
            LocalCards.append(cls.API_DETAILS)


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        attributes = ', '.join(
            f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__
            if not attr.startswith('__')
        )

        return f'<{self.__class__.__name__} {attributes}>'


    @staticmethod
    def enrich_card_data(
            series_info: 'SeriesInfo',
            episode_info: 'EpisodeInfo',
            **kwargs: Any,
        ) -> dict[str, Any]:
        """
        Optional hook to fetch additional data before setting
        resolution. This method can be overridden by card types to query
        external APIs (like TMDb) and add custom data that will be
        available during settings resolution and format string
        evaluation.

        Args:
            series_info: SeriesInfo for the series being processed.
            episode_info: EpisodeInfo for the episode being processed.
            kwargs: Additional optional parameters.

        Returns:
            Dictionary of additional data to merge into card_settings.
            This data will be available for use in format strings and
            settings resolution. Returns an empty dictionary by default.
        """

        return {}


    @staticmethod
    def resolve_format_strings(data: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve any class-specific format strings. If a subclass does
        not implement this, the data is returned unmodified.
        """

        return data


    @staticmethod
    def get_title_split_characteristics(
            max_line_width: int,
            max_line_count: int,
            split_style: SplitStyle,
            default_font_file: str | Path,
            data: dict,
        ) -> tuple[int, int, SplitStyle]:
        """
        Get the title split characteristics for the card defined by the
        given card data. By default this modifies the max line width
        by the `font_size` (if the default Font is used), and adds the
        `font_line_split_modifier` (if specified).

        Args:
            max_line_width: Maximum width of one line of title text,
                in characters.
            max_line_count: Maximum number of lines a title can take up,
                in total.
            split_style: How to split the title into multiple lines.
            default_font_file: Default font file for size evaluation.
            data: Card data to evaluate for any changes to the split
                characteristics.

        Returns:
            Tuple of the new max line width, max line count, and split
            style.
        """

        if ('font_size' in data
            and 'font_file' in data
            and data['font_file'] == str(default_font_file)
        ):
            max_line_width = int(max_line_width / float(data['font_size']))

        if 'font_line_split_modifier' in data:
            max_line_width += int(data['font_line_split_modifier'])

        return max_line_width, max_line_count, split_style


    @property
    def resize(self) -> ImageMagickCommands:
        """
        ImageMagick commands to only resize an image to the output title
        card size.
        """

        return [
            # Use 4:4:4 sampling by default
            f'-sampling-factor 4:4:4',
            # Full sRGB colorspace on source image
            f'-set colorspace sRGB',
            # Ignore profile conversion warnings
            f'+profile "*"',
            # Background resize shouldn't fill with any color
            f'-background transparent',
            f'-gravity center',
            # Fit to title card size
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
        ]


    @property
    def style(self) -> ImageMagickCommands:
        """
        ImageMagick commands to apply any style modifiers to an image.
        """

        return [
            # Use 4:4:4 sampling by default
            f'-sampling-factor 4:4:4',
            # Full sRGB colorspace on source image
            f'-set colorspace sRGB',
            # Ignore profile conversion warnings
            f'+profile "*"',
            # Optionally blur
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            # Optionally set gray colorspace
            f'-colorspace gray' if self.grayscale else '',
            # Reset to full colorspace
            f'-set colorspace sRGB' if self.grayscale else '',
        ]


    @property
    def resize_and_style(self) -> ImageMagickCommands:
        """
        ImageMagick commands to resize and apply any style modifiers to
        an image.
        """

        return [
            # Use 4:4:4 sampling by default
            f'-sampling-factor 4:4:4',
            # Full sRGB colorspace on source image
            f'-set colorspace sRGB',
            # Ignore profile conversion warnings
            f'+profile "*"',
            # Background resize shouldn't fill with any color
            f'-background transparent',
            f'-gravity center',
            # Fit to title card size
            f'-resize "{self.TITLE_CARD_SIZE}^"',
            f'-extent "{self.TITLE_CARD_SIZE}"',
            # Optionally blur
            f'-blur {self.BLUR_PROFILE}' if self.blur else '',
            # Optionally set gray colorspace
            f'-colorspace gray' if self.grayscale else '',
            # Reset to full colorspace
            f'-set colorspace sRGB',
        ]


    def add_overlay_mask(self,
            file: Path,
            /,
            *,
            pre_processing: ImageMagickCommands | None = None,
            x: int = 0,
            y: int = 0,
        ) -> ImageMagickCommands:
        """
        ImageMagick commands to add a top-level mask to the image.
        
        Args:
            file: Path to the file to search for the mask image
                alongside.
            pre_processing: Any ImageMagick commands to apply to the
                mask before it is overlaid.
            x: Offset X-coordinate to use when compositing the mask.
            y: Offset Y-coordinate to use when compositing the mask.

        Returns:
            List of ImageMagick commands.
        """

        # Do not apply any masks for stylized cards
        if self.blur or self.grayscale:
            return []

        # Look for mask file corresponding to this source image
        # Prioritize episode-specific mask, then general mask
        if ((mask := list(file.parent.glob(f'{file.stem}-mask.*')))
            or (mask := list(file.parent.glob(f'{file.stem}_mask.*')))
            or (mask := list(file.parent.glob(f'mask.*')))):
            mask = mask[0]
        else:
            return []

        log.trace(f'Identified mask image "{mask.resolve()}"')
        if pre_processing is None:
            pre_processing = self.resize_and_style

        return [
            fr'\(',
                f'"{mask.resolve()}"',
                *self.resize,
                *pre_processing,
            fr'\)',
            f'-geometry {x:+}{y:+}',
            fr'-composite',
        ]


    @property
    def resize_output(self) -> ImageMagickCommands:
        """
        ImageMagick commands to resize the card to the global card
        dimensions.
        """

        return [
            f'-sampling-factor 4:4:4',
            f'-set colorspace sRGB',
            f'+profile "*"',
            f'-background transparent',
            f'-gravity center',
            f'-resize "{self.card_dimensions}"',
            f'-extent "{self.card_dimensions}"',
            f'-quality {self.quality}',
        ]


    def add_drop_shadow(self,
            commands: ImageMagickCommands,
            shadow: str | Shadow,
            x: int | float = 0,
            y: int | float = 0,
            *,
            shadow_color: str = 'black',
            compose: bool = True,
        ) -> ImageMagickCommands:
        """
        Amend the given commands to apply a drop shadow effect. See
        https://imagemagick.org/script/command-line-options.php?#shadow
        for details on the shadow string.

        Args:
            commands: List of commands being modified. Must contain some
                image definition that can be cloned.
            shadow: IM Shadow string (e.g `85x10+10+10`), or Shadow
                object.
            x: X-position of the offset to apply when compositing if
                `compose` is `True`.
            y: Y-position of the offset to apply when compositing if
                `compose` is `True`.
            shadow_color: Color of the shadow to add.
            compose: Whether to include composition in the returned
                commands.

        Returns:
            List of ImageMagick commands.
        """

        if not commands:
            return []

        compose_commands = []
        if compose:
            compose_commands = [
                fr'-geometry {x:+.0f}{y:+.0f}',
                fr'-composite',
            ]

        return [
            fr'\(',
                *commands,
                fr'\(',
                    f'+clone',
                    f'-background "{shadow_color}"',
                    f'-shadow {shadow}',
                fr'\)',
                f'+swap',
                f'-background None',
                f'-layers merge',
                f'+repage',
            fr'\)',
            *compose_commands,
        ]


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method to create the title card outlined by the
        CardType. All implementations of this method should delete any
        intermediate files.
        """
        raise NotImplementedError


def get_extra_validation_error(
        title: str,
        error_name: str,
        error_template: str,
        error_context: dict[str, Any],
        error_location: str,
        input: Any,
    ) -> ValidationError:
    """
    Construct a ValidationError with a custom error type and message.
    This allows for the custom error to appear like a built-in Pydantic
    schema validation error.

    >>> raise get_extra_validation_error(
    ...     title='Cascade Transparency sequence is invalid',
    ...     error_name='bad_sequence',
    ...     error_template='Transparency sequence is invalid: {exc}}',
    ...     error_context={'exc': str(exc)},
    ...     error_location='cascase_transparencies',
    ...     input=self.cascade_alphas,
    ... )

    Returns:
        ValidationError with a custom error type and message.
        This needs to be raised..
    """

    return ValidationError.from_exception_data(
        title=title,
        line_errors=[
            InitErrorDetails(
                type=PydanticCustomError(
                    error_name, # type: ignore
                    error_template, # type: ignore
                    error_context,
                ),
                loc=(error_location, ),
                input=input,
                ctx={},
            ),
        ]
    )


class PreviewCard(BaseModel):
    filename: str
    variables: dict[str, Any]

class CardDocumentation(BaseModel):
    static_variables: dict[str, Any]
    cards: list[PreviewCard] = []
    extension: str = '.webp'

def add_cli(
        dname: str,
        /,
        card_type: type[BaseCardType],
        validator_model: type[BaseCardModel],
        *,
        documentation: CardDocumentation | None = None,
    ) -> None:
    """
    Add CLI functionality for the given card type.

    Args:
        dname: Name of the module to run the card creation from - this
            should be provided via `__name__`.
        card_type: Card type whose `__init__()` and `create()` methods
            will be called during card creation.
        validator_model: Pydantic model to use for validation of the
            card creation arguments.
        documentation: Definition of how to create card documentation
            assets for this card. If provided, a `docs` command will be
            added.
    """

    if dname != '__main__':
        return None

    import click

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.argument('args', nargs=-1)
    def card(args: list[str]) -> None:
        """
        Create a card from the given arguments.

        Example:
            python app.py card --season-text input.jpg --output output.jpg
        """

        def to_key(val: str, /) -> str:
            return val.lstrip('-').replace('-', '_')

        params: dict[str, Any] = {
            to_key(args[i]): args[i + 1] if i + 1 < len(args) else None
            for i in range(0, len(args), 2)
        }

        card_maker = card_type(**validator_model(**params).model_dump())
        card_maker.create()
        card_maker.image_magick.print_command_history()


    @click.option(
        '--source', '-s', 'source_file',
        required=True,
        type=click.Path(exists=True),
        help='Path to the source image to use for the documentation cards',
    )
    @click.option(
        '--output', '-o', 'output_dir',
        required=True,
        type=click.Path(file_okay=False),
        help='Output directory to save the documentation cards',
    )
    @click.option('--logo-file', '-l', 'logo_file',
        required=False,
        type=click.Path(exists=True),
        help='Path to the logo file to use for the documentation cards',
    )
    @click.option(
        '--debug', '-d', 'debug',
        is_flag=True,
        help='Enable debug mode',
    )
    def docs(
            source_file: Path,
            output_dir: Path,
            logo_file: Path | None = None,
            debug: bool = False,
        ) -> None:
        """
        Create the documentation preview images.
        Example:
            python app.py docs -s input.jpg -o ./out
        """

        if documentation is None:
            return None

        (output_dir := Path(output_dir)).mkdir(parents=True, exist_ok=True)
        for preview_card in documentation.cards:
            # Combine static variables with preview card variables
            kwargs = documentation.static_variables | preview_card.variables
            kwargs['source_file'] = source_file
            kwargs['card_file'] = (
                output_dir / preview_card.filename
            ).with_suffix(documentation.extension)
            if logo_file is not None:
                kwargs['logo_file'] = logo_file

            # Create card
            card_maker = card_type(**validator_model(**kwargs).model_dump())
            card_maker.create()
            log.info(f'Created "{kwargs["card_file"].relative_to(output_dir)}"')

            if debug:
                log.debug(f'{kwargs = !r}')
                card_maker.image_magick.print_command_history()

    if documentation is not None:
        cli.add_command(cli.command(docs))

    cli()


__all__ = [
    'BaseCardType',
    'CardDescription',
    'CardTypeDescription',
    'Coordinate',
    'Dimensions',
    'Extra',
    'ImageMagickCommands',
    'ImageMaker',
    'ImageStack',
    'Rectangle',
    'TextCase',
]
