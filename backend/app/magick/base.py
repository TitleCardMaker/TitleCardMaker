from abc import ABC, abstractmethod
from math import ceil
from pathlib import Path
from random import sample
from typing import TYPE_CHECKING, Annotated

from app.interfaces.magick import Dimensions, ImageMagickInterface
from app.logging.logger import log
from modules import global_objects

if TYPE_CHECKING:
    from modules.preferences import Preferences
    from modules.Show import Show

type ImageMagickCommands = list[str]


class ImageMaker(ABC):
    """
    Abstract class that outlines the necessary attributes for any class
    that creates images.

    All instances of this class must implement `create()` as the main
    callable function to produce an image. The specifics of how that
    image is created are completely customizable.
    """

    BASE_REF_DIRECTORY: Annotated[
        Path,
        'Base reference directory for local assets'
    ] = Path(__file__).parent.parent.parent / 'assets'

    """Directory for all temporary images created during image creation"""
    TEMP_DIR = Path(__file__).parent / '.objects'

    """
    Valid file extensions for input images - ImageMagick supports more
    than just these types, but these are the most common across all
    OS's.
    """
    VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp')

    __slots__ = ('card_dimensions', 'quality', 'image_magick')


    @abstractmethod
    def __init__(self,
            *,
            preferences: 'Preferences | None' = None,
        ) -> None:
        """
        Initializes a new instance. This gives all subclasses access to
        an ImageMagickInterface via the image_magick attribute.

        Args:
            preferences: Global Preferences object to initialize the
                `ImageMagickInterface` with.
        """

        # No Preferences object, use global
        if preferences is None:
            self.card_dimensions = getattr(
                global_objects.pp, 'card_dimensions', '3200x1800'
            )
            self.quality = getattr(global_objects.pp, 'card_quality', 92)
            self.image_magick = ImageMagickInterface(
                getattr(global_objects.pp, 'imagemagick_container', 'ImageMagick'),
                getattr(global_objects.pp, 'use_magick_prefix', True),
                getattr(global_objects.pp, 'executable', None),
                getattr(global_objects.pp, 'imagemagick_timeout', 30),
            )
        # Preferences object provided, use directly
        else:
            self.card_dimensions = preferences.card_dimensions
            self.quality = preferences.card_quality
            self.image_magick = ImageMagickInterface(
                use_magick_prefix=preferences.use_magick_prefix,
                executable=preferences.imagemagick_executable,
            )


    @abstractmethod
    def create(self) -> None:
        """
        Abstract method for the creation of the image outlined by this
        maker. This method should delete any intermediate files, and
        should make ImageMagick calls through the parent class'
        ImageMagickInterface object.
        """
        raise NotImplementedError(f'All ImageMaker objects must implement this')


