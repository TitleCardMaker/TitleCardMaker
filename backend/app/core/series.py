from pathlib import Path
from time import sleep
from typing import Any, Callable

from fastapi import BackgroundTasks, HTTPException
from fastapi_pagination.ext.sqlalchemy import paginate
from PIL import Image, UnidentifiedImageError
from requests import get
from sqlalchemy import ColumnElement, String, cast, desc, func, not_
from sqlalchemy.exc import InvalidRequestError, OperationalError
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Query,
    Session,
    load_only,
)

from app.db.query import (
    get_all_templates,
    get_connection,
    get_font,
    get_interface,
    get_media_interface,
    get_sync,
)
from app.db.pagination import Page
from app.dependencies import (
    get_database,
    get_preferences,
    get_sonarr_interfaces,
    get_tmdb_interfaces,
    get_tvdb_interfaces
)
from app.core.cards import (
    create_episode_cards,
    get_watched_statuses,
    refresh_remote_card_types
)
from app.core.episodes import refresh_episode_data
from app.core.sources import (
    download_episode_source_images,
    download_series_logo,
)
from app.core.translate import translate_episode
from app.models.card import Card
from app.models.episode import Episode
from app.models.loaded import Loaded
from app.models.series import Series
from app.schemas.base import UNSPECIFIED
from app.interfaces.v2 import (
    EpisodeDataSourceInterface,
    EmbyInterface,
    JellyfinInterface,
    PlexInterface,
)
from app.schemas.filter import SeriesFilter
from app.schemas.series import (
    NewSeries,
    SearchResult,
    SeriesOrder,
    SeriesOverview,
    SeriesOverviewWithCounts,
    UpdateSeries
)
from app.logging.logger import Logger, log


"""
Dictionary of condition field names to attributes of the Series
model/object which should be filtered.
"""
ConditionFieldAttributes: dict[str, InstrumentedAttribute[Any]] = {
    'auto_split_titles': Series.auto_split_title,
    'card_filename_format': Series.card_filename_format,
    'card_type': Series.card_type,
    'data_source_id': Series.data_source_id,
    'directory': Series.directory,
    'emby_id': Series.emby_id,
    'episode_text_format': Series.episode_text_format,
    'extras': Series.extras,
    'font_color': Series.font_color,
    'font_id': Series.font_id,
    'font_interline_spacing': Series.font_interline_spacing,
    'font_interword_spacing': Series.font_interword_spacing,
    'font_kerning': Series.font_kerning,
    'font_size': Series.font_size,
    'font_stroke_width': Series.font_stroke_width,
    'font_title_case': Series.font_title_case,
    'font_vertical_shift': Series.font_vertical_shift,
    'hide_episode_text': Series.hide_episode_text,
    'hide_season_text': Series.hide_season_text,
    'id': Series.id,
    'image_source_priority': Series.image_source_priority,
    'imdb_id': Series.imdb_id,
    'jellyfin_id': Series.jellyfin_id,
    'libraries': Series.libraries,
    'match_titles': Series.match_titles,
    # 'missing_cards': ..., # This must be handled separately
    'status': Series.status,
    'name': Series.name,
    'season_titles': Series.season_titles,
    'skip_localized_images': Series.skip_localized_images,
    'sonarr_id': Series.sonarr_id,
    'sync_id': Series.sync_id,
    'sync_specials': Series.sync_specials,
    'tmdb_id': Series.tmdb_id,
    'translations': Series.translations,
    'tvdb_id': Series.tvdb_id,
    'tvrage_id': Series.tvrage_id,
    'unwatched_style': Series.unwatched_style,
    'use_per_season_assets': Series.use_per_season_assets,
    'watched_style': Series.watched_style,
    'year': Series.year,
}

