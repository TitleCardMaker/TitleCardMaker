from datetime import datetime
from os import environ
from pathlib import Path
from pickle import dump, load
from typing import Any, TYPE_CHECKING, Literal

from app.info.episode import EpisodeInfo
from app.interfaces.magick import ImageMagickInterface
from app.logging.logger import log, Logger
from app.settings import BACKEND_ROOT, CONFIG_ROOT, TCM_ROOT, settings
from modules.BaseCardType import BaseCardType
from modules.FormatString import FormatString
from modules.RemoteCardType2 import RemoteCardType
from modules.TitleCard import TitleCard
from modules.Version import Version

if TYPE_CHECKING:
    from app.schemas.preferences import CardExtension


class Preferences:
    """Class defining global Preferences."""

    """Path to the version file for the Web UI"""
    VERSION_FILE = BACKEND_ROOT / 'modules' / 'ref' / 'version_webui'

    """Default values for global settings"""
    DEFAULT_CARD_FILENAME_FORMAT = (
        '{series_full_name} - S{season_number:02}E{episode_number:02}'
    )
    DEFAULT_CARD_EXTENSION: 'CardExtension' = '.jpg'
    VALID_IMAGE_EXTENSIONS = (
        '.avif', '.heic', '.jpg', '.jpeg', '.jxl', '.png', '.tiff', '.webp',
    )

    """Directory to all internal assets"""
    INTERNAL_ASSET_DIRECTORY = TCM_ROOT / 'frontend' / 'public'

    """Directory for all temporary file operations"""
    TEMPORARY_DIRECTORY = BACKEND_ROOT / 'modules' / '.objects'

    """All environment variables which might be applicable to TCM, for boot"""
    __ENVIRONMENT_VARIABLES = (
        'TCM_BACKUP_RETENTION',
        'TCM_CARD_TYPE_URL',
        'TCM_DISABLE_AUTH',
        'TCM_IS_DOCKER',
        'TCM_IM_DOCKER',
        'TCM_LOG_STDOUT',
        'TCM_LOG_FILE',
        'TCM_LOG_RETENTION',
        'TCM_LOG_WEBSOCKET',
        'TZ',
    )

    """Attributes whose values should be ignored when loading from file"""
    __read_only = (
        'is_docker', 'file', 'asset_directory', 'card_type_directory',
        'remote_card_types', 'local_card_types', 'invalid_connections',
        'currently_running_sync', 'current_db_schema', 'current_version',
        'server_boot_time', 'libraries',
    )

    __slots__ = (
        'is_docker',
        'card_directory',
        'source_directory',
        'completely_delete_series',
        'file',
        'card_filename_format',
        'card_extension',
        'image_source_priority',
        'specials_folder_format',
        'season_folder_format',
        'remote_card_types',
        'use_emby',
        'use_jellyfin',
        'use_plex',
        'use_sonarr',
        'use_tmdb',
        'use_tvdb',
        'use_magick_prefix',
        'advanced_scheduling',
        'asset_directory',
        'available_version',
        'blacklisted_blueprints',
        'card_height',
        'card_quality',
        'card_type_directory',
        'colorblind_mode',
        'current_db_schema',
        'current_version',
        'card_width',
        'currently_running_sync',
        'default_blur_profiles',
        'default_card_type',
        'default_fonts',
        'default_templates',
        'default_unwatched_style',
        'default_watched_style',
        'delete_missing_episodes',
        'delete_unsynced_series',
        'display_live_messages',
        'episode_data_page_size',
        'episode_data_source',
        'excluded_card_types',
        'global_extras',
        'home_page_size',
        'home_page_table_view',
        'imagemagick_executable',
        'imported_blueprints',
        'interactive_card_previews',
        'invalid_connections',
        'local_card_types',
        'libraries',
        'library_unique_cards',
        'reduced_animations',
        'require_auth',
        'server_boot_time',
        'simplified_data_table',
        'stylize_unmonitored_posters',
        'sync_specials',
        'source_preview_page_dimensions',
        'task_crontabs',
        'title_card_preview_page_dimensions',
    )


    def __init__(self, file: Path) -> None:
        """
        Initialize this object with the arguments from the given file.

        Args:
            file: Path to the file to parse for existing preferences.
        """

        # Set initial values
        self.is_docker = settings.IS_DOCKER
        self.__initialize_defaults()

        # Get preferences from file
        self.file = file
        self.file.parent.mkdir(exist_ok=True)

        # Parse file
        self.parse_file(self.read_file())
        self.server_boot_time = datetime.now(tz=settings.TIMEZONE)

        # Initialize paths
        self.asset_directory: Path = Path(self.asset_directory)
        self.card_directory: Path = Path(self.card_directory)
        self.card_type_directory = Path(self.card_type_directory)
        self.source_directory = Path(self.source_directory)
        for folder in (
            self.asset_directory,
            self.card_directory,
            self.source_directory
        ):
            try:
                folder.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                log.critical(
                    f'Could not initialize directory "{folder}" - invalid '
                    f'permissions'
                )

        # Parse local card type files
        self.parse_local_card_types()

        # Convert Blueprint blacklist
        if (self.blacklisted_blueprints
            and any(isinstance(_, tuple) for _ in self.blacklisted_blueprints)):
            self.blacklisted_blueprints: set[int] = set()


    def __getstate__(self) -> dict[str, Any]:
        """
        Get the state definition of this object for pickling. This
        is all attributes except `remote_card_types`.

        Returns:
            Dictionary representation of this object with any un-
            pickleable attributes excluded.
        """

        # Exclude the card types dictionaries because the types might
        # not be loaded at runtime; which could cause an error when
        # unpickling
        return {
            attr: getattr(self, attr)
            for attr in self.__slots__
            if attr not in self.__read_only
        }


    def __setstate__(self, state: dict[str, Any]) -> None:
        """
        Set the state of this object from the pickled representation.

        Args:
            state: Dictionary representation of the object.
        """

        for attr, value in state.items():
            try:
                setattr(self, attr, value)
            except AttributeError:
                pass


    def __initialize_defaults(self) -> None:
        """Initialize this object with all default values."""

        if self.is_docker:
            self.asset_directory: Path = Path('/config/assets')
            self.card_directory: Path = Path('/config/cards')
            self.card_type_directory: Path = Path('/config/card_types')
            self.source_directory: Path = Path('/config/source')
        else:
            self.asset_directory: Path = CONFIG_ROOT / 'assets'
            self.card_directory: Path = CONFIG_ROOT / 'cards'
            self.card_type_directory: Path = CONFIG_ROOT / 'card_types'
            self.source_directory: Path = CONFIG_ROOT / 'source'

        self.card_width = TitleCard.DEFAULT_WIDTH
        self.card_height = TitleCard.DEFAULT_HEIGHT
        self.card_filename_format = self.DEFAULT_CARD_FILENAME_FORMAT
        self.library_unique_cards = False
        self.card_extension = self.DEFAULT_CARD_EXTENSION

        self.card_quality = ImageMagickInterface.DEFAULT_CARD_QUALITY
        if (_path := environ.get('TCM_IM_PATH', None)):
            self.imagemagick_executable: Path | None = Path(_path)
        else:
            self.imagemagick_executable: Path | None = None

        self.image_source_priority: list[int] = []
        self.episode_data_source: int | None = None

        self.specials_folder_format = 'Specials'
        self.season_folder_format = 'Season {season_number}'

        self.completely_delete_series = False
        self.sync_specials = True
        self.delete_missing_episodes = True
        self.delete_unsynced_series = False
        self.simplified_data_table = True
        self.interactive_card_previews = True
        self.remote_card_types: dict[str, type[BaseCardType]] = {}
        self.local_card_types: dict[str, type[BaseCardType]] = {}
        self.default_card_type = 'standard'
        self.excluded_card_types = []
        self.default_watched_style = 'unique'
        self.default_unwatched_style = 'unique'
        self.default_templates: list[int] = []
        self.default_fonts: dict[str, int] = {}
        self.default_blur_profiles: dict[str, str] = {}
        self.global_extras: dict[str, dict[str, str]] = {}

        self.currently_running_sync: int | None = None
        self.invalid_connections: list[int] = []
        self.use_emby = False
        self.use_jellyfin = False
        self.use_plex = False
        self.use_sonarr = False
        self.use_tmdb = False
        self.use_tvdb = False
        self.libraries: dict[
            int,
            tuple[Literal['Emby', 'Jellyfin', 'Plex'], list[str]]
        ] = {}

        self.use_magick_prefix = False
        self.blacklisted_blueprints: set[int] = set()
        self.imported_blueprints: set[int] = set()
        self.advanced_scheduling = False
        self.task_crontabs: dict[str, str] = {}

        self.require_auth = False
        self.home_page_size = 100
        self.episode_data_page_size = 50
        self.source_preview_page_dimensions = '3x3'
        self.title_card_preview_page_dimensions = '3x3'
        self.stylize_unmonitored_posters = False
        self.home_page_table_view = True
        self.colorblind_mode = False
        self.reduced_animations = False
        self.display_live_messages = True


    def log_startup(self, *, log: Logger = log) -> None:
        """
        Log the startup details of TCM. This is just a "starting"
        message and all relevant environment variables.

        Args:
            log: Logger for all log messages.
        """

        log.info(f'Starting TitleCardMaker ({self.current_version})')

        log.debug(f'{"-" * 15} Environment Variables {"-" * 15}')
        padding = max(map(len, self.__ENVIRONMENT_VARIABLES))
        for var_name in self.__ENVIRONMENT_VARIABLES:
            var = environ.get(var_name, '[Unspecified]')
            log.debug(f'  {var_name:>{padding}} : {var}')
        log.debug(f'{"-" * 53}')

        self.determine_imagemagick_prefix(log=log)


    def read_file(self) -> object | None:
        """
        Read this object's file, returning the loaded object.

        Returns:
            Object unpickled (loaded) from this object's file. None if
            the file does not exist or cannot be unpickled.
        """

        # Skip if file DNE
        if not self.file.exists():
            log.error(f'Preference file "{self.file.resolve()}" does not exist')
            return None

        # Parse file
        try:
            with self.file.open('rb') as file_handle:
                return load(file_handle)
        except Exception:
            log.exception('Error occured while loading Preferences')

        return None


    def parse_file(self, obj: object) -> None:
        """
        Initialize this object with the defaults for each attribute.
        """

        # Update each attribute known to this object
        for attribute in self.__slots__:
            if hasattr(obj, attribute) and attribute not in self.__read_only:
                setattr(self, attribute, getattr(obj, attribute))

        # Set attributes not parsed from the object
        self.current_version = Version(self.VERSION_FILE.read_text().strip())
        self.available_version: Version | None = None
        self.current_db_schema: str | None = None

        # Write object to file
        self.commit()


    def commit(self) -> None:
        """Commit any changes to this object to file."""

        # Open the file, dump this object's contents
        with self.file.open('wb') as file_handle:
            dump(self, file_handle)


    def update_values(self,
            *,
            log: Logger = log,
            **update_kwargs: Any,
        ) -> None:
        """
        Update multiple values at once, and commit the changes
        afterwards.

        Args:
            log: Logger for all log messages.
            update_kwargs: Dictionary of values to update.
        """

        # Iterate through updated attributes, set dictionary directly
        for name, value in update_kwargs.items():
            if value != '_UnspecifiedValue' and value != getattr(self, name, '*'):
                setattr(self, name, value)
                log.debug(f'Preferences.{name} = {value}')

        # Commit changes
        self.commit()


    def reset(self, *, log: Logger = log) -> None:
        """
        Reset all global preferences to their defaults.

        Args:
            log: Logger for all log messages.
        """

        self.__initialize_defaults()
        self.commit()
        log.info('Reset global preferences to defaults')


    def determine_imagemagick_prefix(self,
            *,
            log: Logger = log,
        ) -> None:
        """
        Determine whether to use the "magick " prefix for ImageMagick
        commands.

        Args:
            log: Logger for all log messages.
        """

        # Do not need to determine in Docker; always omit prefix
        if self.is_docker:
            self.use_magick_prefix = False
            return None

        # Try to initialize with/out the "magick " prefix
        for prefix, use_magick in (('magick', True), ('', False)):
            # Create ImageMagickInterface and verify validity
            interface = ImageMagickInterface(use_magick_prefix=use_magick)
            if interface.validate_interface():
                # Since cards are typically created in the background
                # thread; assign prefix only for threaded eval
                self.use_magick_prefix = use_magick
                log.debug(
                    f'Using "{prefix}" ImageMagick command prefix in '
                    + ('the primary thread' if use_magick else 'all threads')
                )
                return None
            interface.print_command_history(log=log)

        # If neither variation worked, IM might not be installed
        log.critical("ImageMagick doesn't appear to be installed")
        return None


    def parse_local_card_types(self, *, log: Logger = log) -> None:
        """
        Parse all locally specified CardType Python files. This attempts
        to load each `.py` file in the card type directory as a
        `RemoteCardType` object, and then stores the resulting
        identifier and class in the local card types map.

        Args:
            log: Logger for all log messages.
        """

        # Parse all Python files in the card type directory
        for file in self.card_type_directory.glob('*.py'):
            # Attempt to load each file; skip if invalid
            if not (card_type := RemoteCardType(file, log=log)).valid:
                log.critical('Error reading local CardType')
                continue

            # Card type parsed, add to dictionary of identifiers to classes
            if not card_type.card_class:
                continue
            details = card_type.card_class.API_DETAILS
            self.local_card_types[details.identifier] = card_type.card_class
            log.debug(f'Parsed local CardType[{details.identifier}]')


    @property
    def card_properties(self) -> dict[str, str]:
        """Properties to utilize and merge in Title Card creation."""

        return {
            'card_type': self.default_card_type,
            'watched_style': self.default_watched_style,
            'unwatched_style': self.default_unwatched_style,
            'card_filename_format': self.card_filename_format,
        }


    @property
    def export_properties(self) -> dict[str, str]:
        """Dictionary of the properties to be exported in Blueprints."""

        return {
            'card_type': self.default_card_type,
        }


    @property
    def card_dimensions(self) -> str:
        """Card dimensions as a formatted dimensional string."""

        return f'{self.card_width}x{self.card_height}'


    @staticmethod
    def get_filesize(
            value: int | None,
            unit: str | None
        ) -> int | None:
        """
        Get the filesize for the given value and unit.

        Args:
            value: Value of the filesize limit.
            unit: Unit of the filesize limit.

        Returns:
            The integer value of the filesize equivalent of the given
            arguments (in Bytes). None if value or unit is None.
        """

        # If either value is None, return that
        if value is None or unit is None:
            return None

        return value * {
            'b':  1,         'bytes': 1,
            'kb': 2**10, 'kilobytes': 2**10,
            'mb': 2**20, 'megabytes': 2**20,
            'gb': 2**30, 'gigabytes': 2**30,
            'tb': 2**40, 'terabytes': 2**40,
        }[unit.lower()]


    @staticmethod
    def format_filesize(value: int | None) -> tuple[str, str]:
        """
        Format the given filesize limit into a tuple of filesize value
        and units. Formatted as the highest >1 unit value.

        Args:
            value: Integer value of the filesize (in Bytes).

        Returns:
            Tuple of the string equivalent of the filesize bytes and the
            corresponding unit.
        """

        if value is None or value == 0:
            return '0', 'Bytes'

        for ref_value, unit in (
            (10**12, 'Terabytes'),
            (10**9,  'Gigabytes'),
            (10**6,  'Megabytes'),
            (10**3,  'Kilobytes'),
            (1,      'Bytes')
        ):
            if value > ref_value:
                return f'{value/ref_value:,.1f}', unit

        return '0', 'Bytes'


    @staticmethod
    def standardize_style(style: str) -> str:
        """
        Standardize the given style string so that style modifiers are
        not order dependent.

        For example, "blur unique" should standardize to the same value
        as "unique blur".

        Args:
            style: Style string being standardized.

        Returns:
            Standardized value. This is an alphabetically sorted space-
            separated lowercase variation of style. If the given style
            was just "blur", then "blur unique" is returned.
        """

        # Add "unique" if not in the style
        standardized = str(style).lower().strip()
        if 'art' not in standardized and 'unique' not in standardized:
            standardized += ' unique'

        # All other styles get typical standardization.
        return ' '.join(sorted(standardized.split(' ')))


    def get_folder_format(self, episode_info: EpisodeInfo) -> str:
        """
        Get the season folder name for the given Episode.

        Args:
            episode_info: EpisodeInfo of the Episode whose folder is
                being evaluated.

        Returns:
            Name of the season subfolder for the given Episode.
        """

        fstring = (
            self.specials_folder_format
            if episode_info.season_number == 0
            else self.season_folder_format
        )

        # Only return first 254 characters to handle the Windows path limit
        return FormatString(fstring, data=episode_info.indices).result[:254]


    def get_card_type_class(self,
            identifier: str,
            *,
            log: Logger = log,
        ) -> type[BaseCardType] | None:
        """
        Get the CardType class for the given card type identifier.

        Args:
            identifier: Identifier of the CardType class.
            log: Logger for all log messages.

        Returns:
            CardType subclass of the given identifier. None if this is
            an unknown identifier.
        """

        # Get the effective card class
        if identifier in TitleCard.CARD_TYPES:
            return TitleCard.CARD_TYPES[identifier]
        if identifier in self.remote_card_types:
            return self.remote_card_types[identifier]
        if identifier in self.local_card_types:
            return self.local_card_types[identifier]

        log.error(f'Unable to identify card type "{identifier}"')
        return None
