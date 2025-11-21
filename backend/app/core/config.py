"""
Core non-runtime configuration settings. This file cannot have any
project dependencies to avoid circular imports.
"""
from datetime import datetime, timedelta
from os import getenv
from pathlib import Path
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from tzlocal import get_localzone

from app.utils.version import Version

"""
Application root directories
"""
IS_DOCKER = getenv('TCM_IS_DOCKER') == 'TRUE'
TCM_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_ROOT = TCM_ROOT / 'backend'
FRONTEND_ROOT = TCM_ROOT / 'frontend'
INTERNAL_ASSET_DIRECTORY = FRONTEND_ROOT / 'public'

CONFIG_ROOT = Path('/config') if IS_DOCKER else (TCM_ROOT / 'config')
LOG_ROOT = CONFIG_ROOT / 'logs'

# Logging levels
LogLevel = Literal['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class AppConfig(BaseSettings):
    """
    Global environment-configured configuration settings. These cannot
    be changed at runtime.
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='TCM_'
    )

    """
    Logging-related Settings
    """
    CONSOLE_LOG_LEVEL: Annotated[
        LogLevel,
        'Level of logging verbosity to use in the console'
    ] = Field(default='INFO')

    DATABASE_LOG_LEVEL: Annotated[
        LogLevel,
        'Level of logging verbosity to use in the logging database'
    ] = Field(default='TRACE')

    WEBSOCKET_LOG_LEVEL: Annotated[
        LogLevel,
        'Level of logging verbosity to use in the frontend WebSocket'
    ] = Field(default='INFO')

    CONSOLE_LOG_WIDTH: Annotated[
        int | None,
        'Width of the console log'
    ] = Field(default=None, ge=40)

    INTERCEPT_PLEX_LOGS: Annotated[
        bool,
        'Whether to intercept Plex logs'
    ] = Field(default=False)

    PACKAGE_LOGGING: Annotated[
        str,
        'Comma-separated list of packages to intercept logging from'
    ] = Field(default='')

    LOG_RETENTION_DAYS: Annotated[
        int,
        'How many days to keep logs'
    ] = Field(default=7, ge=1)

    _TIMEZONE: ZoneInfo | None = None

    @property
    def TIMEZONE(self) -> ZoneInfo:
        if self._TIMEZONE is not None:
            return self._TIMEZONE

        try:
            self._TIMEZONE = get_localzone()
        except Exception:
            self._TIMEZONE = ZoneInfo('UTC')

        return self._TIMEZONE

    def now(self) -> datetime:
        """Get the current time in the configured timezone."""
        return datetime.now(tz=self.TIMEZONE)

    # Valid image extensions
    VALID_IMAGE_EXTENSIONS: Annotated[
        tuple[str, ...],
        'Valid image extensions'
    ] = ('.jpg', '.jpeg', '.png', '.tiff', '.gif', '.webp')

    # Execution mode
    IS_DOCKER: Annotated[
        bool,
        'Whether executing in Docker mode'
    ] = False

    AVAILABLE_VERSION: Annotated[
        Version | None,
        'The latest available version of TitleCardMaker'
    ] = None

    CURRENT_VERSION: Annotated[
        Version,
        'The current version of TitleCardMaker'
    ] = Version((BACKEND_ROOT / '.version').read_text().strip())

    # Backup
    BACKUP_DT_FORMAT: Annotated[
        str,
        'Naming scheme for backup subfolders'
    ] = Field(default='%Y-%m-%d_%H-%M-%S')

    BACKUP_RETENTION_DAYS: Annotated[
        int,
        'How long to keep old backups'
    ] = Field(default=21, ge=1)

    @property
    def BACKUP_RETENTION(self) -> timedelta:
        return timedelta(days=self.BACKUP_RETENTION_DAYS)

    # Authentication
    AUTH_EXPIRATION_DAYS: Annotated[
        int,
        'How many days to keep authentication tokens valid'
    ] = Field(default=7, ge=1, le=120)

    @property
    def AUTH_EXPIRATION_TIME(self) -> timedelta:
        return timedelta(days=self.AUTH_EXPIRATION_DAYS)

    DISABLE_AUTH: Annotated[bool, 'Whether to disable authentication'] = False

    CRYPTO_ALGORITHM: Annotated[
        str,
        'Algorithm to use for encryption'
    ] = 'HS256'

    # Connection timeouts
    SONARR_REQUEST_TIMEOUT: Annotated[
        int,
        'Timeout for Sonarr requests (in seconds)'
    ] = Field(default=500, ge=10, le=10000)

    # Testing
    TESTING_MODE: Annotated[
        bool,
        'Whether the server is in testing mode'
    ] = Field(default=False, alias='TCM_TESTING')

    CARD_TYPE_REPOSITORY: Annotated[
        str,
        'URL to the card type repository'
    ] = Field(
        default=(
            'https://raw.githubusercontent.com/TitleCardMaker/CardTypes/'
            + ('web-ui-develop' if CURRENT_VERSION.is_develop else 'web-ui')
        ),
    )

    @property
    def CARD_TYPE_URL(self) -> str:
        return self.CARD_TYPE_REPOSITORY.removesuffix('/') + '/cards.json'


    IMAGEMAGICK_CONTAINER: Annotated[
        str | None,
        'Docker container to execute ImageMagick commands within'
    ] = Field(default=None)


    def localize(self, date: datetime, /) -> datetime:
        """Localize the given date to the configured timezone."""

        if date.tzinfo is None:
            date = date.astimezone(self.TIMEZONE)

        return date.astimezone(ZoneInfo('UTC'))


# Create global settings instance
config = AppConfig()


__all__ = [
    'config'
]
