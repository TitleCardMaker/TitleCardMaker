from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import paginate as paginate_sequence
from sqlalchemy import not_
from sqlalchemy.orm import Session, load_only

from app.db.pagination import Page
from app.dependencies import (
    AnyInterface,
    EmbyInterface,
    JellyfinInterface,
    PlexInterface,
    SonarrInterface,
    get_database,
    get_logger,
    get_preferences,
    require_interface,
)
from app.db.users import get_current_user
from app.models.card import Card as CardModel
from app.models.episode import Episode as EpisodeModel
from modules.preferences import Preferences
from app.models.series import Series as SeriesModel
from app.schemas.episode import ReducedEpisodeData
from app.schemas.series import SearchResult, Series
from app.logging.logger import Logger

# Create sub router for all /fonts API requests
missing_router = APIRouter(
    prefix='/missing',
    tags=['Missing'],
    dependencies=[Depends(get_current_user)],
)


@missing_router.get('/cards')
def get_missing_cards(
        db: Session = Depends(get_database),
    ) -> Page[ReducedEpisodeData]: # type: ignore
    """Get all the Episodes that do not have any associated Cards."""

    return paginate(
        db.query(EpisodeModel)\
            .options(
                load_only(
                    EpisodeModel.id,
                    EpisodeModel.series_id,
                    EpisodeModel.season_number,
                    EpisodeModel.episode_number,
                    EpisodeModel.title,
                ),
            )
            .outerjoin(EpisodeModel.series)
            .filter(not_(EpisodeModel.id.in_(
                db.query(CardModel.episode_id).distinct()
            )))
    )


@missing_router.get('/logos')
def get_missing_logos(
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> list[Series]:
    """Get all Series which do not have an associated logo."""

    # Get all source subfolders
    source_directory = preferences.source_directory
    directories = set(source_directory.glob('*'))

    # Get set of series names with no logos
    missing_logos = [
        directory.name.rsplit(' ', maxsplit=1)[0]
        for directory in
        # Find directories which do not have a logo file
        directories - set(
            folder.parent for folder in source_directory.glob('*/logo.png')
        )
        if ' ' in directory.name
    ]

    return [
        series
        for series in db.query(SeriesModel)\
            .filter(SeriesModel.name.in_(missing_logos))\
            .all()
        if not (source_directory / series.path_safe_name / 'logo.png').exists()
    ]


@missing_router.get('/series')
def get_missing_series(
        db: Session = Depends(get_database),
        interface: AnyInterface = Depends(require_interface),
        log: Logger = Depends(get_logger),
    ) -> Page[SearchResult]: # type: ignore
    """Get a list of Series which are not added to the Database."""

    if not isinstance(
        interface,
        (EmbyInterface, JellyfinInterface, PlexInterface, SonarrInterface)
    ):
        raise HTTPException(
            status_code=400,
            detail='Interface type not supported'
        )

    missing_series: list[SearchResult] = []
    for result in interface.query_series(query='', return_all=True, log=log):
        series = db.query(SeriesModel)\
            .filter(result.series_info.filter_conditions(SeriesModel))\
            .first()

        if not series:
            missing_series.append(result)

    return paginate_sequence(missing_series)
