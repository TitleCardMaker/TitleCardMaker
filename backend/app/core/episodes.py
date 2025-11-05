from collections.abc import Iterable
from pathlib import Path

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session, load_only

from app.db.query import (
    get_all_templates,
    get_font,
    get_interface,
)
from app.dependencies import (
    get_sonarr_interfaces,
    get_tmdb_interfaces,
    get_tvdb_interfaces
)
from app.core.templates import get_effective_templates
from app.info.episode import EpisodeInfo
from app.interfaces.base import WatchedStatus
from app.interfaces.v2 import (
    SonarrInterface,
    TMDbInterface,
    TVDbInterface,
)
from app.logging.logger import Logger, log
from app.models.card import Card
from app.models.episode import Episode
from app.models.series import Series
from app.schemas.base import UNSPECIFIED
from app.schemas.episode import UpdateEpisode
from app.schemas.schedule import Hours
from app.settings import settings
from app.utils.tiered_settings import TieredSettings


def set_episode_ids(
        db: Session,
        series: Series,
        episodes: Iterable[Episode],
        *,
        log: Logger = log,
    ) -> None:
    """
    Set the database IDs of the given Episodes.

    Args:
        db: Database to read/update/modify.
        series: Series of the Episodes whose IDs are being set.
        episodes: Any Episodes to set the IDs of.
        log: Logger for all log messages.
    """

    # Get corresponding EpisodeInfo object for this Episode
    episode_infos = [episode.as_episode_info for episode in episodes]

    # Set ID's from all library interfaces
    for library in series.libraries:
        if (interface := get_interface(library['interface_id'], raise_exc=False)):
            interface.set_episode_ids(
                library['name'], series.as_series_info, episode_infos, log=log,
            )
        else:
            log.debug(
                f'Skipping Library "{library["name"]}" - no applicable interface'
            )

    # Set from Sonarr, only do for Connections which have a Sonarr ID
    for _, interface in get_sonarr_interfaces():
        if not series.as_series_info.has_id('sonarr_id', interface.interface_id):
            continue
        interface.set_episode_ids(
            None, series.as_series_info, episode_infos, log=log
        )

    # Set from the first TMDb and TVDb Connection
    for _, interface in get_tmdb_interfaces():
        interface.set_episode_ids(
            None, series.as_series_info, episode_infos, log=log
        )
        break
    for _, interface in get_tvdb_interfaces():
        interface.set_episode_ids(
            None, series.as_series_info, episode_infos, log=log
        )
        break

    # Update database if new ID's are available
    changed = False
    for episode, episode_info in zip(episodes, episode_infos):
        changed |= episode.update_ids_from_info(episode_info, log=log)

    # Write any changes to the DB
    if changed:
        db.commit()


