from datetime import datetime
from pathlib import Path
from shutil import copy as file_copy
from sqlite3 import connect, OperationalError
from typing import NamedTuple

from fastapi import HTTPException

from app.core.config import CONFIG_ROOT, config as app_config
from app.schemas.preferences import DatabaseBackup, SettingsBackup, SystemBackup
from app.settings import settings
from app.logging.logger import Logger, log
from app.utils.version import Version


class DataBackup(NamedTuple): # pylint: disable=missing-class-docstring
    config: Path
    database: Path


def delete_old_backups(*, log: Logger = log) -> None:
    """
    Delete all backups older than the configured retention period.

    Args:
        log: Logger for all log messages.
    """

    delete_before = datetime.now() - app_config.BACKUP_RETENTION

    for backup in settings.backup_directory.iterdir():
        # Backup subdirectories
        if backup.is_dir():
            try:
                date = datetime.strptime(backup.name, app_config.BACKUP_DT_FORMAT)
            except ValueError:
                log.warning(f'Cannot identify date of backup file "{backup}"')
                continue

            if date < delete_before:
                for file in backup.iterdir():
                    file.unlink(missing_ok=True)
                    log.debug(f'Deleted old backup "{backup.name}/{file.name}"')
                backup.rmdir()
        # Old-style files not stored in a subdirectory
        else:
            try:
                date = datetime.strptime(
                    backup.name.rsplit('.')[-1],
                    app_config.BACKUP_DT_FORMAT
                )
            except ValueError:
                log.debug(f'Cannot identify date of backup file "{backup}"')
                continue

            if date < delete_before:
                backup.unlink(missing_ok=True)
                log.debug(f'Deleted old backup "{backup}"')


def delete_backup(folder_name: str | Path, *, log: Logger = log) -> None:
    """
    Delete the given backup folder.

    Args:
        folder_name: Name of the directory to delete.
        log: Logger for all log messages.
    """

    if not (folder := Path(settings.backup_directory / folder_name)).exists():
        log.debug(f'Specified backup folder ({folder}) does not exist')
        return None

    # Delete subcontents and folder
    for file in folder.iterdir():
        file.unlink(missing_ok=True)
        log.debug(f'Deleted backup file "{folder.name}/{file.name}"')
    folder.rmdir()

    return None


def backup_data(
        version: str | Version,
        *,
        log: Logger = log,
    ) -> DataBackup:
    """
    Perform a backup of the SQL database and global preferences. This
    also deletes any "old" backups.

    Args:
        version: Current version of TCM.
        log: Logger for all log messages.

    Returns:
        Tuple of Paths to created preferences and database backup files.
    """

    # Store backups in a dated subfolder
    settings.backup_directory.mkdir(exist_ok=True, parents=True)
    backup_folder = (
        settings.backup_directory
        / datetime.now().strftime(app_config.BACKUP_DT_FORMAT)
    )
    backup_folder.mkdir(exist_ok=True, parents=True)

    # Identify source and destination files
    config = CONFIG_ROOT / 'settings.json'
    config_backup = backup_folder / f'settings.json.{version}'
    database = CONFIG_ROOT / 'db.sqlite'
    database_backup = backup_folder / f'db.sqlite.{version}'

    delete_old_backups(log=log)

    # Backup config
    if config.exists():
        file_copy(config, config_backup)
        log.info(f'Performed settings backup ({config_backup})')
    else:
        log.warning(f'Cannot backup settings from "{config.resolve()}"')

    # Backup database
    if database.exists():
        file_copy(database, database_backup)
        log.info(f'Performed database backup ({database_backup})')
    else:
        log.warning(f'Cannot backup database from "{database.resolve()}"')

    return DataBackup(config=config_backup, database=database_backup)


def restore_backup(backup: DataBackup | str, /, *, log: Logger = log):
    """
    Restore the config and database from the given data backup.

    Args:
        backup: Tuple of backup data (as returned by `backup_data()`)
            to restore from; or the name of the folder containing data.
        log: Logger for all log messages.
    """

    # If a folder name was provided, search for the config/db files
    if isinstance(backup, str):
        folder = settings.backup_directory / backup
        try:
            config = next(folder.glob('settings.json*'))
            database = next(folder.glob('db.sqlite*'))
        except StopIteration as exc:
            log.exception('Unable to identify backup data from folder')
            raise HTTPException(
                status_code=400,
                detail='Invalid backup folder'
            ) from exc
    else:
        config, database = backup

    # Restore config
    if config and config.exists():
        file_copy(config, CONFIG_ROOT / 'settings.json')
        log.debug(f'Restored backup from "{config}"')
    else:
        log.warning(f'Cannot restore backup from "{config}"')

    # Restore database
    if database.exists():
        file_copy(database, CONFIG_ROOT / 'db.sqlite')
        log.debug(f'Restored backup from "{database}"')
    else:
        log.warning(f'Cannot restore backup from "{database}"')


def list_available_backups(*, log: Logger = log) -> list[SystemBackup]:
    """
    Get a list detailing all the available system backups.

    Args:
        log: Logger for all log messages.

    Returns:
        List of system backup information.
    """

    def _parse_version_number(file: Path) -> str:
        """Parse the version number from the given file."""
        return file.name[len('settings.json') + 1:]

    def _parse_schema_version(file: Path) -> str | None:
        """Parse the alembic schema version from the given file."""
        connection = connect(file)
        try:
            return (
                connection.cursor()
                    .execute('SELECT * FROM alembic_version LIMIT 1')\
                    .fetchone()[0]
            )
        except OperationalError:
            log.debug(f'Unable to detect schema from {file}')
            return None
        finally:
            connection.close()

    backups: list[SystemBackup] = []
    for subfolder in settings.backup_directory.glob('2*'):
        # Find setting and database files
        try:
            settings_file = next(subfolder.glob('settings.json*'))
            database = next(subfolder.glob('db.sqlite*'))
        except StopIteration:
            log.debug(f'Missing backup file(s) from "{subfolder}"')
            continue

        # Skip if there's no version or schema
        if (not (schema := _parse_schema_version(database))
            or not (version := _parse_version_number(settings_file))):
            log.debug((
                f'Unable to identify database schema or version from '
                f'"{subfolder}'
            ))
            continue

        backups.append(SystemBackup(
            database=DatabaseBackup(
                filename=database.name,
                filesize=database.stat().st_size,
                schema_version=schema,
            ),
            settings=SettingsBackup(
                filename=settings_file.name,
                filesize=settings_file.stat().st_size,
            ),
            timestamp=datetime.strptime(
                settings_file.parent.name, app_config.BACKUP_DT_FORMAT
            ),
            version=version,
            folder_name=subfolder.name,
        ))

    return sorted(backups, key=lambda b: b.timestamp)
