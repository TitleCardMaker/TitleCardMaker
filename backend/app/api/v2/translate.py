from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.db.query import get_episode, get_series
from app.dependencies import get_database, get_logger, require_tvdb_interface
from app.db.users import get_current_user
from app.core.translate import translate_episode
from app.schemas.episode import Episode
from modules.Debug import Logger
from modules.TVDbInterface import TVDbInterface


translation_router = APIRouter(
    prefix='/translate',
    tags=['Translations'],
    dependencies=[Depends(get_current_user)],
)


@translation_router.get('/series/{series_id}/season-titles')
def get_series_season_titles(
        series_id: int,
        tvdb_interface: TVDbInterface = Depends(require_tvdb_interface),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> dict[str, dict[int, str]]:
    """
    Query possible season titles from TVDb for the given Series.

    - series_id: ID of the Series to query titles of.
    - tvdb_interface_id: ID of the TVDb Connection to query titles from.
    """

    return tvdb_interface.get_season_titles(
        get_series(db, series_id, raise_exc=True).as_series_info,
        log=log
    )


@translation_router.post('/series/{series_id}')
def add_series_translations(
        background_tasks: BackgroundTasks,
        series_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Get all translations for all Episodes of the given Series.

    - series_id: ID of the Series whose Episodes are being translated.
    """

    for episode in get_series(db, series_id, raise_exc=True).episodes:
        background_tasks.add_task(translate_episode, db, episode, log=log)


@translation_router.post('/episode/{episode_id}')
def add_episode_translations(
        episode_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> Episode:
    """
    Get all translations for the given Episode.

    - episode_id: ID of the Episode to translate.
    """

    # Find this Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Translate this Episode
    translate_episode(db, episode, log=log)

    return episode
