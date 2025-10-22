from collections.abc import Awaitable
from io import StringIO
from typing import Callable

from fastapi import Request, Response
from rich.console import Console
from rich.traceback import Traceback

from app.logging.logger import log
import modules.BackgroundTasks


async def log_internal_server_errors(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
    """
    Middleware to log "enhanced" tracebacks for all uncaught exceptions
    (e.g. internal server errors). This middleware MUST be the last one
    added to the application.
    """

    # Perform request
    try:
        response = await call_next(request)
    except Exception as exc:
        output = StringIO()
        console = Console(file=output)
        console.print(
            Traceback(
                show_locals=True,
                locals_max_length=512,
                locals_max_string=512,
                extra_lines=2,
                indent_guides=False,
                suppress=modules.BackgroundTasks.TracebackSuppressedPackages,
            )
        )
        # Try and use contextual logger if attached to Request state
        getattr(request.state, 'log', log).exception(
            f'Internal Server Error\n{output.getvalue()}'
        )
        raise exc

    return response 
