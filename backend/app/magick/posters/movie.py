from pathlib import Path

from pydantic import BaseModel, Field, FilePath

from app.magick.base import ImageMagickCommands, ImageMaker, add_poster_cli
from app.logging.logger import log
from app.schemas.base import Base, FontSize


class MoviePosterMaker(ImageMaker):
    """This class defines a type of maker that creates movie posters."""

    """Directory where all reference files used by this maker are stored"""
    REF_DIRECTORY = Path(__file__).parent / 'ref' / 'movie'

    """Base font for title text"""
    FONT = REF_DIRECTORY / 'Arial Bold.ttf'
    FONT_COLOR = 'white'
    INDEX_FONT_COLOR = 'rgb(154,154,154)'

    """Paths to reference images to overlay"""
    __FRAME = REF_DIRECTORY / 'frame.png'
    __GRADIENT = REF_DIRECTORY / 'gradient.png'


    def __init__(self,
            source: Path,
            output: Path,
            title: str,
            subtitle: str = '',
            top_subtitle: str = '',
            movie_index: str = '',
            logo: Path | None = None,
            font_file: Path = FONT,
            font_color: str = FONT_COLOR,
            font_size: float = 1.0,
            font_vertical_shift: int = 0,
            borderless: bool = False,
            add_drop_shadow: bool = False,
            omit_gradient: bool = False,
        ) -> None:
        """Construct a new instance of this object."""

        # Initialize parent object for the ImageMagickInterface
        super().__init__()

        # Store arguments as attributes
        self.source = source
        self.output = output
        self.movie_index = movie_index
        self.logo = logo
        self.font_file = font_file
        self.font_color = font_color
        self.font_size = font_size
        self.font_vertical_shift = font_vertical_shift
        self.borderless = borderless
        self.add_drop_shadow = add_drop_shadow
        self.omit_gradient = omit_gradient

        # Uppercase title(s) if using default font
        if font_file == self.FONT:
            self.top_subtitle = top_subtitle.upper().strip()
            self.title = title.upper().strip()
            self.subtitle = subtitle.upper().strip()
        else:
            self.top_subtitle = top_subtitle.strip()
            self.title = title.strip()
            self.subtitle = subtitle.strip()


    @property
    def gradient_command(self) -> ImageMagickCommands:
        """
        ImageMagick commands to add the gradient to the source image.
        """

        # If gradient is omitted, return empty command
        if self.omit_gradient:
            return []

        return [
            f'"{self.__GRADIENT.resolve()}"',
            f'-compose Multiply',
            f'-composite',
            f'-compose over',
        ]


    @property
    def index_command(self) -> ImageMagickCommands:
        """
        ImageMagick command(s) to add the underlying index text behind
        the title text.
        """

        # No index, return empty command
        if len(self.movie_index) == 0:
            return []

        return [
            f'-font "{self.FONT.resolve()}"',
            f'-pointsize 598',
            f'-fill "{self.INDEX_FONT_COLOR}"',
            f'-gravity center',
            f'-annotate +0+1150 "{self.movie_index}"',
        ]


    @property
    def title_font_attributes(self) -> ImageMagickCommands:
        """
        Imagemagick commands to define the font attributes of the title
        text.
        """

        title_font_size = 190 * self.font_size

        return [
            f'-pointsize {title_font_size}',
            f'-interline-spacing -44.5',
            f'-interword-spacing 55',
            f'-kerning 0.70',
        ]


    @property
    def subtitle_font_attributes(self) -> ImageMagickCommands:
        """
        Imagemagick commands to define the font attributes of the
        subtitle text.
        """

        subtitle_font_size = 95 * self.font_size

        return [
            f'-pointsize {subtitle_font_size}',
            f'-interword-spacing 18',
            f'-kerning 0.5',
        ]


    @property
    def logo_command(self) -> ImageMagickCommands:
        """
        ImageMagick subcommands to add the logo file to the poster.
        """

        # Logo not indicated, return empty command
        if self.logo is None:
            return []

        return [
            # Bring in logo image
            fr'\(',
                f'"{self.logo.resolve()}"',
                # Resize to 400px wide, limit to 200px tall
                f'-resize 400x',
                fr'-resize x200\>',
            fr'\)',
            # Overlay 100px from top of image
            f'-gravity north',
            f'-geometry +0+100',
            f'-composite',
        ]


    @property
    def title_command(self) -> ImageMagickCommands:
        """
        ImageGagick subcommands to add the title text to the poster.
        """

        # No titles, return empty command
        if not any(map(len, (self.top_subtitle, self.title, self.subtitle))):
            return []

        y_offset = 262.5
        if self.subtitle:
            y_offset = 182.5

        shadow_commands = []
        if self.add_drop_shadow:
            y_offset -= 15
            shadow_commands = [
                fr'\(',
                    f'+clone',
                    f'-background None',
                    f'-shadow 90x3+10+10',
                fr'\)',
                f'+swap',
                f'-background None',
                f'-layers merge',
                f'+repage',
            ]
        y_offset += self.font_vertical_shift

        # At least one title being added, return entire command
        return [
            ## Global font attributes
            f'-font "{self.font_file.resolve()}"',
            f'-fill "{self.font_color}"',
            # Create an image for each title
            fr'\(',
                fr'\(',
                    f'-background transparent',
                    *self.subtitle_font_attributes,
                    # Combine in order [TOP SUBTITLE] / [TITLE] / [SUBTITLE]
                    f'label:"{self.top_subtitle}"' if self.top_subtitle else '',
                    *self.title_font_attributes,
                    f'label:"{self.title}"' if self.title else '',
                    *self.subtitle_font_attributes,
                    f'label:"{self.subtitle}"' if self.subtitle else '',
                    # Merge images
                    f'-smush 30',
                fr'\)',
                # Add drop shadow to text
                *shadow_commands,
                # Add titles to image
            fr'\)',
            f'-gravity south',
            f'-geometry +0+{y_offset}',
            f'-composite',
        ]


    def create(self) -> None:
        """
        Create this object's poster. This WILL overwrite the existing
        file if it  already exists. Errors and returns if the source
        image does not exist.
        """

        # If the source file doesn't exist, exit
        if not self.source.exists():
            log.error((
                f'Cannot create movie poster - "{self.source.resolve()}" does '
                f'not exist.'
            ))
            return None
        if isinstance(self.logo, Path) and not self.logo.exists():
            log.error((
                f'Cannot create movie poster - "{self.logo.resolve()}" does '
                f'not exist.'
            ))
            return None

        # Command to create collection poster
        self.image_magick.run([
            f'convert',
            # Start with source
            f'"{self.source.resolve()}"',
            # Fit to size within frame
            f'-gravity center',
            f'-resize "1892x2892^"',
            f'-extent 1892x2892',
            # Optionally overlay gradient
            *self.gradient_command,
            # Add frame
            f'-background transparent',
            f'"{self.__FRAME.resolve()}"' if not self.borderless else '',
            f'-extent 2000x3000',
            f'-composite' if not self.borderless else '',
            # Optionally overlay logo
            *self.logo_command,
            # Add index text
            *self.index_command,
            # Add title text
            *self.title_command,
            # Crop to remove the empty frame space if borderless
            f'-gravity center -crop 1892x2892+0+0' if self.borderless else '',
            f'"{self.output.resolve()}"',
        ])

        return None


def get_validator_model() -> type[BaseModel]:
    """Get the Pydantic validator class for this poster type."""

    class PosterModel(Base):
        source: FilePath
        output: Path
        title: str
        subtitle: str = ''
        top_subtitle: str = ''
        movie_index: str = ''
        logo: Path | None = None
        font_file: FilePath = Field(default=MoviePosterMaker.FONT)
        font_color: str = MoviePosterMaker.FONT_COLOR
        font_size: FontSize = 1.0
        font_vertical_shift: int = 0
        borderless: bool = False
        add_drop_shadow: bool = False
        omit_gradient: bool = False

    return PosterModel


add_poster_cli(__name__, MoviePosterMaker, get_validator_model())