"""
Dictionary of filter expressions to functions which apply that filter
function to a given Series model attribute and optional filter reference
field.
"""
type _FilterFunction = Callable[
    [InstrumentedAttribute[Any], str | None],
    ColumnElement[bool]
]
ConditionExpressionFunctions: dict[str, _FilterFunction] = {
    'equals': lambda attr, ref: cast(attr, String) == ref,
    'does not equal': lambda attr, ref: cast(attr, String) != ref,
    'contains': lambda attr, ref: attr.contains(ref),
    'does not contain': lambda attr, ref: not_(attr.contains(ref)),
    'starts with': lambda attr, ref: attr.startswith(ref),
    'does not start with': lambda attr, ref: not_(attr.startswith(ref)),
    'ends with': lambda attr, ref: attr.endswith(ref),
    'does not end with': lambda attr, ref: not_(attr.endswith(ref)),
    'matches': lambda attr, ref: func.regex_match(ref, attr),
    'does not match': lambda attr, ref: not_(func.regex_match(ref, attr)),
    'is less than': lambda attr, ref: attr < ref,
    'is less than or equal to': lambda attr, ref: attr <= ref,
    'is greater than': lambda attr, ref: attr > ref,
    'is greater than or equal to': lambda attr, ref: attr >= ref,
    'is null': lambda attr, _: attr.is_(None),
    'is not null': lambda attr, _: attr.isnot(None),
    'is true': lambda attr, _: attr.is_(True),
    'is false': lambda attr, _: attr.is_(False),
    'is empty': lambda attr, _: func.json_array_length(attr) == 0,
    'is not empty': lambda attr, _: func.json_array_length(attr) > 0,
    'includes': lambda attr, ref: attr.contains(ref),
    'does not include': lambda attr, ref: not_(attr.contains(ref)),
}


def set_all_series_ids(*, log: Logger = log) -> None:
    """
    Schedule-able function to set any missing Series ID's for all Series
    in the Database.

    Args:
        log: Logger for all log messages.
    """

    with next(get_database()) as db:
        # Get all Series
        changed = False
        for series in db.query(Series).filter(Series.status != 'disabled').all():
            try:
                changed |= set_series_database_ids(
                    series, db, commit=False, log=log,
                )
            except HTTPException:
                log.warning(f'{series} skipping ID assignment')
                continue

        # Commit changes if any were made
        if changed:
            db.commit()


def load_all_media_servers(*, log: Logger = log) -> None:
    """
    Schedule-able function to load all Title Cards in the Database to
    the media servers.

    Args:
        log: Logger for all log messages.
    """

    with next(get_database()) as db:
        retries = 0
        # Get all Series
        for series in db.query(Series).filter(Series.status != 'disabled').all():
            # Skip this Series if it has no library
            if not series.libraries:
                log.debug(f'{series} has no libraries, not loading Title Cards')
                continue

            # Load Title Cards for this Series
            try:
                load_all_series_title_cards(series, db, log=log)
            except HTTPException:
                log.warning(f'{series} Skipping Title Card loading')
                continue
            except OperationalError:
                if (retries := retries + 1) > 10:
                    log.warning('Database is very busy - stopping Task')
                    break
                log.debug('Database is busy, sleeping..')
                sleep(30)


def download_all_series_posters(*, log: Logger = log) -> None:
    """
    Schedule-able function to download all posters for all monitored
    Series in the Database.

    Args:
        log: Logger for all log messages.
    """

    with next(get_database()) as db:
        # Get all Series
        for series in db.query(Series).all():
            try:
                download_series_poster(db, series, log=log)
            except HTTPException:
                log.warning(f'{series} Skipping poster selection')
                continue


def set_series_database_ids(
        series: Series,
        db: Session,
        *,
        commit: bool = True,
        log: Logger = log,
    ) -> bool:
    """
    Set the database ID's of the given Series.

    Args:
        series: Series to set the ID's of.
        db: Database to commit changes to.
        commit: Whether to commit changes after setting any ID's.
        log: Logger for all log messages.

    Returns:
        Whether the Series was modified.
    """

    # Query all interfaces for potential ID's
    series_info = series.as_series_info
    for library in series.libraries:
        if (interface := get_interface(library['interface_id'])):
            interface.set_series_ids(library['name'], series_info, log=log)
    for _, interface in get_sonarr_interfaces():
        interface.set_series_ids('', series_info, log=log)
    for _, interface in get_tmdb_interfaces():
        interface.set_series_ids('', series_info, log=log)
    for _, interface in get_tvdb_interfaces():
        interface.set_series_ids('', series_info, log=log)

    # Update Series with new IDs
    if (changed := series.set_ids_from_series_info(series_info)) and commit:
        db.commit()

    return changed


