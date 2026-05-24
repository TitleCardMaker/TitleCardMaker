from abc import ABC, abstractmethod
from pathlib import Path
from typing import Annotated, Any, ClassVar

from pydantic import BaseModel

from app.interfaces.magick import Dimensions, ImageMagickInterface

type ImageMagickCommands = list[str]


def ImageStack(*commands: str) -> ImageMagickCommands:
    """
    Wrap a list of ImageMagick commands in parentheses.
    """

    return [fr'\(', *commands, fr'\)']


class ImageMaker(ABC):
    """
    Abstract class that outlines the necessary attributes for any class
    that creates images.

    All instances of this class must implement `create()` as the main
    callable function to produce an image. The specifics of how that
    image is created are completely customizable.
    """

    BASE_REF_DIRECTORY: Annotated[
        ClassVar[Path],
        'Base reference directory for local assets'
    ] = Path(__file__).parent.parent.parent / 'assets'

    """Directory for all temporary images created during image creation"""
    TEMP_DIR = Path(__file__).parent / '.objects'


    __slots__ = ('card_dimensions', 'quality', 'image_magick')


    @abstractmethod
    def __init__(self) -> None:
        """
        Initializes a new instance. This gives all subclasses access to
        an ImageMagickInterface via the image_magick attribute.
        """

        from app.settings import settings

        self.card_dimensions = settings.card_dimensions
        self.quality = settings.card_quality
        self.image_magick = ImageMagickInterface(
            container=settings.config.IMAGEMAGICK_CONTAINER,
            use_magick_prefix=settings.use_magick_prefix,
            executable=settings.imagemagick_executable,
            timeout=settings.config.IMAGEMAGICK_REQUEST_TIMEOUT,
        )


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method for the creation of the image outlined by this
        maker. This method should delete any intermediate files, and
        should make ImageMagick calls through the parent class'
        ImageMagickInterface object.
        """
        raise NotImplementedError('All ImageMaker objects must implement this')


def add_cli(
        dname: str,
        /,
        poster_type: type[ImageMaker],
        validator_model: type[BaseModel],
    ) -> None:
    """
    Add CLI functionality for the given poster type.

    Args:
        dname: Name of the module to run poster creation from - this
            should be provided via `__name__`.
        poster_type: Poster type whose `__init__()` and `create()`
            methods will be called during poster creation.
        validator_model: Pydantic model to use for validation of the
            poster creation arguments.
    """

    # Only add CLI functionality if not running as a module - i.e. the
    # poster file was run from the command line
    if dname != '__main__':
        return None

    import click

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.argument('args', nargs=-1)
    def create(args: list[str]) -> None:
        """
        Create a poster from the given arguments.

        Example:
            python genre.py poster input.jpg --genre Action --output output.jpg
        """

        def to_key(val: str, /) -> str:
            return val.lstrip('-').replace('-', '_')

        params: dict[str, Any] = {
            to_key(args[i]): args[i + 1] if i + 1 < len(args) else None
            for i in range(0, len(args), 2)
        }

        poster_maker = poster_type(**validator_model(**params).model_dump())
        poster_maker.create()
        poster_maker.image_magick.print_command_history()

    cli()


__all__ = [
    'Dimensions',
    'ImageMaker',
    'ImageMagickCommands',
    'add_cli',
]
