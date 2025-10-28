from collections.abc import Awaitable
from typing import Callable

from fastapi import Request, Response
from starlette.datastructures import MutableHeaders


async def convert_cookie_to_oath2_headers(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
    """
    Middleware for all HTTP requests that converts `request`'s
    `tcm_token` Cookie into the required OAuth2 `Authorization: Bearer
    {token}` header (if not present). This is done so that a Cookie can
    be used in place of the header, while still using the OAuth2
    Dependency injection methods.
    """

    # Turn tcm_token Cookie into the appropriate access token OAuth2 Header
    if request.headers.get('Authorization') is None:
        tcm_cookie = request.cookies.get('tcm_token')
        headers = MutableHeaders(request._headers) # pylint: disable=protected-access
        headers['Authorization'] = f'Bearer {tcm_cookie}'
        request._headers = headers # pylint: disable=protected-access
        request.scope.update(headers=request.headers.raw)

    response = await call_next(request)

    if (origin := request.headers.get('Origin')):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'

    return response 