def download_series_poster(
        db: Session,
        series: Series,
        *,
        log: Logger = log,
    ) -> None:
    """
    Download the poster for the given Series.

    Args:
        db: Database to commit any changes to.
        series: Series to download the poster of.
        log: Logger for all log messages.
    """

    # If Series poster exists and is not a placeholder, return
    path = Path(series.poster_file)
    if path.name != 'placeholder.jpg' and path.exists():
        filesize = path.stat().st_size
        poster_url = f'/assets/{series.id}/poster.jpg?{filesize}'
        if series.poster_url != poster_url:
            series.poster_url = poster_url
            db.commit()
        return None

    # Download poster from Media Server if possible
    series_info, poster = series.as_series_info, None
    for library in series.libraries:
        if (interface := get_media_interface(library['interface_id'])):
            try:
                poster = interface.get_series_poster(
                    library['name'], series_info, log=log
                )
            except Exception:
                log.exception('Error downloading poster')
                continue

        # Stop if poster was found
        if poster is not None:
            break

    # If no poster was returned, download from TMDb
    if poster is None:
        for _, interface in get_tmdb_interfaces():
            if (poster := interface.get_series_poster(series_info, log=log)):
                break

    # If no posters were returned, log and exit
    if poster is None:
        log.warning(f'{series} no posters found')
        return None

    # Get path to the poster to download, download
    path = get_preferences().asset_directory / str(series.id) / 'poster.jpg'
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Download
        pb = poster if isinstance(poster, bytes) else get(poster, timeout=30).content

        # Assume corruption if poster is smaller than 1kB
        if not pb or len(pb) < 1024:
            raise ValueError

        # Write content
        path.write_bytes(pb)
    except ValueError:
        log.exception(f'{series} poster is corrupted')
        return None
    except Exception:
        log.exception(f'{series} Error downloading poster')
        return None

    # Verify image file is not corrupt by attempting a read
    try:
        Image.open(path)
    except UnidentifiedImageError:
        log.exception(f'{series} poster is corrupted')
        return None

    filesize = path.stat().st_size
    series.poster_file = str(path)
    series.poster_url = f'/assets/{series.id}/poster.jpg?{filesize}'
    db.commit()

    # Create resized small poster
    img = Image.open(path)
    img.resize((
        750, int(750 / img.width * img.height)),
        Image.Resampling.LANCZOS
    ).convert('RGB').save(path.parent / 'poster-750.jpg', )

    log.debug(f'Series[{series.id}] Downloaded poster {path.resolve()}')
    return None


def process_series(
        db: Session,
        series: Series,
        background_tasks: BackgroundTasks,
        *,
        log: Logger = log,
    ) -> None:
    """
    Completely process the given Series. This does all Title-Card tasks
    except loading the Cards.

    Args:
        db: Database connection.
        series: Series being processed.
        background_tasks: BackgroundTasks to queue processing into.
        log: Logger for all log messages.
    """

    # Nothing to process if disabled
    if series.status == 'disabled':
        log.debug(f'{series} is disabled, skipping processing')
        return None

    # Begin processing the Series
    # Refresh episode data
    if series.status == 'monitored':
        log.debug(f'{series} Started refreshing Episode data')
        refresh_episode_data(db, series, log=log)

    # Update watch statuses
    get_watched_statuses(db, series, series.episodes, log=log)

    # Begin downloading Source images
    if series.status == 'monitored':
        log.debug(f'{series} Started downloading source images')
        for episode in series.episodes:
            background_tasks.add_task(
                download_episode_source_images,
                db, episode, raise_exc=False, log=log,
            )

    # Begin Episode translation
    if series.status == 'monitored':
        log.debug(f'{series} Started adding translations')
        for episode in series.episodes:
            background_tasks.add_task(
                translate_episode,
                db, episode, commit=True, log=log,
            )

    # Begin Card creation
    log.debug(f'{series} Starting Card creation')
    for episode in series.episodes:
        background_tasks.add_task(
            create_episode_cards,
            db, episode, raise_exc=False, log=log
        )

    return None


