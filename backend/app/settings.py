from datetime import datetime
from json import dump as json_dump, dumps as json_dumps, load as json_load
from pathlib import Path
from pickle import Unpickler
from typing import Annotated, Any, Literal

from app.core.config import AppConfig, config as app_config
from app.info.episode import EpisodeInfo
from app.interfaces.magick import ImageMagickInterface
from app.logging.logger import Logger, log
from app.schemas.preferences import CardExtension, Style
from app.cards.types import BUILTIN_CARD_TYPES
from app.cards.base import BaseCardType
from app.utils.fstring import FormatString
from app.cards.loader import RemoteCardType
from app.utils.serialization import SerializationExclusion, SerializationMixin


MediaSource = Literal['Emby', 'Jellyfin', 'Plex']

"""
Application root directories
"""
IS_DOCKER = app_config.IS_DOCKER
TCM_ROOT = Path(__file__).parent.parent.parent
BACKEND_ROOT = TCM_ROOT / 'backend'
FRONTEND_ROOT = TCM_ROOT / 'frontend'

CONFIG_ROOT = Path('/config') if IS_DOCKER else (TCM_ROOT / 'config')
LOG_ROOT = CONFIG_ROOT / 'logs'

# Logging levels
LogLevel = Literal['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class _DummyPreferences:
    """Dummy class for unpickling old preferences."""
    def __new__(cls, *args, **kwargs):
        # Avoid constructor call issues
        return object.__new__(cls)
    def __init__(self, *args, **kwargs):
        # Swallow all args
        pass
    def __setstate__(self, state):
        # Accept state from pickle
        self.__dict__.update(state)


class _PreferencesUnpickler(Unpickler):
    """
    Unpickler for the Preferences class. This is used to unpickle the
    Preferences class when the application is restarted.
    """

    def find_class(self, module: str, name: str) -> type:
        if module == 'pathlib' or name in ('PosixPath', 'WindowsPath'):
            return Path
        return _DummyPreferences


class Settings(SerializationMixin):
    """
    Unified settings class that combines application settings and user
    preferences.
    """

    config: SerializationExclusion[AppConfig] = app_config

    # Paths and directories
    _preferences_file: SerializationExclusion[Path | None] = None
    card_directory: Path = CONFIG_ROOT / 'cards'
    source_directory: Path = CONFIG_ROOT / 'source'
    asset_directory: SerializationExclusion[Path] = CONFIG_ROOT / 'assets'
    card_type_directory: SerializationExclusion[Path] = CONFIG_ROOT / 'card_types'
    backup_directory: SerializationExclusion[Path] = CONFIG_ROOT / 'backups'
    log_directory: SerializationExclusion[Path] = CONFIG_ROOT / 'logs'
    temporary_directory: SerializationExclusion[Path] = CONFIG_ROOT / '.objects'

    # Card properties
    card_width: int = 1920
    card_height: int = 1080
    card_quality: int = 95
    card_filename_format: str = (
        '{series_full_name} - S{season_number:02}E{episode_number:02}'
    )
    card_extension: CardExtension = '.jpg'

    # ImageMagick settings
    imagemagick_executable: Path | None = None
    use_magick_prefix: bool = False

    # Data sources and priorities
    image_source_priority: list[int] = []
    episode_data_source: int | None = None

    # Folder formats
    specials_folder_format: str = 'Specials'
    season_folder_format: str = 'Season {season_number}'

    # Sync settings
    sync_specials: bool = True
    delete_missing_episodes: bool = True
    delete_unsynced_series: bool = False
    completely_delete_series: bool = False

    # Card type settings
    default_card_type: str = 'tinted frame'
    excluded_card_types: list[str] = []
    default_watched_style: Style = 'unique'
    default_unwatched_style: Style = 'unique'
    default_templates: list[int] = []
    default_fonts: Annotated[
        dict[str, int],
        'Mapping of card type identifiers to default Font IDs'
    ] = {}
    default_blur_profiles: Annotated[
        dict[str, str],
        'Mapping of card type identifiers to default blur profiles'
    ] = {}
    global_extras: Annotated[
        dict[str, dict[str, str]],
        'Mapping of card type identifiers to default extras'
    ] = {}

    # Connection toggle flags
    use_emby: SerializationExclusion[bool] = False
    use_jellyfin: SerializationExclusion[bool] = False
    use_plex: SerializationExclusion[bool] = False
    use_sonarr: SerializationExclusion[bool] = False
    use_tmdb: SerializationExclusion[bool] = False
    use_tvdb: SerializationExclusion[bool] = False

    # UI settings
    require_auth: bool = False
    home_page_size: int = 100
    episode_data_page_size: int = 50
    source_preview_page_dimensions: str = '3x3'
    title_card_preview_page_dimensions: str = '3x3'
    stylize_unmonitored_posters: bool = False
    home_page_table_view: bool = True
    colorblind_mode: bool = False
    reduced_animations: bool = False
    display_live_messages: bool = True
    simplified_data_table: bool = True
    interactive_card_previews: bool = True
    library_unique_cards: bool = False

    # Advanced settings
    advanced_scheduling: bool = False
    task_schedules: Annotated[
        dict[str, str],
        'Mapping of Task schedule IDs to their cron expression'
    ] = {}
    blacklisted_blueprints: set[int] = set()
    imported_blueprints: set[int] = set()

    # Runtime state (not persisted)
    invalid_connections: SerializationExclusion[list[int]] = []
    libraries: SerializationExclusion[
        dict[int, tuple[MediaSource, list[str]]]
    ] = {}
    remote_card_types: SerializationExclusion[
        dict[str, type[BaseCardType]]
    ] = {}
    local_card_types: SerializationExclusion[
        dict[str, type[BaseCardType]]
    ] = {}

    # Version and schema tracking
    current_db_schema: SerializationExclusion[str | None] = None
    current_logging_db_schema: SerializationExclusion[str | None] = None
    server_boot_time: SerializationExclusion[datetime | None] = None


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

    @property
    def is_docker(self) -> bool:
        """Whether the application is running in Docker."""
        return self.config.IS_DOCKER


    def __init__(self) -> None:
        """Initialize the settings object."""

        super().__init__()
        self._load_preferences()


    def _load_preferences(self) -> None:
        """Load preferences from file if it exists."""

        if self.config.IS_DOCKER:
            pickle_file = Path('/config/config.pickle')
            json_file = Path('/config/settings.json')
        else:
            pickle_file = CONFIG_ROOT / 'config.pickle'
            json_file = CONFIG_ROOT / 'settings.json'

        self._preferences_file = json_file

        # First, try to migrate from pickle if it exists
        if pickle_file.exists():
            try:
                log.info(f'Migrating settings from pickle file: {pickle_file}')
                with pickle_file.open('rb') as f:
                    loaded_prefs = _PreferencesUnpickler(f).load()

                # Update settings with loaded preferences
                for attr, value in loaded_prefs.__dict__.items():
                    if (hasattr(self, attr)
                        and not attr.startswith('_')
                        and not hasattr(self, f'_{attr}')):
                        setattr(self, attr, value)

                # Save to JSON and delete pickle file
                self.commit()
                pickle_file.unlink()
                log.info(
                    f'Successfully migrated settings to JSON and deleted old '
                    f'settings file ({pickle_file})'
                )
            # Continue with default settings if migration fails
            except Exception as e:
                log.exception(f'Error occurred while migrating from pickle file: {e}')
        # Load from JSON if it exists
        elif json_file.exists():
            try:
                with json_file.open('r') as f:
                    data = json_load(f)

                # Update settings with loaded data
                for key, value in data.items():
                    if hasattr(self, key) and not key.startswith('_'):
                        # Handle special types
                        if key in [
                            'card_directory',
                            'source_directory',
                            'asset_directory',
                            'card_type_directory',
                            'temporary_directory',
                            'imagemagick_executable',
                        ]:
                            setattr(self, key, Path(value) if value else None)
                        elif key in ['blacklisted_blueprints', 'imported_blueprints']:
                            setattr(self, key, set(value) if value else set())
                        else:
                            setattr(self, key, value)

            except Exception as e:
                log.exception(f'Error occurred while loading JSON settings: {e}')

        # Set boot time
        self.server_boot_time = datetime.now(tz=self.config.TIMEZONE)


    def commit(self, *, log: Logger = log) -> None:
        """Commit current settings to JSON file."""

        if self._preferences_file:
            try:
                data = self._serialize()
                with self._preferences_file.open('w') as f:
                    log.trace((
                        f'Saving global settings:\n'
                        f'{json_dumps(data, indent=2, sort_keys=True)}'
                    ))
                    json_dump(data, f, indent=2, sort_keys=True)
            except Exception as e:
                log.exception(f'Error occurred while saving JSON settings: {e}')


    def update_values(self, *, log: Logger = log, **update_kwargs: Any) -> None:
        """Update multiple values at once and commit changes."""

        for name, value in update_kwargs.items():
            if hasattr(self, name) and value != '_UnspecifiedValue':
                setattr(self, name, value)
                log.debug(f'Settings.{name} = {value}')
        self.commit(log=log)


    def get_folder_format(self, episode_info: EpisodeInfo) -> str:
        """Get the season folder name for the given Episode."""
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
        """Get the CardType class for the given card type identifier."""

        if identifier in BUILTIN_CARD_TYPES:
            return BUILTIN_CARD_TYPES[identifier]
        if identifier in self.remote_card_types:
            return self.remote_card_types[identifier]
        if identifier in self.local_card_types:
            return self.local_card_types[identifier]

        log.error(f'Unable to identify card type "{identifier}"')
        return None


    def parse_local_card_types(self, *, log: Logger = log) -> None:
        """Parse all locally specified CardType Python files."""

        for file in self.card_type_directory.glob('*.py'):
            if not (card_type := RemoteCardType(file, log=log)).valid:
                log.critical('Error reading local CardType')
                continue
            if not card_type.card_class:
                continue
            details = card_type.card_class.API_DETAILS
            self.local_card_types[details.identifier] = card_type.card_class
            log.debug(f'Parsed local CardType[{details.identifier}]')


    def determine_imagemagick_prefix(self, log: Logger = log) -> None:
        """
        Determine whether to use the "magick " prefix for ImageMagick
        commands.

        Args:
            log: Logger to use for logging.
        """

        if self.config.IS_DOCKER:
            self.use_magick_prefix = False
            return

        for prefix, use_magick in (('magick', True), ('', False)):
            interface = ImageMagickInterface(
                container=self.config.IMAGEMAGICK_CONTAINER,
                use_magick_prefix=use_magick,
                executable=self.imagemagick_executable,
            )
            if interface.validate_interface():
                self.use_magick_prefix = use_magick
                log.debug((
                    f'Using "{prefix}" ImageMagick command prefix in '
                    + ('the primary thread' if use_magick else 'all threads')
                ))
                return
            interface.print_command_history(log=log)

        log.critical("ImageMagick doesn't appear to be installed")


    def log_startup(self, *, log: Logger = log) -> None:
        """Log the startup details of TCM."""

        log.info(f'Starting TitleCardMaker ({self.config.CURRENT_VERSION})')
        self.determine_imagemagick_prefix(log=log)


    @staticmethod
    def get_filesize(value: int | None, unit: str | None) -> int | None:
        """Get the filesize for the given value and unit."""

        if value is None or unit is None:
            return None

        return value * {
            'b': 1, 'bytes': 1,
            'kb': 2**10, 'kilobytes': 2**10,
            'mb': 2**20, 'megabytes': 2**20,
            'gb': 2**30, 'gigabytes': 2**30,
            'tb': 2**40, 'terabytes': 2**40,
        }[unit.lower()]


    @staticmethod
    def format_filesize(value: int | None) -> tuple[str, str]:
        """
        Format the given filesize limit into a tuple of filesize value
        and units.
        """

        if value is None or value == 0:
            return '0', 'Bytes'

        for ref_value, unit in (
            (10**12, 'Terabytes'),
            (10**9, 'Gigabytes'),
            (10**6, 'Megabytes'),
            (10**3, 'Kilobytes'),
            (1, 'Bytes')
        ):
            if value > ref_value:
                return f'{value/ref_value:,.1f}', unit

        return '0', 'Bytes'


    @staticmethod
    def standardize_style(style: str) -> str:
        """
        Standardize the given style string so that style modifiers are
        not order dependent.
        """

        standardized = str(style).lower().strip()
        if 'art' not in standardized and 'unique' not in standardized:
            standardized += ' unique'

        return ' '.join(sorted(standardized.split(' ')))


settings: Annotated[Settings, 'Global settings instance'] = Settings()


def reset_settings(*, log: Logger = log) -> Settings:
    """
    Reset the settings to their default values.

    Args:
        log: Logger to use for logging.
    """

    global settings

    # Delete the preferences file
    if settings._preferences_file and settings._preferences_file.exists():
        settings._preferences_file.unlink(missing_ok=True)

    # Get the default values from the class definition
    default_settings = Settings()

    # Get a set of all @property attributes, as these cannot be set
    properties = {
        name
        for name, value in Settings.__dict__.items()
        if isinstance(value, property)
    }

    # Reset all attributes to their default values
    # Cannot use __dict__ as most attributes are class attributes and
    # not present in __dict__ until assigned to the instance 
    for attr_name in dir(default_settings):
        if attr_name.startswith('_') or attr_name in properties:
            continue

        # Skip callable attributes (methods) - only copy data attributes
        if callable((attr_value := getattr(default_settings, attr_name))):
            continue
        if not attr_name.startswith('_') and hasattr(settings, attr_name):
            setattr(settings, attr_name, attr_value)

    # Commit the reset settings
    settings.commit(log=log)
    settings.__init__()

    return settings
