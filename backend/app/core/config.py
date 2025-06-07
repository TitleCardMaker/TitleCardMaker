from datetime import timedelta
from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from modules.preferences import Preferences


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='TCM_'
    )

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


settings = Settings()


if settings.IS_DOCKER:
    preferences_file = Path('/config/config.pickle')
else:
    preferences_file = (
        Path(__file__).parent.parent.parent
        / 'config'
        / 'config.pickle'
    )

PreferencesLocal = Preferences(preferences_file)

__all__ = [
    'settings',
    'PreferencesLocal'
]
