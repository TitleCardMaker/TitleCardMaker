from collections.abc import Awaitable
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import RedirectResponse

from app.logging.logger import log


async def redirect_non_api_401_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Redirect all non-API unauthenticated 401 requests to the login page.
    """

    # Perform request
    response: Response = await call_next(request)

    # If status code is 401 and this is a non-API request, redirect to login
    if response.status_code == 401 and not request.url.path.startswith('/api'):
        log.debug(f'Redirecting unauthenticated request to "{request.url}"')
        return RedirectResponse(url=f'/login?redirect={request.url.path}')

    return response
