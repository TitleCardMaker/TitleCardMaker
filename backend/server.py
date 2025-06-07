# ruff: noqa: E402
from collections.abc import Awaitable
from contextlib import asynccontextmanager
from http import HTTPStatus
from io import StringIO
from pathlib import Path
from time import time as current_time
from typing import Callable
from warnings import filterwarnings

filterwarnings('ignore', category=SyntaxWarning)

import asyncio
from dotenv import load_dotenv
load_dotenv()
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import add_pagination
from rich.console import Console
from rich.traceback import Traceback
from sqlalchemy.orm import Session
from starlette.datastructures import MutableHeaders
from starlette.middleware.cors import CORSMiddleware

from app.core.boot import initialize_app, teardown_app
from app.db.query import get_series
from app.dependencies import get_database, get_preferences
from app.db.users import get_current_user
from app.core.font import get_available_fonts
from app.core.logs import clear_log_data
from app.core.schedule import repeat_every
from app.core.settings import get_episode_data_sources
from app.core.templates import get_available_templates
from app.models.connection import Connection
from modules.preferences import Preferences
from app.models.user import User
from app.api.api import api_router, initialize_scheduler
from app.schemas.schedule import Hours
import modules.BackgroundTasks
from modules.Debug import contextualize
from modules.Debug2 import logger as log, ACTIVE_WEBSOCKETS
from modules.cards.available import DEFAULT_BLUR_PROFILES

# Patch rich.pretty.traverse to force no limit on max length/string
# see my issue on rich: https://github.com/Textualize/rich/issues/3301
# Also catch AttributeErrors caused by uninitialized dataclasses - see
# my PR https://github.com/Textualize/rich/pull/3418/
import rich.pretty
ogt = rich.pretty.traverse
def _traverse(_object, max_length=512, max_string=512, max_depth=2):
    try:
        return ogt(_object, 512, 512, max_depth)
    except AttributeError:
        return rich.pretty.Node(value_repr="...")
rich.pretty.traverse = _traverse


# Base directories for mounting into Uvicorn
PROGRAM_ROOT = Path(__file__).parent.parent
FRONTEND_ROOT = PROGRAM_ROOT / 'frontend'
TEMPLATES = Jinja2Templates(directory=FRONTEND_ROOT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """"""

    initialize_app(app)
    yield
    teardown_app(app)


# Create API
app = FastAPI(
    title='TitleCardMaker',
    description='Backend API for TitleCardMaker',
    contact={
        'name': 'Collin Heist',
        'url': 'https://github.com/CollinHeist/',
    },
    swagger_ui_parameters={'operationsSorter': 'method'},
    lifespan=lifespan,
)

add_pagination(app)
app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],  # Your frontend URL
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['*'],
)


@repeat_every(seconds=Hours(24))
def fix_bad_schedules() -> None:
    """
    Repeated function to (re)initialize the scheduler. Also clears the
    log cache.
    """

    initialize_scheduler()
    clear_log_data()


@app.middleware('http')
async def log_internal_server_errors(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """
    Middleware to log "enhanced" tracebacks for all uncaught exceptions
    (e.g. internal server errors). This middleware MUST be the last one
    added to the application (first in file) for the tracebacks to work
    as expected.
    """

    # Perform request
    try:
        response = await call_next(request)
    except HTTPException as exc:
        raise exc
    # Uncaught exceptions MUST be caught in the LAST middleware for local
    # traceback logging to work
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


@app.middleware('http')
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


@app.middleware('http')
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


@app.middleware('http')
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
    log_ = contextualize(log)
    request.state.log = log_

    def _decorate_url(url: str) -> bool:
        return (
            url.startswith('/api/')
            and not url.startswith(
                ('/api/statistics/series', '/api/proxy/')
            )
            and url not in (
                '/api/logs/query', '/api/healthcheck', '/api/statistics'
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


@app.middleware('http')
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


@app.get(
    '/',
    tags=['HTML Pages'],
    dependencies=[Depends(get_current_user)],
)
async def go_to_home_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences),
):
    """Navigate to the home page."""

    return TEMPLATES.TemplateResponse(
        '/pages/home.html',
        {'request': request, 'preferences': preferences}
    )


@app.get('/login', tags=['HTML Pages'])
async def go_to_login_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences),
):
    """Navigate to the login page."""

    return TEMPLATES.TemplateResponse(
        '/pages/login.html',
        {
            'request': request,
            'require_auth': preferences.require_auth,
            'current_version': str(preferences.current_version),
        }
    )


@app.get(
    '/add',
    tags=['HTML Pages'],
    dependencies=[Depends(get_current_user)],
)
async def go_to_add_series_page(
    request: Request,
    db: Session = Depends(get_database),
    preferences: Preferences = Depends(get_preferences),
):
    """Navigate to the add Series page."""

    return TEMPLATES.TemplateResponse(
        '/pages/addSeries.html',
        {
            'request': request,
            'preferences': preferences,
            'all_connections': db.query(Connection).all(),
            'episode_data_sources': get_episode_data_sources(db),
        }
    )


@app.get(
    '/missing',
    tags=['HTML Pages'],
    dependencies=[Depends(get_current_user)],
)
async def go_to_missing_card_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences),
):
    """Navigate to the add missing Card page."""

    return TEMPLATES.TemplateResponse(
        '/pages/missing.html',
        {'request': request, 'preferences': preferences}
    )


