from typing import Literal

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Query,
)
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, load_only

from app.core.cards import delete_cards, refresh_remote_card_types
from app.core.episodes import (
    refresh_episode_data,
    set_episode_ids,
    update_episode_config,
)
from app.db.query import (
    get_all_templates,
    get_connection,
    get_episode,
    get_series
)
from app.db.pagination import Page
from app.dependencies import (
    get_database,
    get_emby_interfaces,
    get_jellyfin_interfaces,
    get_plex_interfaces,
    InterfaceGroup,
)
from app.dependencies import get_logger
from app.db.users import get_current_user
from app.interfaces.v2 import (
    EmbyInterface,
    JellyfinInterface,
    PlexInterface,
)
from app.logging.logger import Logger
from app.models.card import Card
from app.models.episode import Episode as EpisodeModel
from app.models.loaded import Loaded
from app.models.series import Series
from app.schemas.episode import (
    BatchUpdateEpisode,
    Episode,
    EpisodeData,
    EpisodeOverview,
    ExtendedEpisodeData,
    NewEpisode,
    ReducedEpisodeData,
    SimplifiedEpisodeData,
    UpdateEpisode
)


episodes_router = APIRouter(
    prefix='/episodes',
    tags=['Episodes'],
    dependencies=[Depends(get_current_user)],
)


