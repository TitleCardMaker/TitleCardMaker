from datetime import datetime, timedelta, tzinfo
from os import getenv
from pathlib import Path
from typing import Annotated, Literal

from pytz import timezone, UnknownTimeZoneError
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


"""
Application root directories
"""
IS_DOCKER = getenv('TCM_IS_DOCKER') == 'TRUE'
TCM_ROOT = Path(__file__).parent.parent.parent
BACKEND_ROOT = TCM_ROOT / 'backend'
FRONTEND_ROOT = TCM_ROOT / 'frontend'

CONFIG_ROOT = Path('/config') if IS_DOCKER else (TCM_ROOT / 'config')
LOG_ROOT = CONFIG_ROOT / 'logs'

# Logging levels
LogLevel = Literal['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class Settings(BaseSettings):
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

    INTERCEPT_PLEX_LOGS: Annotated[
        bool,
        'Whether to intercept Plex logs'
    ] = Field(default=False, alias='PLEX_LOGGING')

    PACKAGE_LOGGING: Annotated[
        str,
        'Comma-separated list of packages to intercept logging from'
    ] = Field(default='')

    LOG_RETENTION_DAYS: Annotated[
        int,
        'How many days to keep logs'
    ] = Field(default=7, ge=1)

    @property
    def TIMEZONE(self) -> tzinfo:
        if (tz_code := getenv('TZ', None)) is not None:
            try:
                return timezone(tz_code)
            except UnknownTimeZoneError:
                pass

        try:
            return datetime.now().astimezone().tzinfo
        except Exception:
            return timezone('UTC')

    # Execution mode
    IS_DOCKER: Annotated[
        bool,
        'Whether executing in Docker mode'
    ] = False

    # Backup
    BACKUP_RETENTION_DAYS: Annotated[
        int,
        'How long to keep old backups'
    ] = Field(default=21, alias='BACKUP_RETENTION')

    @property
    def BACKUP_RETENTION(self) -> timedelta:
        return timedelta(days=self.BACKUP_RETENTION_DAYS)

    # Authentication
    AUTH_EXPIRATION_DAYS: Annotated[
        int,
        'How many days to keep authentication tokens valid'
    ] = 7

    @property
    def AUTH_EXPIRATION_TIME(self) -> timedelta:
        return timedelta(days=self.AUTH_EXPIRATION_DAYS)

    DISABLE_AUTH: Annotated[bool, 'Whether to disable authentication'] = False

    CRYPTO_ALGORITHM: Annotated[
        str,
        'Algorithm to use for encryption'
    ] = 'HS256'

    # Testing mode
    TESTING_MODE: Annotated[
        bool,
        'Whether the server is in testing mode'
    ] = Field(default=False, alias='TESTING')

    # Version 1 settings
    V1_PREFERENCE_FILE: Annotated[
        Path,
        'Path to the global preferences.yml file'
    ] = Field(
        default=CONFIG_ROOT / 'preferences.yml',
        alias='PREFERENCES_FILE',
    )

    V1_CARD_QUALITY: Annotated[
        int,
        'Image compression quality to utilize'
    ] = Field(default=92, alias='CARD_QUALITY')

    V1_IMAGEMAGICK_CONTAINER: Annotated[
        str | None,
        'Docker container to execute ImageMagick commands within'
    ] = Field(default=None, alias='IMAGEMAGICK_DOCKER')

    V1_RUNTIME: Annotated[
        str | None,
        'When to first run the TitleCardMaker (in 24-hour time)'
    ] = Field(default=None)

    V1_FREQUENCY: Annotated[
        str,
        'How often to run the TitleCardMaker'
    ] = Field(default='12h')

    V1_MISSING_FILE: Annotated[
        Path,
        'File to write the list of missing assets to'
    ] = Field(default=CONFIG_ROOT / 'missing.yml')

    V1_TAUTULLI_LIST: Annotated[
        Path | None,
        'File to monitor for Tautulli-driven episode watch-status updates'
    ] = Field(default=None)

    V1_TAUTULLI_FREQUENCY: Annotated[
        str,
        'How often to check the Tautulli update list'
    ] = Field(default='4m')

settings = Settings()


"""Global tqdm arguments"""
TQDM_KWARGS = {
    # Progress bar format string
    'bar_format': (
        '{desc:.50s} {percentage:2.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}]'
    ),
    # Progress bars should disappear when finished
    'leave': False,
    # Progress bars can not be used if no TTY is present
    'disable': None,
}