class BaseSummary(ImageMaker):
    """
    This class describes a type of ImageMaker that specializes in
    creating Show summaries. These are montage images that display a
    random selection of  title cards for a given Show object in order to
    give a quick visual indicator as to the style of the cards.

    This object cannot be instantiated directly, and only provides very
    few methods that can/should be used by all Summary subclasses.
    """
    show: 'Show'
    logo: Path
    created_by: str | None
    output: Path
    inputs: list[str]
    number_rows: int

    """Directory where all reference files are stored"""
    REF_DIRECTORY: Annotated[
        Path,
        'Directory where all reference files are stored'
    ] = ImageMaker.BASE_REF_DIRECTORY / 'summary'

    BACKGROUND_COLOR = '#1A1A1A'

    """
    Path to the 'created by' image to add to all show summaries. This
    was created with the "BasicSans-SemiBold" Font.
    """
    _CREATED_BY_PATH = REF_DIRECTORY / 'created_by_v2.png'

    """Configuration for the created by image creation"""
    HEADER_FONT = REF_DIRECTORY / 'standard' / 'Proxima Nova Regular.otf'
    __CREATED_BY_FONT = REF_DIRECTORY.parent / 'star_wars' / 'HelveticaNeue.ttc'
    __TCM_LOGO = REF_DIRECTORY / 'logo.png'
    __CREATED_BY_TEMPORARY_PATH = ImageMaker.TEMP_DIR / 'user_created_by.png'

    __slots__ = (
        'created_by',
        'inputs',
        'logo',
        'number_rows',
        'output',
        'show',
    )


    @abstractmethod
    def __init__(self,
            show: 'Show',
            created_by: str | None = None,
        ) -> None:
        """
        Initialize this object.

        Args:
            show: The Show object to create the Summary for.
            background: Background color or image to use for the
                summary. Can also be a "format string" that is
                "{series_background}" to use the given Show object's
                backdrop.
            created_by: Optional string to use in custom "Created by .."
                tag at the bottom of this Summary.
        """

        # Initialize parent ImageMaker
        super().__init__()

        # Store object attributes
        self.show = show
        self.logo = show.logo
        self.created_by = created_by

        # Summary output is just below show media directory
        self.output = show.media_directory / 'Summary.jpg'

        # Initialize variables that will be set upon image selection
        self.inputs = []
        self.number_rows = 0


    def _select_images(self, maximum_images: int = 9) -> bool:
        """
        Select the images that are to be incorporated into the show
        summary. This updates the object's inputs and number_rows
        attributes.

        Args:
            maximum_images: maximum number of images to select.

        Returns:
            Whether the ShowSummary should/can be created.
        """

        # Filter out episodes that don't have an existing title card
        available_episodes = list(filter(
            lambda e: (
                self.show.episodes[e].destination is not None
                and self.show.episodes[e].destination.exists() # type: ignore
            ),
            self.show.episodes
        ))

        # Filter specials if indicated
        if getattr(global_objects.pp, 'summary_ignore_specials', True):
            available_episodes = list(filter(
                lambda e: self.show.episodes[e].episode_info.season_number != 0,
                available_episodes
            ))

        # Warn if this show has no episodes to work with
        if (episode_count := len(available_episodes)) == 0:
            return False

        # Skip if the number of available episodes is below the minimum
        minimum = getattr(global_objects.pp, 'summary_minimum_episode_count', 6)
        if episode_count < minimum:
            log.debug(
                f'Skipping Summary, {self.show} has {episode_count} episodes, '
                f'minimum setting is {minimum}'
            )
            return False

        # Get a random subset of images to create the summary with
        # Sort that subset my season/episode number so the montage is ordered
        episode_keys = sorted(
            sample(available_episodes, min(episode_count, maximum_images)),
            key=lambda k: int(k.split('-')[0])*1000+int(k.split('-')[1])
        )

        # Get the full filepath for each of the selected images
        self.inputs = [
            str(self.show.episodes[e].destination.resolve())
            for e in episode_keys
        ]

        # The number of rows is necessary to determine how to scale y-values
        self.number_rows = ceil(len(episode_keys) / 3)

        return True


    def _create_created_by(self, created_by: str) -> Path:
        """
        Create a custom "Created by" tag image. This image is formatted
        like: "Created by {input} with {logo} TitleCardMaker". The image
        is exactly  the correct size (i.e. fit to width of text).

        Returns:
            Path to the created image.
        """

        self.image_magick.run([
            f'convert',
            # Create blank background
            f'-background transparent',
            # Create "Created by" image/text
            f'-font "{self.__CREATED_BY_FONT.resolve()}"',
            f'-pointsize 100',
            f'-fill "#CFCFCF"',
            f'label:"Created by"',
            # Create "{username}" image/text
            f'-fill "#DA7855"',
            f'label:"{created_by}"',
            # Create "with" image/text
            f'-fill "#CFCFCF"',
            f'label:"with"',
            # Resize TCM logo
            fr'\(',
            f'"{self.__TCM_LOGO.resolve()}"',
            f'-resize x100',
            fr'\)',
            # Create "TitleCardMaker" image/text
            f'-fill "#5493D7"',
            f'label:"TitleCardMaker"',
            # Combine all text images with 30px padding
            f'+smush 30',
            f'"{self.__CREATED_BY_TEMPORARY_PATH.resolve()}"'
        ])

        return self.__CREATED_BY_TEMPORARY_PATH
