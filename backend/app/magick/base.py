from abc import ABC, abstractmethod
from pathlib import Path
from typing import Annotated, ClassVar

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


__all__ = [
    'Dimensions',
    'ImageMaker',
    'ImageMagickCommands',
]
