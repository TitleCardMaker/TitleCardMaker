from fastapi import APIRouter

from .auth import auth_router
from .availability import availablility_router
from .backups import backup_router
from .blueprint import blueprint_router
from .cards import card_router
from .connection import connection_router
from .episodes import episodes_router
from .fonts import font_router
from .imports import import_router
from .logs import log_router
from .missing import missing_router
from .proxy import proxy_router
from .scheduler import scheduler_router
from .series import series_router
from .settings import settings_router
from .sources import source_router
from .statistics import statistics_router
from .sync import sync_router
from .templates import template_router
from .translate import translation_router
from .webhooks import webhook_router


v2_router = APIRouter(prefix='/v2')


for sub_router in [
    auth_router,
    availablility_router,
    backup_router,
    blueprint_router,
    card_router,
    connection_router,
    episodes_router,
    font_router,
    import_router,
    log_router,
    missing_router,
    proxy_router,
    scheduler_router,
    series_router,
    settings_router,
    source_router,
    statistics_router,
    sync_router,
    template_router,
    translation_router,
    webhook_router,
]:
    v2_router.include_router(sub_router)


__all__ = [
    'v2_router',
]
