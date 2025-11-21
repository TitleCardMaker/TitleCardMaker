import asyncio
from io import StringIO
from sys import exit as sys_exit
from typing import Annotated

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from huey.consumer import Consumer
from rich.console import Console
from rich.traceback import Traceback
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from starlette.staticfiles import StaticFiles

from app.core.availability import get_latest_version
from app.core.backup import backup_data, restore_backup
from app.core.cards import refresh_all_card_types
from app.core.connection import initialize_connections
from app.core.schedule import huey
from app.core.settings import apply_card_type_blur_profiles
from app.db.database import engine as db_engine, SQLALCHEMY_DATABASE_URL
from app.dependencies import get_database
from app.logging.database import logs_engine, LOGS_DATABASE_URL
from app.logging.logger import (
    contextualize,
    get_contextualized_logger,
    set_contextualized_logger,
)
from app.models.user import User
from app.settings import BACKEND_ROOT, FRONTEND_ROOT, settings
from app.utils.tasks import TracebackSuppressedPackages


APP_ROOT = BACKEND_ROOT / 'app'

huey_consumer: Annotated[Consumer | None, 'Global Huey Consumer'] = None


def initialize_root_directories() -> None:
    """
    Initialize the root directories for the application. This creates
    the required `/config` directories if running on Docker.
    """

    log = get_contextualized_logger()

    for directory in [
        settings.asset_directory,
        settings.backup_directory,
        settings.card_directory,
        settings.card_type_directory,
        settings.log_directory,
        settings.source_directory,
        settings.temporary_directory,
    ]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            log.critical((
                f'Could not initialize directory "{directory}" - invalid '
                f'permissions'
            ))
            sys_exit(1)
        except Exception:
            log.critical('Error initializing root directories')
            log.exception('Raised error')
            sys_exit(1)

    return None


def mount_static_app_directories(app: FastAPI) -> None:
    """
    Mount the static app directories into the FastAPI application.

    Args:
        app: The FastAPI application to mount the directories into.
    """

    log = get_contextualized_logger()

    for (mount, directory) in (
        ('/css', FRONTEND_ROOT / 'css'),
        ('/js', FRONTEND_ROOT / 'js'),
        ('/pages', FRONTEND_ROOT / 'pages'),
        ('/public', FRONTEND_ROOT / 'public'),
        ('/assets', settings.asset_directory),
        ('/cards', settings.card_directory),
        ('/source', settings.source_directory),
    ):
        try:
            app.mount(mount, StaticFiles(directory=directory))
        except RuntimeError:
            log.critical((
                f'Unable to mount StaticFiles("{directory}") - assets may not '
                f'load'
            ))


def perform_database_migrations() -> None:
    """Perform the database migrations."""

    log = get_contextualized_logger()

    def store_db_schema(engine: Engine, db_attribute: str) -> None:
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            version = context.get_current_revision()
            setattr(settings, db_attribute, version)
            log.info(f'Settings.{db_attribute} = {version}')

    # Initialize Alembic config (simulating config.ini)
    for engine, url, migration_directory, db_attribute in (
        (
            db_engine,
            SQLALCHEMY_DATABASE_URL,
            APP_ROOT / 'alembic',
            'current_db_schema',
        ),
        (
            logs_engine,
            LOGS_DATABASE_URL,
            APP_ROOT / 'logging' / 'alembic',
            'current_logging_db_schema',
        ),
    ):
        alembic_config = Config()
        alembic_config.set_main_option('sqlalchemy.url', url)
        alembic_config.set_main_option(
            'script_location', str(migration_directory)
        )

        backup = None
        script = ScriptDirectory.from_config(alembic_config)
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            # Backup database if migration is about to be performed
            if context.get_current_revision() != script.get_current_head():
                log.info('Pending schema migration - performing database backup')
                backup = backup_data(settings.config.CURRENT_VERSION)

                # Perform database migrations
                try:
                    command.upgrade(alembic_config, 'head')
                except Exception:
                    output = StringIO()
                    console = Console(file=output)
                    console.print(Traceback(
                        show_locals=True,
                        locals_max_length=512,
                        locals_max_string=512,
                        extra_lines=2,
                        indent_guides=False,
                        suppress=TracebackSuppressedPackages,
                    ))
                    log.error(f'SQL Migration Error:\n{output.getvalue()}')
                    log.critical('Unable to migrate and initialize Database')
                    if backup:
                        log.info('Restoring from backup..')
                        restore_backup(backup)
                    sys_exit(1)

            store_db_schema(engine, db_attribute)


def disable_authentication(db: Session) -> None:
    """
    Disable authentication based on environment variable. This disables
    the global setting and deletes any existing Users.

    Args:
        db: The database session to use.
    """

    log = get_contextualized_logger()

    if not settings.config.DISABLE_AUTH:
        return None

    # If authentication is required, disable it
    if settings.require_auth:
        log.warning('Disabling Authentication (TCM_DISABLE_AUTH=TRUE)')
        settings.require_auth = False
        settings.commit()

    # Delete all existing Users
    db.query(User).delete()
    db.commit()
    log.warning('Deleted all existing Users')


def initialize_app(app: FastAPI) -> None:
    """
    Initialize the FastAPI application.

    Args:
        app: The FastAPI application to initialize.
    """

    with contextualize() as (contextualization, log):
        settings.config.AVAILABLE_VERSION = get_latest_version(raise_exc=False)
        settings.log_startup()

        initialize_root_directories()
        mount_static_app_directories(app)
        perform_database_migrations()
        apply_card_type_blur_profiles()
        refresh_all_card_types()

        # Database operations
        with next(get_database()) as db:
            disable_authentication(db)

            try:
                initialize_connections(db)
            except Exception:
                log.exception('Error initializing Connections')

        contextualization.log_execution()


def initialize_huey() -> tuple[Consumer, asyncio.Task]:
    """
    Initialize the Huey Consumer. This launches a new thread which acts
    as the consumer for all scheduled recurring Huey tasks.

    Returns:
        Tuple containing the Huey Consumer and the asyncio Task which
        runs the consumer.
    """

    log, _ = set_contextualized_logger()

    # Initialize Huey Consumer
    global huey_consumer
    loop = asyncio.get_event_loop()
    # Flush locks to prevent tasks from being stuck in the queue
    huey_consumer = Consumer(huey, flush_locks=True, scheduler_interval=30)
    huey_consumer.start()
    log.info('Huey Consumer started')

    consumer_thread = asyncio.to_thread(huey_consumer.run)
    consumer_task = loop.create_task(consumer_thread)
    log.info(f'Huey Consumer task created in thread {consumer_task.get_name()}')

    return huey_consumer, consumer_task


def teardown_app(app: FastAPI) -> None:
    """
    Teardown the FastAPI application.

    Args:
        app: The FastAPI application to teardown.
    """

    pass


async def teardown_huey(consumer: Consumer, task: asyncio.Task) -> None:
    """
    Teardown the Huey Consumer. This stops the consumer and waits for
    the asyncio Task to complete.

    Args:
        consumer: The Huey Consumer to stop.
        task: The asyncio Task to wait for.
    """

    consumer.stop()
    await task