def update_series_config(
        db: Session,
        series: Series,
        update_series: UpdateSeries,
        *,
        commit: bool = True,
        log: Logger = log,
    ) -> bool:
    """
    Update the given Series with the changes defined in update_series.
    This verifies any specified Fonts or Templates exist.

    Args:
        db: Database to query for Font or Template objects and to
            commit changes to.
        series: Series to modify.
        update_series: Object defining changes to make to the Series.
        commit: Whether to commit any changes to the database.
        log: Logger for all log messages.

    Returns:
        Whether the given Series was modified.
    """

    # If a Font is indicated, verify it exists
    if update_series.font_id not in (None, UNSPECIFIED):
        get_font(db,update_series.font_id, raise_exc=True)

    # Verify Image Source Priorty if indicated
    if (isp := update_series.image_source_priority) not in (None, UNSPECIFIED):
        [get_connection(db, id_, raise_exc=True) for id_ in isp]

    # Assign Templates if indicated
    changed = False
    if ((template_ids := update_series.template_ids)
        not in (None, UNSPECIFIED)):
        if series.template_ids != template_ids:
            templates = get_all_templates(db, template_ids)
            series.assign_templates(templates, log=log)
            changed = True

    # Update each attribute of the object
    for attr, value in update_series.model_dump(
        exclude_unset=True,
        exclude={
            'template_ids',
        },
    ).items():
        if getattr(series, attr) != value:
            log.debug(f'Series[{series.id}].{attr} = {value!r}')
            setattr(series, attr, value)
            changed = True

    # If any values were changed, commit to database
    if changed:
        if commit:
            db.commit()
        refresh_remote_card_types(db, log=log)

    return changed


def _delete_folder(folder: Path, *, log: Logger = log) -> None:
    """
    Recursively delete all subcontent of the provided folder.

    Args:
        folder: Folder to iterate through and delete.
        log: Logger for all log messages.
    """

    if folder.is_file():
        return None

    for item in folder.iterdir():
        if item.is_dir():
            _delete_folder(item, log=log)
        else:
            item.unlink(missing_ok=True)
            log.trace(f'Deleting "{item}"')

    return None


