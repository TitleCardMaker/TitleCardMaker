from collections.abc import Awaitable
from http import HTTPStatus
from time import time as current_time
from typing import Callable

from fastapi import Request, Response

from app.logging.logger import contextualize


async def contextualize_api_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Middleware for all HTTP requests that logs the start and end of all
    API requests to the API logger. This also adds a contextualized
    logger to Request's state `log` attribute.
    """

    # Add contextualized logger to Request state
    log_ = contextualize()
    request.state.log = log_

    def _decorate_url(url: str) -> bool:
        return (
            url.startswith('/api/')
            and not url.startswith(
                ('/api/v2/statistics/series', '/api/v2/proxy/')
            )
            and url not in (
                '/api/v2/logs/query',
                '/api/v2/healthcheck',
                '/api/v2/statistics'
            )
        )

    # Decorate start and end of all API requests
    if _decorate_url(request.url.path):
        # Log request start
        log_.trace(
            f'Starting {request.method} "{request.url.path}'
            f'?{request.query_params}"'
        )
        start_time = current_time()

        # Perform request
        response = await call_next(request)

        # Log end of request
        status = f'({response.status_code}'
        if response.status_code in HTTPStatus._value2member_map_:
            status += f' {HTTPStatus(response.status_code).phrase}'
        log_.trace(
            f'Finished in {(current_time() - start_time)*1000:.1f}ms {status})'
        )
    # Non-API request, just call and return
    else:
        response = await call_next(request)

    return response 
