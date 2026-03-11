from collections.abc import Awaitable
from typing import Callable

from fastapi import Request, Response

from app.logging.logger import contextualize_request


def _should_decorate_request(request: Request) -> bool:
    """Determine if the request should be decorated with API logging."""

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
    API requests to the API logger. This wraps the request in a
    contextualized logger context (if necessary)
    """

    # No decoration necessary, call and return
    if not _should_decorate_request(request):
        return await call_next(request)

    response = Response()
    with contextualize_request(request) as (api_contextualization, logger):
        response = await call_next(request)
        api_contextualization.log_response(response)
        duration = (
            api_contextualization._last_message_time
            - api_contextualization._request_start_time
        )
        logger.trace((
            f'Request {request.method} {request.url.path} took '
            f'{duration:.1f}ms ({response.status_code})'
        ))

    return response
