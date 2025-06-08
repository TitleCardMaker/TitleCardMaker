# ruff: noqa: E402
from contextlib import asynccontextmanager
from warnings import filterwarnings

filterwarnings('ignore', category=SyntaxWarning)

from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware

from app.api.api import api_router, initialize_scheduler
from app.api.pages import router as pages_router
from app.core.boot import initialize_app, teardown_app
from app.core.schedule import repeat_every
from app.core.logs import clear_log_data
from app.middleware import middlewares
from app.schemas.schedule import Hours

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan for the FastAPI application."""

    initialize_app(app)
    yield
    teardown_app(app)


# Create application
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

# Configure Application by adding Pagination, all API routers, page
# navigation, and CORS middleware
add_pagination(app)
app.include_router(api_router)
app.include_router(pages_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000'],  # Your frontend URL
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    expose_headers=['*'],
)

# Add middleware in the correct order
for middleware in middlewares:
    app.middleware('http')(middleware)


@repeat_every(seconds=Hours(24))
def fix_bad_schedules() -> None:
    """
    Repeated function to (re)initialize the scheduler. Also clears the
    log cache.
    """

    initialize_scheduler()
    clear_log_data()
