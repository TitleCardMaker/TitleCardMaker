from pathlib import Path
from typing import TYPE_CHECKING

from app.logging.logger import log
from app.magick.base import BaseSummary

if TYPE_CHECKING:
    from modules.Show import Show


class StandardSummary(BaseSummary):
    """
    This class describes a show summary. The StandardSummary is a type
    of Summary object that displays (at most) a 3x3 grid of images, with
    a logo at the top.

    This type of Summary supports different background colors and
    images.
    """

    """Default color for the background of the summary image"""
    BACKGROUND_COLOR = '#1A1A1A'

    """Configurations for the header text"""
    HEADER_TEXT = 'EPISODE TITLE CARDS'
    HEADER_FONT = (
        BaseSummary.REF_DIRECTORY.parent
        / 'standard'
        / 'Proxima Nova Regular.otf'
    )
    HEADER_FONT_COLOR = '#CFCFCF'

    """Paths to intermediate images created by this object"""
    __MONTAGE_PATH = BaseSummary.TEMP_DIR / 'montage.png'
    __MONTAGE_WITH_HEADER_PATH = BaseSummary.TEMP_DIR / 'header.png'
    __RESIZED_LOGO_PATH = BaseSummary.TEMP_DIR / 'resized_logo.png'
    __LOGO_AND_HEADER_PATH = BaseSummary.TEMP_DIR / 'logo_and_header.png'
    __TRANSPARENT_MONTAGE = BaseSummary.TEMP_DIR / 'transparent_montage.png'

    __slots__ = ('background', '__background_is_image')


    def __init__(self,
            show: 'Show',
            background: str = BACKGROUND_COLOR,
            created_by: str | None = None,
        ) -> None:
        """
        Construct a new instance of this object.

        Args:
            show: The Show object to create the Summary for.
            background: Background color or image to use for the
                summary. Can also be a "format string" that is
                "{series_background}" to use the given Show object's
                backdrop.
            created_by: Optional string to use in custom "Created by .."
                tag at the botom of this Summary.
        """

        # Initialize parent Summary object
        super().__init__(show, created_by)

        # If background is default, use that
        if background == 'default':
            background = self.BACKGROUND_COLOR

        # Get global background color or image
        if isinstance(background, str):
            # Attempt to format as this series background ({series_background})
            try:
                background = background.format(series_background=show.backdrop)
            except Exception:
                pass

        # If a filepath that exists, use as image
        self.background: str | Path = background
        self.__background_is_image = False
        if Path(background).exists():
            self.background = Path(background)
            self.__background_is_image = True
            log.debug(
                f'Identified summary background image {self.background.resolve()}'
            )


    def _create_montage(self) -> Path:
        """
        Create a (max) 3x3 montage of input images.

        Returns:
            Path to the created image.
        """

        background = 'None' if self.__background_is_image else self.background

        self.image_magick.run([
            f'montage',
            f'-set colorspace sRGB',
            f'-background "{background}"',
            f'-density 300',
            f'-tile 3x3',
            f'-geometry +80+80',
            f'-shadow',
            f'"'+'" "'.join(self.inputs)+'"', # Wrap each filename in ""
            f'"{self.__MONTAGE_PATH.resolve()}"',
        ])

        return self.__MONTAGE_PATH


    def _add_header(self, montage: Path) -> Path:
        """
        Pad 80 pixels of blank space around the image, and add a header
        of text that says "EPISODE TITLE CARDS".

        Args:
            montage: The montage of images to add a header to.

        Returns:
            Path to the created image.
        """

        background = 'None' if self.__background_is_image else self.background

        self.image_magick.run([
            f'convert "{montage.resolve()}"',
            f'-resize 50%',
            f'-background "{background}"',
            f'-gravity north',
            f'-splice 0x840',
            f'-font "{self.HEADER_FONT.resolve()}"',
            f'-pointsize 100',
            f'-kerning 4.52',
            f'-fill black',
            f'-stroke black',
            f'-strokewidth 3',
            f'-annotate +0+700 "{self.HEADER_TEXT}"',
            f'-fill "{self.HEADER_FONT_COLOR}"',
            f'+stroke',
            f'-annotate +0+700 "{self.HEADER_TEXT}"',
            f'-gravity east',
            f'-splice 80x0',
            f'-gravity south',
            f'-splice 0x{80+int(80*self.number_rows/3)}',
            f'-gravity west',
            f'-splice 80x0',
            f'"{self.__MONTAGE_WITH_HEADER_PATH.resolve()}"'
        ])

        return self.__MONTAGE_WITH_HEADER_PATH


    def _resize_logo(self) -> Path:
        """
        Resize this associated show's logo to fit into at least a 500
        pixel high space. If the resulting logo is wider than 3400
        pixels, it is scaled.

        Returns:
            Path to the resized logo.
        """

        self.image_magick.run([
            f'convert',
            f'"{self.logo.resolve()}"',
            f'-resize x500',
            fr'-resize 3400x500\>',
            f'"{self.__RESIZED_LOGO_PATH.resolve()}"',
        ])

        return self.__RESIZED_LOGO_PATH


    def _add_logo(self, montage: Path, logo: Path) -> Path:
        """
        Add the logo to the top of the montage image.

        Args:
            montage: Path to the montage image to add the logo to.
            logo: Path to the logo image to add to the montage.

        Returns:
            Path to the created images.
        """

        _, height = self.image_magick.get_image_dimensions(logo)

        self.image_magick.run([
            f'composite',
            f'-gravity north',
            f'-geometry +0+{150+(500-height)//2}',
            f'"{logo.resolve()}"',
            f'"{montage.resolve()}"',
            f'"{self.__LOGO_AND_HEADER_PATH.resolve()}"'
        ])

        return self.__LOGO_AND_HEADER_PATH


    def _add_created_by(self,
            montage_and_logo: Path,
            created_by: Path,
        ) -> Path:
        """
        Add the 'created by' image to the bottom of the montage.

        Args:
            montage_and_logo: Path to the montage with the logo already
                applied.
            created_by: Path to the created by tag image.

        Returns:
            Path to the created (output) image.
        """

        y_offset = (self.number_rows == 2) * 35 + (self.number_rows == 1) * 15

        self.image_magick.run([
            f'composite',
            f'-gravity south',
            f'-geometry +0+{35+y_offset}',
            f'"{created_by.resolve()}"',
            f'"{montage_and_logo.resolve()}"',
            f'"{self.output.resolve()}"',
        ])

        return self.output


    def __add_background_image(self,
            montage_and_logo: Path,
            created_by: Path,
        ) -> Path:
        """
        Add the two images on top of the background image.

        Args:
            montage_and_logo: Path to the montage with the logo already
                applied.
            created_by: Path to the created by tag image.

        Returns:
            Path to the created (output) image.
        """

        # Create transparent montage
        y_offset = (self.number_rows == 2) * 35 + (self.number_rows == 1) * 15
        self.image_magick.run([
            f'composite',
            f'-gravity south',
            f'-geometry +0+{35+y_offset}',
            f'"{created_by.resolve()}"',
            f'"{montage_and_logo.resolve()}"',
            f'"{self.__TRANSPARENT_MONTAGE.resolve()}"',
        ])

        # Get dimensions of transparent montage to fit background
        width, height = self.image_magick.get_image_dimensions(
            self.__TRANSPARENT_MONTAGE
        )

        # Add background behind transparent montage
        self.image_magick.run([
            f'convert',
            f'"{self.background.resolve()}"',
            f'-gravity center',
            f'-resize "{width}x{height}"^',
            f'"{self.__TRANSPARENT_MONTAGE.resolve()}"',
            f'-composite',
            f'"{self.output.resolve()}"',
        ])

        return self.output


    def create(self) -> None:
        """
        Create the Summary defined by this object. Image selection is
        done at the start of this function.
        """

        # Exit if a logo does not exist
        if not self.logo.exists():
            log.warning('Cannot create Summary - no logo found')
            return None

        # Select images for montaging
        if not self._select_images(9) or len(self.inputs) == 0:
            return None

        # Create montage of title cards
        montage = self._create_montage()

        # Add header text and pad image with blank space
        montage_and_header = self._add_header(montage)

        # Resize show logo
        logo = self._resize_logo()

        # Add logo to the montage
        montage_and_logo = self._add_logo(montage_and_header, logo)

        # Create created by tag
        if self.created_by is None:
            created_by = self._CREATED_BY_PATH
        else:
            created_by = self._create_created_by(self.created_by)

        # Add created by and then optionally add background image
        if self.__background_is_image:
            self.__add_background_image(montage_and_logo, created_by)
        else:
            self._add_created_by(montage_and_logo, created_by)

        # Delete temporary files
        images = [montage, montage_and_header, logo, montage_and_logo]
        if self.created_by is not None:
            images.append(created_by)
        if self.__background_is_image:
            images.append(self.__TRANSPARENT_MONTAGE)

        self.image_magick.delete_intermediate_images(*images)
        return None


