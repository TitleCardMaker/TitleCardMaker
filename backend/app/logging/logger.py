from contextvars import ContextVar
import logging
from pathlib import Path
from random import choices as random_choices
from string import hexdigits
import sys
from time import time as current_time
from types import TracebackType
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Self
from uuid import uuid4

import better_exceptions
from fastapi import Request, Response, WebSocket
from loguru import logger as base_logger
from loguru._logger import Logger
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from sqlalchemy.exc import OperationalError

from app.core.config import LOG_ROOT, config
from app.logging.database import LogsSessionLocal
from app.logging.models import Log

if TYPE_CHECKING:
    from loguru import Message, Record


ACTIVE_WEBSOCKETS: Annotated[
    set[WebSocket],
    'Websocket connections to send log messages to'
] = set()

# Do not limit the length of exception tracebacks
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
        #     enqueue=True,
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


_global_log = initialize_logging()
rlv: ContextVar[Logger] = ContextVar('request_logger')


def set_contextualized_logger() -> tuple[Logger, str]:
    """
    Set the contextualized logger for the current request.

    Returns:
        Tuple containing the contextualized logger and the context ID.
    """

    context_id = uuid4().hex[:6]
    context_logger = _global_log.bind(context_id=context_id)

    rlv.set(context_logger)

    return context_logger, context_id


def get_contextualized_logger() -> Logger:
    """
    Get the contextualized Logger from the Request object.

    Returns:
        Contextualized logger with a (pseudo)random context ID for this
        request.
    """

    return rlv.get(_global_log)


class contextualize_request:
    """
    Context manager which creates a contextualized logger which captures
    the logs for a given FastAPI request.

    >>> with contextualize_request(request) as (contextualization, log):
    ...     log.info('Hello, world!')
    ...     await call_next(request) # Do some request processing
    ...     contextualization.log_response()
    """

    PANEL_MARGIN: ClassVar[int] = 4

    def __init__(self, request: Request) -> None:
        self._context_id = generate_context_id()
        self._request = request
        self._logger = _global_log
        self._log_buffer: list[str] = []
        self._request_start_time = current_time()
        self._last_message_time = current_time()
        self._sink_id: int | None = None


    def __enter__(self) -> tuple[Self, Logger]:
        self._logger = _global_log.bind(context_id=self._context_id)
        rlv.set(self._logger)

        def sink(message: 'Message') -> None:
            self._log_buffer.append(self._format_record(message.record))

        self._sink_id = _global_log.add(sink, level='TRACE')

        return self, self._logger


    def __exit__(self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_traceback: TracebackType | None,
        ) -> bool:
        """
        Exit the contextualized logger context.
        """

        if self._sink_id is not None:
            self._logger.remove(self._sink_id)

        return False


    def _format_record(self, record: 'Record') -> str:
        """
        Add a metadata line to the beginning of the log message.

        Args:
            record: The log record to add the metadata line to.

        Returns:
            An amended log message with the metadata line added.
        """

        level = record['level'].name

        file_string = 'unknown'
        if ((file_obj := record.get('file', {}))
            and (file_path := getattr(file_obj, 'path', None))):
            filename = Path(str(file_path)).name
            line_number = record.get('line', '?')
            file_string = f'{filename}:{line_number}'

        time_string = (
            f'+{(record["time"].timestamp()-self._last_message_time)*1000:.0f}ms'
        )

        center_width = (
            config.CONSOLE_LOG_WIDTH
            - (
                self.PANEL_MARGIN
                + len(level)
                + len(time_string)
                + self.PANEL_MARGIN
            )
        )
        metadata_line = f'{level}{file_string.center(center_width)}{time_string}'

        self._last_message_time = record['time'].timestamp()

        return f'{metadata_line}\n{record["message"]}'


    def _get_request_panel(self) -> Panel:
        """
        Format the request panel for the API request.
        """

        return Panel(
            Text('\n'.join([
                f'URL: {self._request.url}',
                f'Method: {self._request.method}',
                f'Query Parameters: {dict(self._request.query_params)}',
                f'Path Parameters: {self._request.path_params}',
            ])),
            title=f'[bold yellow]REQUEST INFO[/]',
            border_style='yellow',
        )


    def _get_logs_panel(self) -> Panel | None:
        """
        Get a formatted Panel containing all log messages for the
        request.

        Returns:
            A formatted Panel containing all log messages for the request,
            or None if no log messages are available.
        """

        if not self._log_buffer:
            return None

        text = Text()
        for idx, message in enumerate(self._log_buffer):
            text.append(message)
            # Add separator until the last message
            if idx < len(self._log_buffer) - 1:
                inner_width = config.CONSOLE_LOG_WIDTH - (self.PANEL_MARGIN * 2)
                text.append(f'\n{"-" * inner_width}\n', style='dim')

        return Panel(
            text,
            title="[bold cyan]APPLICATION LOG MESSAGES[/]",
            border_style="cyan",
        )


    def _get_response_panel(self, response: Response) -> Panel:

        response_time_ms = (current_time() - self._request_start_time) * 1000

        return Panel(
            Text('\n'.join([
                f'Status Code: {response.status_code}',
                f'Response Time: {response_time_ms:.1f}ms',
            ])),
            title='[bold green]RESPONSE INFO[/]',
            border_style='green',
        )


    def log_response(self, response: Response) -> None:

        panels = [
            self._get_request_panel(),
            self._get_logs_panel(),
            self._get_response_panel(response),
        ]

        combined = Group(*(panel for panel in panels if panel is not None))

        Console(width=config.CONSOLE_LOG_WIDTH).print(
            Panel(
                combined,
                title=f'Request Log ({self._context_id})',
                border_style='magenta',
                padding=1,
            )
        )


class contextualize(contextualize_request):
    """
    Context manager which creates a modified contextual logger which
    captures a scoped executions logs and displays them in a formatted
    Panel.
    
    >>> with contextualize() as (contextualization, log):
    >>>     log.info('Hello, world!')
    >>>     contextualization.log_execution()
    """

    PANEL_MARGIN: ClassVar[int] = 2

    def __init__(self) -> None:
        self._context_id = uuid4().hex[:8]
        self._logger = _global_log
        self._log_buffer: list[str] = []
        self._start_time = current_time()
        self._last_message_time = current_time()
        self._sink_id: int | None = None

    def log_execution(self) -> None:
        """
        Log the execution of the scoped code. This displays a panel of
        log messages, if any occured.
        """

        if (logs_panel := self._get_logs_panel()) is None:
            return None

        Console(width=config.CONSOLE_LOG_WIDTH).print(logs_panel)


# IMPORTANT
# Rebind the global `log` variable to a "class" which always resolves to
# the contextualized logger for the current scope
class ContextLogProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_contextualized_logger(), name)

if TYPE_CHECKING:
    log = _global_log
else:
    log = ContextLogProxy()
