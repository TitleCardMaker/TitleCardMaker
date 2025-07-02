from io import StringIO
from pathlib import Path
from sys import exit as sys_exit

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from rich.console import Console
from rich.traceback import Traceback
from sqlalchemy.orm import Session
from starlette.staticfiles import StaticFiles

from app.core.schedule import initialize_scheduler
from app.core.availability import get_latest_version
from app.core.backup import backup_data, restore_backup
from app.core.cards import refresh_remote_card_types
from app.core.config import settings
from app.core.connection import initialize_connections
from app.core.settings import apply_card_type_blur_profiles
from app.db.database import engine as db_engine, SQLALCHEMY_DATABASE_URL
from app.db.scheduler import Scheduler
from app.dependencies import get_database, get_preferences
from app.logging.database import logs_engine, LOGS_DATABASE_URL
from app.logging.logger import contextualize, log as logger, Logger
from app.models.user import User
from app.settings import BACKEND_ROOT, FRONTEND_ROOT
from modules.BackgroundTasks import TracebackSuppressedPackages


APP_ROOT = BACKEND_ROOT / 'app'


def initialize_root_directories(*, log: Logger = logger) -> None:
    """
    Initialize the root directories for the application. This creates
    the required `/config` directories if running on Docker.

    Args:
        log: The logger to use for logging.
    """

    # Exit if not on Docker
    if not settings.IS_DOCKER:
        return None

    # Initialize root directories
    REQUIRED_ROOT_DIRECTORIES = (
        '/config/assets',
        '/config/backups',
        '/config/cards',
        '/config/logs',
        '/config/source',
        '/config/card_types',
    )
    try:
        for directory in REQUIRED_ROOT_DIRECTORIES:
            Path(directory).mkdir(parents=True, exist_ok=True)
    except Exception:
        log.critical('Error initializing root directories')
        log.exception('Raised error')
        sys_exit(1)


def mount_static_app_directories(app: FastAPI, *, log: Logger = logger) -> None:
    """
    Mount the static app directories into the FastAPI application.

    Args:
        app: The FastAPI application to mount the directories into.
        log: The logger to use for logging.
    """

    prefs = get_preferences()

    for (mount, directory) in (
        ('/css', FRONTEND_ROOT / 'css'),
        ('/js', FRONTEND_ROOT / 'js'),
        ('/pages', FRONTEND_ROOT / 'pages'),
        ('/public', FRONTEND_ROOT / 'public'),
        ('/assets', prefs.asset_directory),
        ('/cards', prefs.card_directory),
        ('/source', prefs.source_directory),
    ):
        try:
            app.mount(mount, StaticFiles(directory=directory))
        except RuntimeError:
            log.critical(
                f'Unable to mount StaticFiles("{directory}") - assets may not '
                f'load'
            )


def perform_database_migrations(*, log: Logger = logger) -> None:
    """
    Perform the database migrations.

    Args:
        app: The FastAPI application to mount the directories into.
        log: The logger to use for logging.
    """

    preferences = get_preferences()

    # Initialize Alembic config (simulating config.ini)
    for engine, url, migration_directory in (
        (db_engine, SQLALCHEMY_DATABASE_URL, APP_ROOT / 'alembic'),
        (logs_engine, LOGS_DATABASE_URL, APP_ROOT / 'logging' / 'alembic'),
    ):
        alembic_config = Config()
        alembic_config.set_main_option('sqlalchemy.url', url)
        alembic_config.set_main_option(
            'script_location', str(migration_directory)
        )

        # Backup database if migration is about to be performed
        backup = None
        script = ScriptDirectory.from_config(alembic_config)
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            if context.get_current_revision() == script.get_current_head():
                continue

            log.info('Pending schema migration - performing database backup')
            backup = backup_data(preferences.current_version, log=log)

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
                    restore_backup(backup, log=log)
                sys_exit(1)

            # Store current DB schema
            with engine.begin() as connection:
                context = MigrationContext.configure(connection)
                preferences.current_db_schema = context.get_current_revision()


def disable_authentication(db: Session, *, log: Logger = logger) -> None:
    """
    Disable authentication based on environment variable. This disables
    the global setting and deletes any existing Users.

    Args:
        log: The logger to use for logging.
    """

    if not settings.DISABLE_AUTH:
        return None

    # If authentication is required, disable it
    if (preferences := get_preferences()).require_auth:
        log.warning('Disabling Authentication (TCM_DISABLE_AUTH=TRUE)')
        preferences.require_auth = False
        preferences.commit()

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

    log = contextualize(logger)

    preferences = get_preferences()
    preferences.available_version = get_latest_version(raise_exc=False)
    preferences.log_startup(log=log)

    initialize_root_directories(log=log)
    mount_static_app_directories(app, log=log)
    perform_database_migrations(log=log)
    Scheduler.start() # Start the scheduler, initialized via repeated task
    apply_card_type_blur_profiles()

    # Database operations
    with next(get_database()) as db:
        # Refresh remote card types
        refresh_remote_card_types(db, log=log)

        disable_authentication(db, log=log)

        try:
            initialize_connections(db, preferences, log=log)
        except Exception:
            log.exception('Error initializing Connections')

    initialize_scheduler()


def teardown_app(app: FastAPI) -> None:
    """
    Teardown the FastAPI application.

    Args:
        app: The FastAPI application to teardown.
    """

    pass
