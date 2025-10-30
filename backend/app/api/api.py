from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import MetaData, text
from sqlalchemy.orm import Session

from app.api.v2 import v2_router
from app.dependencies import get_database, get_logger
from app.logging.logger import Logger
from app.settings import reset_settings, settings


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
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Reset the entire database and system state. This DOES NOT clear any
    files, and requires the appropriate environment variable to be set
    in order to function.

    Intended only for testing setup and teardown.
    """

    from app.db.database import engine

    if not settings.config.TESTING_MODE:
        raise HTTPException(status_code=401, detail='Unauthorized')

    # Delete all tables in the database in reverse order so children
    # are removed before parents
    metadata = MetaData()
    metadata.reflect(bind=engine)
    for table in reversed(metadata.sorted_tables):
        # Do not delete the version table so migrations aren't triggered
        if table.name == 'alembic_version':
            continue
        log.debug(f'Deleting SQL Table "{table.name}"')
        db.execute(table.delete())
    db.commit()

    reset_settings(log=log)