def delete_series(
        db: Session,
        series: Series,
        *,
        commit_changes: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Delete the given Series, poster, and all child (Episode, Card, and
    Loaded) objects.

    Args:
        db: Database to commit any deletion to.
        series: Series to delete.
        commit_changes: Whether to commit Database changes.
        log: Logger for all log messages.
    """

    # Delete poster if not the placeholder
    series_poster = Path(series.poster_file)
    if series_poster.stem != 'placeholder' and series_poster.exists():
        series_poster.unlink(missing_ok=True)
        small_poster = series_poster.parent / 'poster-750.jpg'
        small_poster.unlink(missing_ok=True)
        log.trace(f'{series} Deleted posters')

    # Delete Source directory (and files) if necessary
    if get_preferences().completely_delete_series:
        _delete_folder(series.source_directory, log=log)

    # Delete Series; all child objects are deleted on cascade
    log.info(f'Deleting {series}')
    db.delete(series)

    # Commit if indicated
    if commit_changes:
        db.commit()


def load_series_title_cards(
        series: Series,
        library_name: str,
        interface_id: int,
        db: Session,
        interface: EmbyInterface | JellyfinInterface | PlexInterface,
        force_reload: bool = False,
        *,
        episodes: list[Episode] | None = None,
        log: Logger = log,
    ) -> None:
    """
    Load the Title Cards for the given Series into the associated
    library.

    Args:
        series: Series to load the Title Cards of.
        library_name: Name of the library to load these Title Cards
            into.
        interface_id: ID of the Interface to associated with the
            loaded Title Cards.
        db: Database to look for and add Loaded records from/to.
        interface: Interfaces to the applicable Media Server to load
            Title Cards into.
        force_reload: Whether to reload Title Cards even if no changes
            are detected.
        episodes: Subset of Episodes to load the Title Cards of. If
            omitted, all Episodes are loaded.
        log: Logger for all log messages.
    """

    # Get list of Episodes to reload
    changed, episodes_to_load = False, []
    for episode in (episodes or series.episodes):
        # Determine queries based on library mode
        if len(series.libraries) == 1:
            card_query = dict(episode_id=episode.id)
        elif (len(series.libraries) > 1
            and not get_preferences().library_unique_cards):
            card_query = dict(episode_id=episode.id)
        else:
            card_query = dict(
                episode_id=episode.id,
                interface_id=interface_id,
                library_name=library_name,
            )

        # Only load if Episode has a Card
        if not (card := db.query(Card).filter_by(**card_query).first()):
            log.debug(f'{episode} - no associated Card')
            continue

        # Determine query for Loaded assets
        if len(series.libraries) == 1:
            loaded_query = dict(episode_id=episode.id)
        elif (len(series.libraries) > 1
            and not get_preferences().library_unique_cards):
            loaded_query = dict(
                episode_id=episode.id,
                interface_id=interface_id,
                library_name=library_name,
            )
        else:
            loaded_query = card_query

        # Find existing associated Loaded object(s)
        previously_loaded = db.query(Loaded).filter_by(**loaded_query).all()

        # No previously loaded Cards, load
        if not previously_loaded:
            episodes_to_load.append((episode, card))
            continue

        # There is a previously loaded Card, delete entry, reload
        if force_reload or (previously_loaded[0].filesize != card.filesize):
            # Delete previously loaded entries for this server
            for loaded in previously_loaded:
                db.delete(loaded)
            changed = True
            episodes_to_load.append((episode, card))
        # >1 loaded entry for this Card, delete first entries
        elif len(previously_loaded) > 1:
            for loaded in previously_loaded[:-1]:
                log.debug(f'Deleted {loaded}')
                db.delete(loaded)
        # Episode does not need to be reloaded
        else:
            continue

    # Load into indicated interface
    loaded_assets = interface.load_title_cards(
        library_name, series.as_series_info, episodes_to_load, log=log,
    )

    # Update database with loaded entries
    for loaded_episode, loaded_card in loaded_assets:
        try:
            db.add(Loaded(
                card_id=loaded_card.id,
                episode_id=loaded_episode.id,
                interface_id=interface_id,
                series_id=series.id,
                filesize=loaded_card.filesize,
                library_name=library_name,
            ))
        except InvalidRequestError:
            log.warning(
                f'Error creating Loaded asset for {loaded_episode} {card}'
            )
            continue

    # If any cards were (re)loaded, commit updates to database
    if changed or loaded_assets:
        db.commit()
        log.info(
            f'{series} Loaded {len(loaded_assets)} Cards into "{library_name}"'
        )


def load_all_series_title_cards(
        series: Series,
        db: Session,
        force_reload: bool = False,
        *,
        episodes: list[Episode] | None = None,
        raise_exc: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Load the Title Cards for the given Series into all the Series
    assigned libraries and Connections.

    Args:
        series: Series to load the Cards of.
        media_server: Where to load the Cards into.
        db: Database to look for and add Loaded records from/to.
        force_reload: Whether to reload Cards even if no changes are
            detected.
        episodes: Subset of Episodes to load the Title Cards of. If
            omitted, all Episodes are loaded.
        raise_exc: Whether to raise an HTTPException if a Connection
            associated with a library is invalid.
        log: Logger for all log messages.
    """

    # Load into each assigned library
    for library in series.libraries:
        interface_id = library['interface_id']
        if (interface := get_media_interface(interface_id)):
            load_series_title_cards(
                series, library['name'], interface_id, db, interface,
                force_reload=force_reload, episodes=episodes, log=log,
            )
        elif raise_exc:
            raise HTTPException(
                status_code=409,
                detail=f'Unable to communicate with Connection {interface_id}',
            )


def load_episode_title_card(
        episode: Episode,
        db: Session,
        library_name: str,
        interface_id: int,
        interface: EmbyInterface | JellyfinInterface | PlexInterface,
        *,
        attempts: int = 1,
        log: Logger = log,
    ) -> bool | None:
    """
    Load the Title Card for the given Episode into the indicated media
    server. This is a forced reload, and any existing Loaded assets are
    deleted.

    Args:
        episode: Episode to load the Title Card of.
        db: Database to look for and add Loaded records from/to.
        media_server: Which media server to load Title Cards into.
        interface: Interface to load Title Cards into.
        attempts: How many times to attempt loading the given Card.
        log: Logger for all log messages.

    Returns:
        Whether the Episode's Card was loaded or not. None if there is
        no Card.
    """

    # Determine if in single-library mode
    if len(episode.series.libraries) == 1:
        card_query = dict(episode_id=episode.id)
    elif (len(episode.series.libraries) > 1
        and not get_preferences().library_unique_cards):
        card_query = dict(episode_id=episode.id)
    else:
        card_query = dict(
            episode_id=episode.id,
            interface_id=interface_id,
            library_name=library_name,
        )

    # Only load if Episode has a Card
    if not (card := db.query(Card).filter_by(**card_query).first()):
        log.debug(f'{episode} - no associated Card')
        return None

    # Determine query for Loaded assets
    if len(episode.series.libraries) == 1:
        loaded_query = dict(card_id=card.id)
    elif (len(episode.series.libraries) > 1
        and not get_preferences().library_unique_cards):
        loaded_query = dict(
            episode_id=episode.id,
            interface_id=interface_id,
            library_name=library_name,
        )
    else:
        loaded_query = card_query

    # Delete previously Loaded entries
    db.query(Loaded).filter_by(**loaded_query).delete()

    loaded_assets = []
    for _ in range(attempts):
        # Load Episode's Card; exit loop if loaded
        loaded_assets = interface.load_title_cards(
            library_name,
            episode.series.as_series_info,
            [(episode, card)],
            log=log,
        )
        if loaded_assets:
            break

        log.debug(f'{episode} not found - waiting')
        sleep(30)

    # Episode was not loaded, exit
    if not loaded_assets:
        log.debug(f'{episode} could not be loaded')
        return False

    # Episode loaded, create Loaded asset and commit to database
    db.add(Loaded(
        card_id=card.id,
        episode_id=episode.id,
        interface_id=interface_id,
        series_id=episode.series.id,
        filesize=card.filesize,
        library_name=library_name,
    ))
    db.commit()
    return True


def load_title_card(
        card: Card,
        db: Session,
        library_name: str,
        interface_id: int,
        interface: EmbyInterface | JellyfinInterface | PlexInterface,
        *,
        uid: int | str | None = None,
        log: Logger = log,
    ) -> bool:
    """
    Load the Title Card for the given Episode into the indicated media
    server. This is a forced reload, and any existing Loaded assets are
    deleted.

    Args:
        episode: Episode to load the Title Card of.
        db: Database to look for and add Loaded records from/to.
        media_server: Which media server to load Title Cards into.
        interface: Interface to load Title Cards into.
        uid: Optional unique ID for for loading to a specific item in
            the indicated Interface.
        log: Logger for all log messages.

    Returns:
        Whether the Card was loaded or not.
    """

    # Determine query for Loaded assets
    if len(card.episode.series.libraries) == 1:
        loaded_query = dict(card_id=card.id)
    elif (len(card.episode.series.libraries) > 1
        and not get_preferences().library_unique_cards):
        loaded_query = dict(
            episode_id=card.episode.id,
            interface_id=interface_id,
            library_name=library_name,
        )
    else:
        loaded_query = dict(
            episode_id=card.episode.id,
            interface_id=interface_id,
            library_name=library_name,
        )

    # Delete previously Loaded entries
    db.query(Loaded).filter_by(**loaded_query).delete()

    # Load Card
    target = (card.episode, card) if uid is None else (card.episode, card, uid)
    loaded_assets = interface.load_title_cards(
        library_name,
        card.episode.series.as_series_info,
        [target], # type: ignore
        log=log,
    )

    # Card not loaded, exit
    if not loaded_assets:
        log.debug(f'{card} could not be loaded')
        return False

    # Card loaded, create Loaded asset and commit to database
    db.add(Loaded(
        card_id=card.id,
        episode_id=card.episode.id,
        interface_id=interface_id,
        series_id=card.episode.series.id,
        filesize=card.filesize,
        library_name=library_name,
    ))
    db.commit()
    return True


def add_series(
        new_series: NewSeries,
        background_tasks: BackgroundTasks | None,
        db: Session,
        *,
        log: Logger = log,
    ) -> Series:
    """
    Add the given NewSeries object to the database, and then perform all
    the initial Series processing - e.g. setting Series ID's,
    downloading a poster and logo, and refreshing Episode data.

    Args:
        new_series: NewSeries to add to the Database.
        background_tasks: BackgroundTasks to add the Episode data
            refresh task to.
        db: Database to add the Series to.
        log: Logger for all log messages.

    Returns:
        The Created Series.

    Raises:
        HTTPException (404): Any specified linked objects do not exist.
    """

    # Convert object to dictionary
    new_series_dict = new_series.dict()

    # If a Font, Sync, or any Templates were indicated, verify they exist
    get_font(db, getattr(new_series, 'font_id', None), raise_exc=True)
    get_sync(db, getattr(new_series_dict, 'sync_id', None), raise_exc=True)
    templates = get_all_templates(db, new_series_dict, raise_exc=True)

    # Add to database
    series = Series(**new_series.model_dump(exclude={'template_ids'}))
    db.add(series)
    db.commit()
    log.info(f'Added {series} to Database')

    # Assign Templates
    series.assign_templates(templates, log=log)
    db.commit()

    # Create source directory if DNE
    series.source_directory.mkdir(parents=True, exist_ok=True)

    # Set Series ID's, download poster and logo
    set_series_database_ids(series, db, log=log)
    download_series_poster(db, series, log=log)
    download_series_logo(series, log=log)

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, reset=False, log=log)

    # Refresh Episode data
    if series.status == 'monitored':
        if background_tasks:
            background_tasks.add_task(
                refresh_episode_data,
                db, series, background_tasks=background_tasks, log=log,
            )
        else:
            refresh_episode_data(db, series, background_tasks=None, log=log)

    return series


