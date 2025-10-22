from signal import SIGINT, raise_signal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.backup import (
    backup_data,
    delete_backup,
    delete_old_backups,
    list_available_backups,
    restore_backup,
)
from app.db.database import engine
from app.db.users import get_current_user
from app.dependencies import get_logger
from app.logging.logger import ACTIVE_WEBSOCKETS, Logger
from app.schemas.preferences import SystemBackup
from app.settings import settings
from modules.BackgroundTasks import task_queue


# Create sub router for all /backups API requests
backup_router = APIRouter(
    prefix='/backups',
    tags=['Backups'],
    dependencies=[Depends(get_current_user)],
)


@backup_router.get('/all')
def get_available_system_backups(
    log: Logger = Depends(get_logger),
) -> list[SystemBackup]:
    """Get a list detailing all the available system backups."""

    return list_available_backups(log=log)


@backup_router.post('/backup')
def perform_backup(log: Logger = Depends(get_logger)) -> None:
    """Perform a backup of the SQL database and global settings."""

    backup_data(settings.config.CURRENT_VERSION, log=log)


@backup_router.post('/restore/{folder}')
async def restore_from_backup(
    folder: str,
    bypass: bool = Query(default=False),
    log: Logger = Depends(get_logger),
) -> None:
    """

    - bypass: Whether to bypass the "lock" if there are currently any
    running or pending tasks.
    """

    if task_queue or engine.pool.checkedout() > 0: # type: ignore
        if bypass:
            log.warning(
                'Restoring from backup while there are pending operations - '
                'performing backup to prevent data loss'
            )
            log.trace(f'TaskQueue: {task_queue}\nPool: {engine.pool}')
            backup_data(settings.config.CURRENT_VERSION, log=log)
        else:
            raise HTTPException(
                status_code=400,
                detail='There are pending Background Tasks/Database Connections'
            )

    # Restore from backup
    restore_backup(folder, log=log)

    # Kill any active websockets
    for connection in list(ACTIVE_WEBSOCKETS):
        try:
            log.debug(f'Killing WebSocket.. {connection}')
            await connection.close()
        finally:
            ACTIVE_WEBSOCKETS.remove(connection)

    # Raise a signal interrupt to kill the server
    log.info('Please shut down TitleCardMaker for these changes to take effect')
    raise_signal(SIGINT)


@backup_router.delete('/outdated')
def delete_outdated_backups(log: Logger = Depends(get_logger)) -> None:
    """
    Delete all backups older than the globally configured retention
    policy. This is adjusted with the `TCM_BACKUP_RETENTION` environment
    variable (integer number of days).
    """

    delete_old_backups(log=log)


@backup_router.delete('/backup/{folder}')
def delete_backup_folder(
    folder: str,
    log: Logger = Depends(get_logger),
) -> None:
    """
    Delete the backup data located in the given folder.

    - folder: Folder to delete.
    """

    delete_backup(folder, log=log)