class StylizedSummary(BaseSummary):
    """
    This class describes a type of Summary image maker. This is a more
    stylized summary (compared to the StandardSummary) that uses a (max)
    4x3 grid of images, and creates a reflection of that grid. There is
    a logo at the top as well.

    This type of Summary does not support any background aside from
    black.
    """

    """Default (and only allowed) background color for this Summary"""
    BACKGROUND_COLOR = 'black'

    """Paths to intermediate images created by this object"""
    __MONTAGE_PATH = BaseSummary.TEMP_DIR / 'montage.png'
    __RESIZED_LOGO_PATH = BaseSummary.TEMP_DIR / 'resized_logo.png'


    def __init__(self,
            show: 'Show',
            background: str = BACKGROUND_COLOR, # pylint: disable=unused-argument
            created_by: str | None = None
        ) -> None:
        """
        Construct a new instance of this object.

        Args:
            show: Show object to create the Summary for.
            background: Background color or image to use for the
                summary. This is ignored and 'black' is always used.
            created_by: Optional string to use in custom "Created by .."
                tag at the botom of this Summary. Defaults to None.
        """

        # Initialize parent BaseSummary object
        super().__init__(show, created_by)


    def __create_montage(self) -> Path:
        """
        Create a montage of input images.

        Returns:
            Path to the created image.
        """

        self.image_magick.run([
            f'montage',
            f'-set colorspace sRGB',
            f'-background "{self.BACKGROUND_COLOR}"',
            f'-tile 3x{self.number_rows}',
            f'-geometry 800x450\>+5+5',
            f'"'+'" "'.join(self.inputs)+'"',
            f'"{self.__MONTAGE_PATH.resolve()}"',
        ])

        return self.__MONTAGE_PATH


    def __resize_logo(self, max_width: int | float) -> Path:
        """
        Resize this associated show's logo to fit into at least a 350
        pixel high space. If the resulting logo is wider than the given
        width, it is scaled.

        Returns:
            Path to the resized logo.
        """

        self.image_magick.run([
            f'convert',
            f'"{self.logo.resolve()}"',
            f'-resize x350',
            fr'-resize {max_width}x350\>',
            f'"{self.__RESIZED_LOGO_PATH.resolve()}"',
        ])

        return self.__RESIZED_LOGO_PATH


    def create(self) -> None:
        """
        Create the Summary defined by this object. Image selection is
        done at the start of this function.
        """

        # Exit if a logo does not exist
        if not self.logo.exists():
            log.warning('Cannot create Summary - no logo found')
            return None

        # Select images for montaging
        if not self._select_images(12) or len(self.inputs) == 0:
            return None

        # Create montage
        montage = self.__create_montage()

        # Get dimensions of montage
        width, height = self.image_magick.get_image_dimensions(montage)

        # Resize logo
        resized_logo = self.__resize_logo(width)

        # Get dimension of logo
        _, logo_height = self.image_magick.get_image_dimensions(resized_logo)

        # Get/create created by tag
        if self.created_by is None:
            created_by = self._CREATED_BY_PATH
        else:
            created_by = self._create_created_by(self.created_by)

        self.image_magick.run([
            f'convert "{montage.resolve()}"',
            # Create reflection of montage
            fr'\(',
            f'+clone',
            f'-flip',
            # Blur reflection
            f'-blur 0x8',
            # Darken reflection
            f'-fill black',
            f'-colorize 75%',
            fr'\)',
            f'-append',
            # Create colored background
            f'-size {width+200}x{height+700}',
            f'xc:"{self.BACKGROUND_COLOR}"',
            # Reverse reflection/montage(s)
            f'+swap',
            # Put montage+reflection on background
            f'-gravity north',
            f'-geometry +0+400',
            f'-composite',
            # Overlay created by image
            fr'\(',
            f'"{created_by.resolve()}"',
            f'-resize x75',
            # Create reflection of created by image
            fr'\(',
            f'+clone',
            f'-flip',
            f'-blur 0x2',
            # Darken reflection of created by image
            f'-fill black',
            f'-colorize 75%',
            fr'\)',
            f'-append',
            fr'\)',
            f'-gravity south',
            f'-geometry +0+50',
            f'-composite',
            # Overlay resized logo
            f'-gravity north',
            f'"{resized_logo.resolve()}"',
            f'-geometry +0+{400//2-logo_height//2}',
            f'-composite',
            f'"{self.output.resolve()}"',
        ])

        # Delete intermediate images
        if self.created_by is None:
            images = [montage]
        else:
            images = [montage, created_by]
        self.image_magick.delete_intermediate_images(*images)

        return None
