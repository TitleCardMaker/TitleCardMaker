from logging import Logger
from os import getenv

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import MetaData, text
from sqlalchemy.orm import Session

from app.api.v2 import v2_router
from app.api.v2.schedule import initialize_scheduler
from app.dependencies import get_database, get_logger, get_preferences
from modules.preferences import Preferences


# Create sub router for all API requests
api_router = APIRouter(prefix='/api')
api_router.include_router(v2_router)


@api_router.get('/healthcheck')
def health_check(
    db: Session = Depends(get_database),
    log: Logger = Depends(get_logger),
) -> None:
    """
    Check the health of the TCM server by attempting to perform a dummy
    database operation; raising an HTTPException (500) if a connection
    cannot be established.
    """

    try:
        db.execute(text('SELECT 1'))
    except Exception as exc:
        log.exception(f'Health check failed - {exc}')
        raise HTTPException(
            status_code=500,
            detail=f'Database returned some error - {exc}'
        ) from exc


@api_router.post('/reset')
def reset_database(
    db: Session = Depends(get_database),
    preferences: Preferences = Depends(get_preferences),
    log: Logger = Depends(get_logger),
) -> None:
    """
    Reset the entire database and system state. This DOES NOT clear any
    files, and requires the appropriate environment variable to be set
    in order to function.

    Intended only for testing setup and teardown.
    """

    from app.db.database import engine

    if getenv('TCM_TESTING', 'false') != 'TRUE':
        raise HTTPException(
            status_code=401,
            detail='Unauthorized',
        )

    # Delete all tables in the database in reverse order so children
    # are removed before parents
    metadata = MetaData()
    metadata.reflect(bind=engine)
    for table in reversed(metadata.sorted_tables):
        # Do not delete the version table so migrations aren't triggered
        if table.name == 'alembic_version':
            continue
        log.info(f'Deleting SQL Table "{table.name}"')
        db.execute(table.delete())
    db.commit()

    # Reset the global preferences
    preferences.reset(log=log)

    # Re-initialize the scheduler
    
    initialize_scheduler(override=True, log=log)