def lookup_series(
        db: Session,
        interface: EpisodeDataSourceInterface,
        name: str,
        *,
        max_results: int = 25,
        log: Logger = log,
    ) -> list[SearchResult]:
    """
    Get all the search results for the given name on the given
    interface.

    Args:
        db: Database to query for whether the Series exists or not.
        interface: Interface to query for results.
        name: Name of the Series being looked up.
        max_results: Maximum number of results to return.
        log: Logger for all log messages.

    Returns:
        Search results from the specified Interface for the given
        Series name.
    """

    # Query Interface
    results = interface.query_series(name, log=log)[:max_results]

    # Update added attribute(s)
    for result in results:
        # Query database for this result
        existing = db.query(Series)\
            .filter(result.series_info.filter_conditions(Series))\
            .first()

        # Result has been added if there is an existing Series
        result.added = existing is not None

    return results # type: ignore


def apply_filter(
        db: Session,
        query: Query[Series],
        filter: SeriesFilter | None,
        *,
        log: Logger = log,
    ) -> Query[Series]:
    """
    Apply the given set of filters to the provided query.

    Args:
        db: Session to optionally query if necessary.
        query: Query of Series to modify.
        filter: Optional filter to apply. May include any number of
            conditions, which will be applied in order.
        log: Logger for all log messages.

    Returns:
        A modified query (`query`) with the indicated filter conditions
        applied.
    """

    # Return unmodified original query if no filter was provided
    if not filter or not filter.conditions:
        return query

    # Apply each filter condition of the given filter
    criterion: list[ColumnElement[bool]] = []
    for condition in filter.conditions:
        # Special handling for the "missing cards" criteria
        if condition.field == 'missing_cards':
            # Unique Episode IDs associated with any Card
            episode_ids = db.query(Card.episode_id).distinct()

            # Series IDs of Episodes whose ID is not in the above list
            missing_series_ids: list[int] = [
                id_[0] for id_ in 
                db.query(Episode.series_id)
                    .filter(not_(Episode.id.in_(episode_ids)))
                    .distinct()
                    .all()
            ]

            criterion.append(
                Series.id.in_(missing_series_ids)
                if condition.expression == 'is true'
                else Series.id.notin_(missing_series_ids)
            )
            continue
        # Special handling for the "has no episodes" criteria
        elif condition.field == 'has_no_episodes':
            # Series IDs of Series which have Episodes
            series_ids = [
                id_[0] for id_ in db.query(Episode.series_id).distinct().all()
            ]

            # Filter Series which have no Episodes; No episodes = true
            # means include Series which are not in the above list
            criterion.append(
                Series.id.notin_(series_ids)
                if condition.expression == 'is true'
                else Series.id.in_(series_ids)
            )
            continue

        # Get attribute which will be operated on
        if (attribute := ConditionFieldAttributes.get(condition.field)) is None:
            log.debug(f'Unrecognized condition "{condition.field}"')
            continue

        # Get expression function, add to list of filter criteria
        expr_function = ConditionExpressionFunctions[condition.expression]
        criterion.append(expr_function(attribute, condition.reference))

    return query.filter(*criterion)