def get_all_episode_data(
        series: Series,
        *,
        raise_exc: bool = True,
        log: Logger = log,
    ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
    """
    Get all EpisodeInfo for the given Series from it's indicated Episode
    data source.

    Args:
        series: Series whose Episode data is being queried.
        raise_exc: Whether to raise any HTTPExceptions caused by
            disabled interfaces or missing libraries.
        log: Logger for all log messages.

    Returns:
        List of tuples of the EpisodeInfo from the given Series' episode
        data source and the WatchedStatus for that Episode. If the data
        cannot be queried and `raise_exc` is False, then an empty list
        is returned.

    Raises:
        HTTPException (404): A Series' Template does not exist.
        HTTPException (409): The indicated Episode Data Source cannot be
            communicated with.
    """

    # Determine effective Episode data source
    g_template, s_template, _ = get_effective_templates(series)
    interface_id = TieredSettings.resolve_singular_setting(
        settings.episode_data_source,
        getattr(g_template, 'data_source_id', None),
        getattr(s_template, 'data_source_id', None),
        series.data_source_id,
    )

    # No assigned Episode Data Source
    if interface_id is None:
        raise HTTPException(
            status_code=409,
            detail='No assigned Episode Data Source',
        )

    # Raise 409 if cannot communicate with the Series' Episode data source
    if (interface := get_interface(interface_id, raise_exc=False)) is None:
        log.error(
            f'Unable to communicate with Episode Data Source ([{interface_id}])'
        )
        if raise_exc:
            raise HTTPException(
                status_code=409,
                detail=f'Unable to communicate with Connection[{interface_id}]'
            )
        return []

    # Query Connections which do not have libraries
    if isinstance(interface, (SonarrInterface, TMDbInterface, TVDbInterface)):
        return interface.get_all_episodes('', series.as_series_info, log=log)

    # Verify Series has an associated Library if EDS is a media server
    if not (libraries := list(series.get_libraries(interface_id))):
        log.error(
            'Series does not have a Library for the assigned Episode Data Source'
        )
        if raise_exc:
            raise HTTPException(
                status_code=409,
                detail=f'Series does not have a Library for Connection[{interface_id}]'
            )
        return []

    # Get Episodes from the Series' first (primary) library
    return interface.get_all_episodes(
        libraries[0][1], series.as_series_info, log=log
    )


def refresh_episode_data(
        db: Session,
        series: Series,
        background_tasks: BackgroundTasks | None = None,
        *,
        refresh_all_ids: bool = False,
        log: Logger = log,
    ) -> list[Episode]:
    """
    Refresh the episode data for the given Series. This adds any new
    Episodes on the associated episode data source to the Database,
    updates the titles of any existing Episodes (if indicated), and
    assigns the database ID's of all added/modified Episodes.

    Args:
        db: Database to read/update/modify.
        series: Series whose episodes are being refreshed.
        background_tasks: Optional BackgroundTasks queue to add the
            Episode ID assignment task to, if provided. If omitted then
            the assignment is done in a blocking manner.
        refresh_all_ids: Whether to refresh all Episode ID's, not just
            those of new Episodes, after querying data.
        log: Logger for all log messages.

    Returns:
        List of any newly added Episodes. Empty list of no new Episodes
        were added, or only existing Episodes were modified.

    Raises:
        HTTPException (404): A Series Template does not exist.
        HTTPException (409): The indicted Episode data source cannot
            be communicated with.
    """

    # Get all Episodes for this Series from the Episode data source
    all_episodes = get_all_episode_data(series, raise_exc=True, log=log)

    # Get effective sync specials toggle
    global_template, series_template, _ = get_effective_templates(series)
    sync_specials = TieredSettings.resolve_singular_setting(
        settings.sync_specials,
        getattr(global_template, 'sync_specials', None),
        getattr(series_template, 'sync_specials', None),
        series.sync_specials,
    )

    # Filter Episodes
    new_episodes: list[Episode] = []
    changed = False
    for episode_info, watched in all_episodes:
        # Skip specials if indicated
        if not sync_specials and episode_info.season_number == 0:
            log.trace(f'{series} skipping {episode_info} - specials disabled')
            continue

        # Check if this Episode exists in the database already
        existing = db.query(Episode)\
            .filter(Episode.series_id == series.id,
                    episode_info.filter_conditions(Episode))\
            .first()

        # Episode does not exist, add
        if existing is None:
            episode = Episode(
                series=series,
                title=episode_info.title,
                **episode_info.indices,
                **episode_info.ids,
                watched_statuses=watched.as_db_entry,
                airdate=episode_info.airdate,
            )
            db.add(episode)
            changed = True
            new_episodes.append(episode)
        # Episode exists, update metadata and watched statuses
        else:
            changed |= existing.update_metadata_from_info(episode_info, log=log)
            changed |= existing.add_watched_status(watched, log=log)

    # Get existing Episodes
    if settings.delete_missing_episodes:
        new_keys = set(
            ep_info.index_str
            for ep_info, _ in all_episodes
            if sync_specials or ep_info.season_number != 0
        )
        all_existing = {ep.index_str: ep for ep in series.episodes}
        for delete_key in set(all_existing) - new_keys:
            # Delete Title Card(s)
            log.info(
                f'Deleting {all_existing[delete_key]} - not in Episode Data '
                f'Source'
            )
            cards = db.query(Card)\
                .filter_by(episode_id=all_existing[delete_key].id)\
                .all()
            for card in cards:
                if (card_file := Path(card.card_file)).exists():
                    card_file.unlink(missing_ok=True)
                    log.info(f'Deleted "{card_file.resolve()}" Title Card')
                db.delete(card)

            # Delete Episode (also deleted associated Loaded + Card objects)
            db.delete(all_existing[delete_key])
            changed = True

    # Log any new Episodes
    if len(new_episodes) > 1:
        log.info(f'{series} {len(new_episodes)} new Episodes')
    elif len(new_episodes) == 1:
        log.info(f'{series} new Episode "{new_episodes[0].title}"')
    else:
        log.trace(f'{series} has no new Episodes')

    # Set Episode ID's for all/new Episodes
    id_episodes = series.episodes if refresh_all_ids else new_episodes
    if id_episodes:
        if background_tasks is None:
            set_episode_ids(db, series, id_episodes, log=log)
        else:
            background_tasks.add_task(
                set_episode_ids,
                db, series, id_episodes,log=log
            )

    # Commit to database if changed
    if changed:
        db.commit()

    return new_episodes


def update_episode_config(
        db: Session,
        episode: Episode,
        update_episode: UpdateEpisode,
        *,
        log: Logger = log,
    ) -> bool:
    """
    Update the given Episode.

    Args:
        db: Database to query for Fonts or Templates if indicated.
        episode: Episode to update.
        update_episode: Objet detailing which attributes of the given
            Episode to update.
        log: Logger for all log messages.

    Returns:
        True if the given Episode was modified, False otherwise.
    """

    # If any reference ID's were indicated, verify referenced object exists
    update_episode_dict = update_episode.model_dump(exclude_unset=True)
    get_font(db, update_episode_dict.get('font_id'), raise_exc=True)

    # Assign Templates if indicated
    changed = False
    if ((template_ids := update_episode_dict.pop('template_ids', None))
        not in (None, UNSPECIFIED)):
        if episode.template_ids != template_ids:
            templates = get_all_templates(db, update_episode_dict)
            episode.assign_templates(templates, log=log)
            changed = True

    # Update each attribute of the object
    for attr, value in update_episode_dict.items():
        if value != UNSPECIFIED and getattr(episode, attr) != value:
            log.debug(f'Episode[{episode.id}].{attr} = {value}')
            setattr(episode, attr, value)
            changed = True

    return changed


def get_series_episodes_with_cache(
        db: Session,
        series_id: int,
        *,
        log: Logger = log,
    ) -> list[Episode]:
    """
    Get all episodes for a series with caching support.
    
    Args:
        db: Database session
        series_id: ID of the Series whose Episodes are being queried.
        log: Logger for all log messages.
        
    Returns:
        List of Episode objects
    """

    # Get from database
    episodes = db.query(Episode)\
        .filter_by(series_id=series_id)\
        .order_by(Episode.season_number, Episode.episode_number)\
        .all()

    log.debug(f'Retrieved {len(episodes)} episodes for series {series_id} from database')

    return episodes


def get_series_episodes_simplified_with_cache(
        db: Session,
        series_id: int,
        *,
        log: Logger = log,
    ) -> list[dict]:
    """
    Get simplified episode data for a series with caching support.
    
    Args:
        db: Database session
        series_id: Series ID
        log: Logger instance
        
    Returns:
        List of simplified episode data dictionaries
    """
    # Get from database with simplified fields
    episodes = (
        db.query(Episode)
            .options(
                load_only(
                    Episode.id,
                    Episode.season_number,
                    Episode.episode_number,
                    Episode.absolute_number,
                    Episode.title,
                    Episode.match_title,
                    Episode.auto_split_title,
                    Episode.season_text,
                    Episode.episode_text,
                    Episode.hide_season_text,
                    Episode.hide_episode_text,
                    Episode.extras,
                    Episode.translations,
                )
            )
            .filter_by(series_id=series_id)\
            .order_by(Episode.season_number, Episode.episode_number)
            .all()
    )

    # Convert to simplified format
    simplified_episodes = [
        {
            'id': episode.id,
            'season_number': episode.season_number,
            'episode_number': episode.episode_number,
            'absolute_number': episode.absolute_number,
            'title': episode.title,
            'match_title': episode.match_title,
            'auto_split_title': episode.auto_split_title,
            'season_text': episode.season_text,
            'episode_text': episode.episode_text,
            'hide_season_text': episode.hide_season_text,
            'hide_episode_text': episode.hide_episode_text,
            'extras': episode.extras,
            'translations': episode.translations,
        }
        for episode in episodes
    ]

    log.debug(f'Retrieved {len(simplified_episodes)} simplified episodes for series {series_id} from database')

    return simplified_episodes


def get_series_episodes_overview_with_cache(
        db: Session,
        series_id: int,
        order_by: str = 'index',
        *,
        log: Logger = log,
    ) -> list[dict]:
    """
    Get episode overview data for a series with caching support.
    
    Args:
        db: Database session
        series_id: Series ID
        order_by: How to order the episodes
        log: Logger instance
        
    Returns:
        List of episode overview data dictionaries
    """
    # Get from database with overview fields
    query = db.query(
        Episode.id,
        Episode.series_id,
        Episode.season_number,
        Episode.episode_number,
        Episode.absolute_number,
    ).filter_by(series_id=series_id)
    
    # Order by indicated attribute
    if order_by == 'index':
        sorted_query = query.order_by(Episode.season_number, Episode.episode_number)
    elif order_by == 'absolute':
        sorted_query = query.order_by(Episode.absolute_number)
    elif order_by == 'id':
        sorted_query = query
    else:
        sorted_query = query.order_by(Episode.season_number, Episode.episode_number)
    
    episodes = sorted_query.all()
    
    # Convert to overview format
    overview_episodes = [
        {
            'id': episode.id,
            'series_id': episode.series_id,
            'season_number': episode.season_number,
            'episode_number': episode.episode_number,
            'absolute_number': episode.absolute_number,
        }
        for episode in episodes
    ]
    
    log.debug(f'Retrieved episode overview for series {series_id} from database')
    
    return overview_episodes
