import logging
from os import environ, getenv
from pathlib import Path
import sys
import sqlite3

import better_exceptions
from fastapi import WebSocket
from loguru import logger


"""Format for all datetime objects written to log files"""
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f %Z'
DATETIME_FORMAT_NO_TZ = '%Y-%m-%d %H:%M:%S.%f'

"""Base log database"""
LOG_DB = Path(__file__).parent.parent / 'config' / 'logs' / 'logs.db'
if getenv('TCM_IS_DOCKER', 'false').lower() == 'true':
    LOG_DB = Path('/config/logs/logs.db')
LOG_DB.parent.mkdir(parents=True, exist_ok=True)

# Initialize SQLite database for logs
def init_log_db():
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            context_id TEXT,
            file TEXT,
            line INTEGER,
            exception_type TEXT,
            exception_value TEXT,
            exception_traceback TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_log_db()

"""Websocket connections to send log messages to"""
ACTIVE_WEBSOCKETS: set[WebSocket] = set()

"""Do not limit the length of exception tracebacks"""
better_exceptions.MAX_LENGTH = None

"""
Logging filters and formatters
"""
SECRETS: set[str] = set()
def redact_secrets(message: str) -> str:
    """Redact all secrets from the given message."""

    # Redact the longest secrets first so that substrings of secrets are
    # not leaked - e.g. {'ABC', 'ABCDEF'} would redact 'ABC' and then
    # leave 'DEF' exposed
    for secret in sorted(SECRETS, key=len, reverse=True):
        message = message.replace(secret, '[REDACTED]')

    return message

def sqlite_sink(message: str) -> None:
    """Write log messages to SQLite database."""
    record = message.record
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    
    exc_type = None
    exc_value = None
    exc_traceback = None
    if record['exception'] is not None:
        exc_type = str(record['exception'].type)
        exc_value = str(record['exception'].value)
        tb = logger._core.handlers[2]._exception_formatter.format_exception(
            *record['exception']
        )
        exc_traceback = redact_secrets(''.join(tb))

    c.execute('''
        INSERT INTO logs (
            timestamp, level, message, context_id, file, line,
            exception_type, exception_value, exception_traceback
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        record['time'].strftime(DATETIME_FORMAT),
        record['level'].name,
        redact_secrets(record['message']),
        record['extra'].get('context_id'),
        getattr(record.get('file', {}), 'path', None),
        record.get('line'),
        exc_type,
        exc_value,
        exc_traceback
    ))
    conn.commit()
    conn.close()

"""
Send log messages over all active WebSockets for real-time logs to the
UI.
"""
async def websocket_logger(message: str) -> None:
    for connection in ACTIVE_WEBSOCKETS:
        try:
            await connection.send_text(message)
        except Exception:
            pass

handlers = [
    # WARNING: The sys.stdout print WILL NOT have secrets redacted
    dict(
        sink=sys.stdout,
        level=getenv('TCM_LOG_STDOUT', getenv('TCM_LOG', 'INFO')),
        format='<level>[<bold>{level}</bold>] {message}</level>',
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    ),
    dict(
        sink=sqlite_sink,
        level=environ.get('TCM_LOG_FILE', 'TRACE'),
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
        sink=websocket_logger,
        level=getenv('TCM_LOG_WEBSOCKET', 'INFO'),
        format='{message}',
        colorize=False,
        backtrace=False,
        enqueue=environ.get('TCM_V1', 'False') == 'False',
    ),
]
levels = [
    dict(name='TRACE', color='<dim><fg #6d6d6d>'),
    dict(name='DEBUG', color='<dim><white>'),
    dict(name='INFO', color='<light-cyan>'),
    dict(name='WARNING', color='<yellow>'),
    dict(name='ERROR', color='<fg 237,112,46>'),
    dict(name='CRITICAL', color='<red><bold>'),
]

try:
    logger.configure(handlers=handlers, levels=levels) # type: ignore
except ValueError:
    # Remove the async handler if executing without an event loop
    handlers.pop(-1)
    logger.configure(handlers=handlers, levels=levels) # type: ignore

# Automatically redact all messages
logger = logger.patch(
    lambda record: record.update(message=redact_secrets(record['message']))
)


def intercept_plex_logs():
    """Intercept all PlexAPI logs and reroute them to Loguru."""

    # Custom handler to redirect logging messages to Loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
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

if getenv('TCM_PLEX_LOGGING') == 'TRUE':
    intercept_plex_logs()

def intercept_package_logs(logger_name):
    """Enable HTTPConnection debug logging to the logging framework"""

    # Redirect standard logging messages to loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            logger.bind(context_id=logger_name).log('TRACE', record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logging.getLogger(logger_name).setLevel(logging.DEBUG)
    logger.trace(f'Intercepting "{logger_name}" requests')

if packages := getenv('TCM_PACKAGE_LOGGING'):
    for package in packages.split(','):
        intercept_package_logs(package)