@episodes_router.post('/new')
def add_new_episode(
        new_episode: NewEpisode = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> Episode:
    """
    Add a new episode to the given series.

    - series_id: Series to add the episode to.
    - new_episode: NewEpisode to add.
    """

    # Verify Series exists
    series = get_series(db, new_episode.series_id, raise_exc=True)

    # Get dictionary of object and all associated Templates
    new_episode_dict = new_episode.dict()
    templates = get_all_templates(db, new_episode_dict)

    # Create new entry, add to database
    episode = EpisodeModel(**new_episode_dict)
    db.add(episode)
    db.commit()

    # Assign Templates
    episode.assign_templates(templates, log=log)
    db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    # Add ID's for this Episode
    set_episode_ids(db, series, [episode], log=log)

    return episode


@episodes_router.get('/episode/{episode_id}')
def get_episode_by_id(
        episode_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> Episode:
    """
    Get the Episode with the given ID.

    - episode_id: ID of the Episode to retrieve.
    """

    return get_episode(db, episode_id, raise_exc=True)


@episodes_router.get('/search')
def search_episodes(
        search: str = Query(..., min_length=1),
        db: Session = Depends(get_database),
    ) -> Page[ReducedEpisodeData]: # type: ignore
    """
    Search for Episodes by Series name OR Episode title.

    - search: Search string to query against Series name or Episode title.
    """

    # Query episodes with a join to Series
    query = (
        db.query(EpisodeModel)
            .options(
                load_only(
                    EpisodeModel.id,
                    EpisodeModel.series_id,
                    EpisodeModel.season_number,
                    EpisodeModel.episode_number,
                    EpisodeModel.title,
                ),
                joinedload(EpisodeModel.series).load_only(
                    Series.name,
                ),
            )
            .join(Series)
            .filter(
                or_(
                    EpisodeModel.title.ilike(f'%{search}%'),
                    Series.name.ilike(f'%{search}%'),
                )
            )
            .order_by(
                Series.sort_name,
                EpisodeModel.season_number,
                EpisodeModel.episode_number,
            )
    )

    return paginate(query)


@episodes_router.delete('/episode/{episode_id}')
def delete_episode(
        episode_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Delete the Episode with the ID.

    - episode_id: ID of the Episode to delete.
    """

    # Find Episode with this ID, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Delete card files, Card objects, and Loaded objects
    delete_cards(
        db,
        db.query(Card).filter_by(episode_id=episode_id),
        db.query(Loaded).filter_by(episode_id=episode_id),
        log=log,
    )

    # Delete Episode itself
    db.delete(episode)
    db.commit()


@episodes_router.delete('/series/{series_id}', tags=['Series'])
def delete_all_series_episodes(
        series_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> list[int]:
    """
    Delete all Episodes for the Series with the given ID.

    - series_id: ID of the Series to delete the Episodes of.
    """

    # Get list of Episode ID's to delete
    query = db.query(EpisodeModel).filter_by(series_id=series_id)
    deleted = [episode.id for episode in query]

    # Delete card files, Card objects, and Loaded objects
    delete_cards(
        db,
        db.query(Card).filter_by(series_id=series_id),
        db.query(Loaded).filter_by(series_id=series_id),
        log=log,
    )

    # Delete all associated Episodes
    query.delete()
    db.commit()

    return deleted


@episodes_router.post('/series/{series_id}/refresh')
def refresh_episode_data_(
        series_id: int,
        db: Session = Depends(get_database),
        refresh_all_ids: bool = Query(default=True),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Refresh the episode data associated with the given series. This
    queries the series' episode data source for any new episodes, and
    returns all the series episodes.

    - series_id: Series whose episode data to refresh.
    - refresh_all_ids: Whether to refresh the Episode ID's of ALL
    episodes after querying data or just NEW Episodes.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    refresh_episode_data(
        db,
        series,
        refresh_all_ids=refresh_all_ids,
        log=log
    )


@episodes_router.patch('/batch')
def update_multiple_episode_configs(
        update_episodes: list[BatchUpdateEpisode] = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> list[Episode]:
    """
    Update all the Epiodes at once. Only provided fields are updated.

    - update_episodes: List of BatchUpdateEpisode containing fields to
    update.
    """

    # Update each Episode in the list
    episodes, changed = [], False
    for update_obj in update_episodes:
        # Get this Episode, raise 404 if DNE
        episode = get_episode(db, update_obj.episode_id, raise_exc=True)

        # Apply changes
        changed |= update_episode_config(
            db, episode, update_obj.update_episode, log=log
        )

        # Append updated Episode
        episodes.append(episode)

    # If any values were changed, commit to database; refresh card types
    if changed:
        db.commit()
        refresh_remote_card_types(db, log=log)

    return episodes


@episodes_router.patch('/episode/{episode_id}')
def update_episode_config_(
        episode_id: int,
        update_episode: UpdateEpisode = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> Episode:
    """
    Update the Epiode with the given ID. Only provided fields are
    updated.

    - episode_id: ID of the Episode to update.
    - update_episode: UpdateEpisode containing fields to update.
    """

    # Get this Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # If any values were changed, commit to database
    if update_episode_config(db, episode, update_episode, log=log):
        db.commit()

        # Refresh card types in case new remote type was specified
        refresh_remote_card_types(db, log=log)

    return episode


@episodes_router.get('/series/{series_id}', tags=['Series'], deprecated=True)
def get_all_series_episodes(
        series_id: int,
        order_by: Literal['index', 'absolute', 'id'] = 'index',
        db: Session = Depends(get_database),
    ) -> Page[Episode]: # type: ignore
    """
    Get all the episodes associated with the given series.

    - series_id: Series being queried.
    - order_by: How to order the returned episodes.
    """

    # Query for Episodes of this Series
    query = db.query(EpisodeModel).filter_by(series_id=series_id)

    # Order by indicated attribute
    if order_by == 'index':
        sorted_query = query.order_by(EpisodeModel.season_number)\
            .order_by(EpisodeModel.episode_number)
    elif order_by == 'absolute':
        sorted_query = query.order_by(EpisodeModel.absolute_number)
    elif order_by == 'id':
        sorted_query = query

    return paginate(sorted_query)


@episodes_router.get('/series/{series_id}/extended', tags=['Series'])
def get_series_extended_episode_data(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> Page[ExtendedEpisodeData]:
    """
    Get all the episodes associated with the given series. This returns
    the extended episode data for each Episode.

    - series_id: Series being queried.
    """

    return paginate(
        db.query(Episode)
            .filter_by(series_id=series_id)
            .order_by(
                EpisodeModel.season_number,
                EpisodeModel.episode_number,
            )
        )


@episodes_router.get('/series/{series_id}/simplified', tags=['Series'])
def get_series_simplified_episode_data(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> Page[SimplifiedEpisodeData]:
    """
    Get all the episodes associated with the given series. This returns
    the simplified episode data for each Episode.

    - series_id: Series being queried.
    """

    return paginate(
        db.query(EpisodeModel)
            .options(
                load_only(
                    EpisodeModel.id,
                    EpisodeModel.season_number,
                    EpisodeModel.episode_number,
                    EpisodeModel.absolute_number,
                    EpisodeModel.title,
                    EpisodeModel.match_title,
                    EpisodeModel.auto_split_title,
                    EpisodeModel.season_text,
                    EpisodeModel.episode_text,
                    EpisodeModel.hide_season_text,
                    EpisodeModel.hide_episode_text,
                    EpisodeModel.extras,
                    EpisodeModel.translations,
                )
            )
            .filter_by(series_id=series_id)\
            .order_by(
                EpisodeModel.season_number,
                EpisodeModel.episode_number,
            )
    )


@episodes_router.get('/series/{series_id}/overview', tags=['Series'])
def get_series_episode_overview_data(
        series_id: int,
        order_by: Literal['index', 'absolute', 'id'] = 'index',
        db: Session = Depends(get_database),
    ) -> Page[EpisodeOverview]:
    """
    Get all the episodes associated with the given series.

    - series_id: Series being queried.
    - order_by: How to order the returned episodes.
    """

    # Make reduced query
    query = (
        db.query(
            EpisodeModel.id,
            EpisodeModel.series_id,
            EpisodeModel.season_number,
            EpisodeModel.episode_number,
            EpisodeModel.absolute_number,
        )
        .filter_by(series_id=series_id)
    )
    
    # Order by indicated attribute
    if order_by == 'absolute':
        sorted_query = query.order_by(EpisodeModel.absolute_number)
    elif order_by == 'id':
        sorted_query = query
    else:
        sorted_query = query.order_by(
            EpisodeModel.season_number,
            EpisodeModel.episode_number
        )

    return paginate(sorted_query)


@episodes_router.delete('/batch/delete')
def batch_delete_episodes(
        series_ids: list[int] = Body(...),
        delete_title_cards: bool = Query(default=True),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Perform a batch operation to delete all the Episodes, Cards, and
    Loaded queries for all the Series with the given IDs.
    """

    for series in db.query(Series).filter(Series.id.in_(series_ids)).all():
        if delete_title_cards:
            delete_cards(
                db,
                db.query(Card).filter_by(series_id=series.id),
                db.query(Loaded).filter_by(series_id=series.id),
                log=log,
            )
        db.query(EpisodeModel).filter_by(series_id=series.id).delete()
    db.commit()


@episodes_router.get(
    '/series/{series_id}/connection/{interface_id}',
    tags=['Connections'],
)
def get_all_episodes_on_connection(
        series_id: int,
        interface_id: int,
        library_name: str = Query(...),
        db: Session = Depends(get_database),
        emby_interfaces: (
            InterfaceGroup[int, EmbyInterface]
        ) = Depends(get_emby_interfaces),
        jellyfin_interfaces: (
            InterfaceGroup[int, JellyfinInterface]
        ) = Depends(get_jellyfin_interfaces),
        plex_interfaces: (
            InterfaceGroup[int, PlexInterface]
        ) = Depends(get_plex_interfaces),
        log: Logger = Depends(get_logger),
    ) -> list[EpisodeData]:
    """
    Get a list of all episode data for the given Series on the given
    Connection.

    - series_id: ID of the Series whose Episode data to query.
    - interface_id: ID of the Connection to query Episode data from.
    - library_name: Name of the library on the associated Connection to
    look for Episode data within.
    """

    # Get associated Series and Connection
    series = get_series(db, series_id, raise_exc=True)
    connection = get_connection(db, interface_id, raise_exc=True)

    # Verify interface ID was of a valid type
    if connection.interface_type not in ('Emby', 'Jellyfin', 'Plex'):
        raise HTTPException(
            status_code=422,
            detail='Interface ID must correspond to a media server'
        )

    # Get associated Interface from group
    interface, uid_attr = None, None
    if connection.interface_type == 'Emby':
        interface = emby_interfaces[interface_id]
        uid_attr = 'emby_id'
    elif connection.interface_type == 'Jellyfin':
        interface = jellyfin_interfaces[interface_id]
        uid_attr = 'jellyfin_id'
    elif connection.interface_type == 'Plex':
        interface = plex_interfaces[interface_id]
        uid_attr = 'plex_id'

    # Verify interface is available and valid
    if not interface or not interface.active or not uid_attr:
        raise HTTPException(
            status_code=422,
            detail='Interface ID or Connection is invalid'
        )

    return [
        EpisodeData(
            season_number=episode_info.season_number,
            episode_number=episode_info.episode_number,
            title=episode_info.title,
            uid=getattr(episode_info, uid_attr)[interface_id, library_name]
        )
        for episode_info, _ in interface.get_all_episodes(
            library_name,
            series.as_series_info,
            log=log,
        )
    ]
