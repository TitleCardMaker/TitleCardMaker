from datetime import datetime
import logging
from random import choices as random_choices
from string import hexdigits
import sys
from typing import TYPE_CHECKING

import better_exceptions
from fastapi import WebSocket
from loguru import logger as base_logger
from loguru._logger import Logger
from sqlalchemy.exc import OperationalError

from app.core.config import LOG_ROOT, config
from app.logging.database import LogsSessionLocal
from app.logging.models import Log

if TYPE_CHECKING:
    from loguru import Message


"""Websocket connections to send log messages to"""
ACTIVE_WEBSOCKETS: set[WebSocket] = set()

"""Do not limit the length of exception tracebacks"""
better_exceptions.MAX_LENGTH = None

"""
Logging filters and sinks
"""
SECRETS: set[str] = set()
def _redact_secrets(message: str) -> str:
    """Redact all secrets from the given message."""

    # Redact the longest secrets first so that substrings of secrets are
    # not leaked - e.g. {'ABC', 'ABCDEF'} would redact 'ABC' and then
    # leave 'DEF' exposed
    for secret in sorted(SECRETS, key=len, reverse=True):
        message = message.replace(secret, '[REDACTED]')

    return message


def _sqlalchemy_sink(message: 'Message') -> None:
    """Write log messages to SQLAlchemy database."""

    record = message.record
    
    exc_type = None
    exc_value = None
    exc_traceback = None
    if record['exception'] is not None and len(base_logger._core.handlers) > 2:
        exc_type = str(record['exception'].type)
        exc_value = str(record['exception'].value)
        tb = base_logger._core.handlers[2]._exception_formatter.format_exception(
            *record['exception']
        )
        exc_traceback = _redact_secrets(''.join(tb))

    log_entry = Log(
        timestamp=record['time'],
        level_name=record['level'].name,
        level_number=record['level'].no,
        message=_redact_secrets(record['message']),
        context_id=record['extra'].get('context_id'),
        file=getattr(record.get('file', {}), 'path', None),
        line=record.get('line'),
        exception_type=exc_type,
        exception_value=exc_value,
        exception_traceback=exc_traceback
    )

    db = LogsSessionLocal()
    try:
        db.add(log_entry)
        db.commit()
    except OperationalError:
        # Do not raise an Exception for logging-related database errors
        pass
    finally:
        db.close()


async def _websocket_logger(message: str) -> None:
    for connection in ACTIVE_WEBSOCKETS:
        try:
            await connection.send_text(message)
        except Exception:
            pass


def generate_context_id() -> str:
    """
    Generate a unique pseudo-random "unique" ID.
    
    Returns:
        6 character string of pseudo-random hexadecimal chacters.
    """

    return ''.join(random_choices(hexdigits, k=6)).lower()


def contextualize(
        logger: Logger = base_logger,
        context_id: str | None = None
    ) -> Logger:
    """
    Create a contextualized logger with a context ID for request
    tracking.

    Args:
        logger: Base logger to contextualize.
        context_id: Context ID to bind to the logger. If None, a random
            one will be generated.

    Returns:
        Contextualized logger with the context ID bound.
    """

    return logger.bind(context_id=context_id or generate_context_id())


def _configure_logger(logger: Logger) -> Logger:
    """Configure the logger with all sinks and handlers."""

    # Remove default handler
    logger.remove()

    # Add handlers
    handlers = [
        # WARNING: The sys.stdout print WILL NOT have secrets redacted
        dict(
            sink=sys.stdout,
            level=config.CONSOLE_LOG_LEVEL,
            format='<level>[{level.name[0]}] {message}</level>',
            colorize=True,
            backtrace=True,
            diagnose=True,
            enqueue=True,
        ),
        dict(
            sink=_sqlalchemy_sink,
            level=config.DATABASE_LOG_LEVEL,
            format='{message}',
            colorize=False,
            backtrace=True,
            diagnose=True,
            # Do not serialize each log entry as JSON as this is handled by the
            # formatter! See
            # https://loguru.readthedocs.io/en/latest/resources/recipes.html
            # serialize=True,
            # Make log calls non-blocking
            enqueue=True,
        ),
        # Uncomment to capture SQLAlchemy logging
        # dict(
        #     sink='sqlalchemy.engine',
        #     level='DEBUG',
        # ),
        # Asyncronous websocket handler - must be removed if executing in an
        # environment w/o an event loop
        dict(
            sink=_websocket_logger,
            level=config.WEBSOCKET_LOG_LEVEL,
            format='{message}',
            colorize=False,
            backtrace=False,
            enqueue=False,
        ),
    ]
    levels = [
        dict(name='TRACE', color='<dim><fg #d0d0d0>'),
        dict(name='DEBUG', color='<dim><white>'),
        dict(name='INFO', color='<light-cyan>'),
        dict(name='WARNING', color='<yellow>'),
        dict(name='ERROR', color='<magenta>'),
        dict(name='CRITICAL', color='<red><bold>'),
    ]

    try:
        logger.configure(handlers=handlers, levels=levels) # type: ignore
    except ValueError:
        # Remove the async handler if executing without an event loop
        handlers.pop(-1)
        logger.configure(handlers=handlers, levels=levels) # type: ignore

    # Automatically redact all messages
    return logger.patch(
        lambda record: record.update(message=_redact_secrets(record['message']))
    )


def _intercept_plex_logs(logger: Logger) -> Logger:
    """Intercept all PlexAPI logs and reroute them to Loguru."""

    # Custom handler to redirect logging messages to Loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info)\
                .bind(context_id='plexapi')\
                .log(level, record.getMessage())

    # Modify PlexAPI logger with the custom handler
    plex_logger = logging.getLogger('plexapi')
    plex_logger.handlers = []
    plex_logger.addHandler(InterceptHandler())
    logger.trace('Intercepting PlexAPI logs')

    return logger


def _intercept_package_logs(logger: Logger, logger_name: str) -> Logger:
    """Enable HTTPConnection debug logging to the logging framework"""

    # Redirect standard logging messages to loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord):
            logger.bind(context_id=record.name).log('TRACE', record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logging.getLogger(logger_name).setLevel(logging.DEBUG)
    logger.trace(f'Intercepting "{logger_name}" requests')

    return logger


def initialize_logging() -> Logger:
    """Initialize the logging system."""

    # Create parent folders for the log database
    LOG_ROOT.mkdir(parents=True, exist_ok=True)

    logger = _configure_logger(base_logger)

    if config.INTERCEPT_PLEX_LOGS:
        logger = _intercept_plex_logs(logger)

    # If intercepting all packages, use the root logger
    if config.PACKAGE_LOGGING.lower() == 'all':
        logger = _intercept_package_logs(logger, '')
    elif config.PACKAGE_LOGGING:
        for package in config.PACKAGE_LOGGING.split(','):
            logger = _intercept_package_logs(logger, package)

    return logger


log = initialize_logging()