def query_and_filter_series(
        db: Session,
        filter: SeriesFilter | None,
        *,
        order_by: SeriesOrder,
        log: Logger = log,
    ) -> Page[SeriesOverview] | Page[SeriesOverviewWithCounts]: # type: ignore
    """
    Query for Series which match the given filter, ordering the results
    as indicated.

    Args:
        db: Session to query for Series.
        filter: Optional set of filter conditions to apply
        order_by: How to order the returned query.
        log: Logger for all log messages.

    Returns:
        Paginated overview of all matching Series.
    """

    # Perform query
    query = db.query(Series).options(
        load_only(
            Series.id,
            Series.full_name,
            Series.sort_name,
            Series.year,
            Series.poster_url,
            Series.libraries,
            Series.sync_id,
            Series.status,
        )
    )

    query = apply_filter(db, query, filter, log=log)

    # Order associated query
    series = query
    if order_by == 'alphabetical':
        series = query.order_by(Series.sort_name, Series.year)
    elif order_by == 'reverse-alphabetical':
        series = query.order_by(desc(Series.sort_name), Series.year)
    # Order by Cards
    elif order_by == 'cards':
        series = query\
            .outerjoin(Card)\
            .group_by(Series.id)\
            .order_by(func.count(Series.id))
    elif order_by == 'reverse-cards':
        series = query\
            .outerjoin(Card)\
            .group_by(Series.id)\
            .order_by(func.count(Series.id).desc())
    # Order by Sync
    elif order_by == 'sync':
        series = query.order_by(
            Series.sync_id.desc(),
            Series.sort_name,
            Series.year
        )
    # Order by ID
    elif order_by == 'id':
        series = query.order_by(Series.id)
    elif order_by == 'reverse-id':
        series = query.order_by(Series.id.desc())
    # Order by Year > Name
    elif order_by == 'year':
        series = query.order_by(Series.year, func.lower(Series.sort_name))
    elif order_by == 'reverse-year':
        series = query.order_by(Series.year.desc(), func.lower(Series.sort_name))

    return paginate(series)
