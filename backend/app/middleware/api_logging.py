from collections.abc import Awaitable
from pathlib import Path
from time import time as current_time
from typing import TYPE_CHECKING, Callable
from uuid import uuid4

from fastapi import Request, Response
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from app.logging.logger import contextualize_request
from app.settings import settings

if TYPE_CHECKING:
    from loguru import Message


def _should_decorate_request(request: Request) -> bool:
    return (
        request.url.path.startswith('/api/')
        and not request.url.path.startswith(
            ('/api/v2/statistics/series', '/api/v2/proxy/')
        )
        and request.url.path not in (
            '/api/v2/logs/query',
            '/api/v2/healthcheck',
            '/api/v2/statistics'
        )
    )


async def contextualize_api_requests(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
    """
    Middleware for all HTTP requests that logs the start and end of all
    API requests to the API logger. This also adds a contextualized
    logger to Request's state `log` attribute.
    """

    # No decoration necessary, call and return
    if not _should_decorate_request(request):
        return await call_next(request)

    response = Response()
    with contextualize_request(request) as (api_contextualization, _):
        response = await call_next(request)
        api_contextualization.log_response(response)

    return response
