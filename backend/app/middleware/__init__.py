from .api_logging import contextualize_api_requests
from .auth import redirect_non_api_401_requests
from .error_logging import log_internal_server_errors
from .redirect import redirect_non_api_404_requests
from .oauth import convert_cookie_to_oath2_headers


middlewares = [
    log_internal_server_errors, # Must be first
    contextualize_api_requests,
    redirect_non_api_401_requests,
    redirect_non_api_404_requests,
    convert_cookie_to_oath2_headers,
]

__all__ = [
    'middlewares',
]
