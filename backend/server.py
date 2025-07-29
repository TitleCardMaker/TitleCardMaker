# ruff: noqa: E402
from contextlib import asynccontextmanager
from warnings import filterwarnings

filterwarnings('ignore', category=SyntaxWarning)

from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.api.pages import router as pages_router
from app.core.boot import initialize_app, initialize_huey, teardown_app, teardown_huey
from app.middleware import middlewares

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
    consumer, task = initialize_huey()

    yield

    teardown_app(app)
    await teardown_huey(consumer, task)


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

# Configure Application by adding pagination, all API routers, and page
# navigation
add_pagination(app)
app.include_router(api_router)
app.include_router(pages_router)

# Add middleware in the correct order
for middleware in middlewares:
    app.middleware('http')(middleware)
