from collections.abc import Awaitable
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import RedirectResponse


async def redirect_non_api_404_requests(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
    """
    Redirect all non-API invalid requests to missing pages/endpoints to
    the home page.
    """

    # Perform request
    response: Response = await call_next(request)

    # If status code is 404 and this is a non-API request, redirect to root
    if response.status_code == 404 and not request.url.path.startswith('/api'):
        return RedirectResponse(url='/')

    return response 
