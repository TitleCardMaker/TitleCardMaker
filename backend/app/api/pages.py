from pathlib import Path

from app.core.sync import CURRENTLY_RUNNING_SYNC
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.card_registry import DEFAULT_BLUR_PROFILES
from app.core.font import get_available_fonts
from app.core.settings import get_episode_data_sources
from app.core.templates import get_available_templates
from app.db.query import get_series
from app.db.users import get_current_user
from app.dependencies import get_database
from app.logging.logger import log
from app.models.connection import Connection
from app.models.user import User
from app.settings import settings


# Base directories for mounting into Uvicorn
PROGRAM_ROOT = Path(__file__).parent.parent.parent.parent
FRONTEND_ROOT = PROGRAM_ROOT / 'frontend'
TEMPLATES = Jinja2Templates(directory=FRONTEND_ROOT)

router = APIRouter(tags=['HTML Pages'])

@router.get('/', dependencies=[Depends(get_current_user)])
async def go_to_home_page(request: Request):
    """Navigate to the home page."""
    return TEMPLATES.TemplateResponse(
        '/pages/home.html',
        {'request': request, 'preferences': settings}
    )

@router.get('/login')
async def go_to_login_page(request: Request):
    """Navigate to the login page."""
    return TEMPLATES.TemplateResponse(
        '/pages/login.html',
        {
            'request': request,
            'require_auth': settings.require_auth,
            'current_version': str(settings.config.CURRENT_VERSION),
        }
    )

@router.get('/add', dependencies=[Depends(get_current_user)])
async def go_to_add_series_page(
    request: Request,
    db: Session = Depends(get_database),
):
    """Navigate to the add Series page."""

    return TEMPLATES.TemplateResponse(
        '/pages/addSeries.html',
        {
            'request': request,
            'preferences': settings,
            'all_connections': db.query(Connection).all(),
            'episode_data_sources': get_episode_data_sources(db),
        }
    )

@router.get('/missing', dependencies=[Depends(get_current_user)])
async def go_to_missing_card_page(request: Request):
    """Navigate to the add missing Card page."""
    return TEMPLATES.TemplateResponse(
        '/pages/missing.html',
        {'request': request, 'preferences': settings}
    )

@router.get(
   '/connections',
   tags=['Connections'],
   dependencies=[Depends(get_current_user)]
)
async def go_to_connections_page(
    request: Request,
    db: Session = Depends(get_database),
    user: User | None = Depends(get_current_user),
):
    """Navigate to the Connections HTML Page."""
    connections = db.query(Connection).all()
    return TEMPLATES.TemplateResponse(
        '/pages/connections.html',
        {
            'request': request,
            'preferences': settings,
            'active_username': None if user is None else user.username,
            'connections': connections,
        }
    )

@router.get(
    '/import',
    tags=['Import'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_import_page(request: Request):
    """Navigate to the import page."""
    return TEMPLATES.TemplateResponse(
        '/pages/import.html',
        {'request': request, 'preferences': settings}
    )

@router.get(
    '/series/{series_id}',
    tags=['Series'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_series_page(
    series_id: int,
    request: Request,
    db: Session = Depends(get_database),
):
    """Navigate to the Series page for the Series with the given ID."""
    if (series := get_series(db, series_id, raise_exc=False)) is None:
        return RedirectResponse('/')

    return TEMPLATES.TemplateResponse(
        '/pages/series.html',
        {
            'request': request,
            'series': series, 
            'preferences': settings,
            'all_connections': db.query(Connection).all(),
            'available_fonts': get_available_fonts(db),
            'available_templates': get_available_templates(db),
            'episode_data_sources': get_episode_data_sources(db),
        }
    )

@router.get(
    '/settings',
    tags=['Settings'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_settings_page(request: Request):
    """Navigate to the settings page."""
    return TEMPLATES.TemplateResponse(
        '/pages/settings.html',
        {
            'request': request,
            'preferences': settings,
            'DEFAULT_BLUR_PROFILES': DEFAULT_BLUR_PROFILES,
        }
    )

@router.get(
    '/sync',
    tags=['Sync'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_sync_page(request: Request):
    """Navigate to the Syncs page."""
    return TEMPLATES.TemplateResponse(
        '/pages/sync.html',
        {
            'request': request,
            'preferences': settings,
            'currently_running_sync': CURRENTLY_RUNNING_SYNC,
        }
    )

@router.get(
    '/card-templates',
    tags=['Templates'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_template_page(request: Request):
    """Navigate to the Templates page."""
    return TEMPLATES.TemplateResponse(
        '/pages/cardTemplates.html',
        {'request': request, 'preferences': settings}
    )

@router.get(
    '/fonts',
    tags=['Fonts'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_font_page(request: Request):
    """Navigate to the named Fonts page."""
    return TEMPLATES.TemplateResponse(
        '/pages/fonts.html',
        {'request': request, 'preferences': settings}
    )

@router.get(
    '/scheduler',
    tags=['Scheduler'],
    dependencies=[Depends(get_current_user)]
)
async def go_to_scheduler_page(request: Request):
    """Navigate to the scheduler page."""
    return TEMPLATES.TemplateResponse(
        '/pages/scheduler.html',
        {'request': request, 'preferences': settings}
    )

@router.get(
    '/logs',
    dependencies=[Depends(get_current_user)]
)
async def go_to_logs_page(request: Request):
    """Navigate to the log page."""
    return TEMPLATES.TemplateResponse(
        '/pages/logs.html',
        {'request': request, 'preferences': settings}
    )

@router.get('/graphs', dependencies=[Depends(get_current_user)])
async def go_to_graphs_page(request: Request):
    """Navigate to the graphs page."""
    return TEMPLATES.TemplateResponse(
        '/pages/graphs.html',
        {'request': request, 'preferences': settings}
    )

@router.get('/scalar')
async def go_to_scalar_docs(request: Request):
    """Navigate to the scalar API docs page."""
    return TEMPLATES.TemplateResponse(
        '/pages/docs_scalar.html',
        {'request': request}
    )

@router.get('/changelog', dependencies=[Depends(get_current_user)])
async def go_to_changelog_page(request: Request):
    """Navigate to the changelog page."""
    return TEMPLATES.TemplateResponse(
        '/pages/changelog.html',
        {'request': request, 'preferences': settings}
    )

@router.get('/system', dependencies=[Depends(get_current_user)])
async def go_to_system_page(request: Request):
    """Navigate to the system page."""
    return TEMPLATES.TemplateResponse(
        '/pages/system.html',
        {'request': request, 'preferences': settings}
    )

@router.get(
    '/recent',
    dependencies=[Depends(get_current_user)]
)
async def go_to_recently_added_page(request: Request):
    """Navigate to the recently added page."""
    return TEMPLATES.TemplateResponse(
        '/pages/recent.html',
        {'request': request, 'preferences': settings}
    )