@app.get(
    '/connections',
    tags=['HTML Pages', 'Connections'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_connections_page(
    request: Request,
    db: Session = Depends(get_database),
    preferences: Preferences = Depends(get_preferences),
    user: User | None = Depends(get_current_user),
):
    """Navigate to the Connections HTML Page."""

    connections = db.query(Connection).all()

    return TEMPLATES.TemplateResponse(
        '/pages/connections.html',
        {
            'request': request,
            'preferences': preferences,
            'active_username': None if user is None else user.username,
            'connections': connections,
        }
    )


@app.get(
    '/import',
    tags=['HTML Pages', 'Import'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_import_page(
        request: Request,
        preferences: Preferences = Depends(get_preferences),
    ):
    """Navigate to the home page."""

    return TEMPLATES.TemplateResponse(
        '/pages/import.html',
        {'request': request, 'preferences': preferences}
    )


@app.get(
    '/series/{series_id}',
    tags=['HTML Pages', 'Series'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_series_page(
        request: Request,
        series_id: int,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ):
    """Navigate to the Series page for the Series with the given ID."""

    # Redirect to home page if Series DNE
    if (series := get_series(db, series_id, raise_exc=False)) is None:
        return RedirectResponse('/')

    return TEMPLATES.TemplateResponse(
        '/pages/series.html',
        {
            'request': request,
            'series': series, 
            'preferences': preferences,
            'all_connections': db.query(Connection).all(),
            'available_fonts': get_available_fonts(db),
            'available_templates': get_available_templates(db),
            'episode_data_sources': get_episode_data_sources(db),
        }
    )


@app.get(
    '/settings',
    tags=['HTML Pages', 'Settings'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_settings_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences),
):
    """Navigate to the settings page."""

    return TEMPLATES.TemplateResponse(
        '/pages/settings.html',
        {
            'request': request,
            'preferences': preferences,
            'DEFAULT_BLUR_PROFILES': DEFAULT_BLUR_PROFILES,
        }
    )


@app.get(
    '/sync',
    tags=['HTML Pages', 'Sync'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_sync_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences),
):
    """ Navigate to the Syncs page."""

    return TEMPLATES.TemplateResponse(
        '/pages/sync.html',
        {'request': request, 'preferences': preferences}
    )


@app.get(
    '/card-templates',
    tags=['HTML Pages', 'Templates'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_template_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences),
):
    """Navigate to the Templates page."""

    return TEMPLATES.TemplateResponse(
        '/pages/cardTemplates.html',
        {'request': request, 'preferences': preferences}
    )


@app.get(
    '/fonts',
    tags=['HTML Pages', 'Fonts'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_font_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences),
):
    """Navigate to the named Fonts page."""

    return TEMPLATES.TemplateResponse(
        '/pages/fonts.html',
        {'request': request, 'preferences': preferences}
    )


@app.get(
    '/scheduler',
    tags=['HTML Pages', 'Scheduler'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_scheduler_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences),
):
    """Navigate to the scheduler page."""

    return TEMPLATES.TemplateResponse(
        '/pages/scheduler.html',
        {'request': request, 'preferences': preferences}
    )


@app.get(
    '/logs',
    tags=['HTML Pages'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_logs_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences),
):
    """Navigate to the log page."""

    return TEMPLATES.TemplateResponse(
        '/pages/logs.html',
        {'request': request, 'preferences': preferences}
    )


@app.get(
    '/graphs',
    tags=['HTML Pages'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_graphs_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences),
):
    """Navigate to the log page."""

    return TEMPLATES.TemplateResponse(
        '/pages/graphs.html',
        {'request': request, 'preferences': preferences}
    )


@app.get('/scalar', tags=['HTML Pages'])
async def go_to_scalar_docs(request: Request):
    """Navigate to the scalar API docs page."""

    return TEMPLATES.TemplateResponse(
        '/pages/docs_scalar.html',
        {'request': request}
    )


@app.get(
    '/changelog',
    tags=['HTML Pages'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_changelog_page(
    request: Request,
    preferences: Preferences = Depends(get_preferences)
):
    """Navigate to the changelog page."""

    return TEMPLATES.TemplateResponse(
        '/pages/changelog.html',
        {'request': request, 'preferences': preferences}
    )


@app.get('/system', tags=['HTML Pages'],
         dependencies=[Depends(get_current_user)])
async def go_to_system_page(
        request: Request,
        preferences: Preferences = Depends(get_preferences)
    ):
    """Navigate to the system page."""

    return TEMPLATES.TemplateResponse(
        '/pages/system.html',
        {'request': request, 'preferences': preferences}
    )


@app.get(
    '/recent', tags=['HTML Pages'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_recently_added_page(
        request: Request,
        preferences: Preferences = Depends(get_preferences)
    ):
    """Navigate to the recently added page."""

    return TEMPLATES.TemplateResponse(
        '/pages/recent.html',
        {'request': request, 'preferences': preferences}
    )


@app.websocket('/ws/logs')
async def open_log_websocket(
        websocket: WebSocket,
        timeout: int = Query(default=600, min=1),
    ) -> None:
    """
    Open a websocket for all live log messages.

    - timeout: The maximum number of seconds to keep the connection
    alive.
    """

    # Connect
    await websocket.accept()

    # Add to active set so log messages can be sent
    global ACTIVE_WEBSOCKETS
    for connection in list(ACTIVE_WEBSOCKETS):
        try:
            await connection.close()
        # Handle if WebSocket has already been closed
        except RuntimeError:
            pass
        finally:
            ACTIVE_WEBSOCKETS.discard(connection)
    ACTIVE_WEBSOCKETS.add(websocket)

    # Begin permanent connection
    start_time = asyncio.get_event_loop().time()
    try:
        while True:
            await log.complete()
            if asyncio.get_event_loop().time() - start_time > timeout:
                log.trace(f'Closed WebSocket after {timeout} seconds')
                break

            # Keep the Connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        ACTIVE_WEBSOCKETS.discard(websocket)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
