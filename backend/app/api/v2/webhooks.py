from asyncio import wait_for, TimeoutError as AsyncTimeoutError
from time import sleep
from typing import cast

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    Query,
    Request,
    UploadFile
)
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse
from pydantic.error_wrappers import ValidationError
from sqlalchemy.orm import Session

from app.db.query import get_episode, get_media_interface
from app.dependencies import (
    get_database,
    get_logger,
    get_sonarr_interfaces,
    require_plex_interface,
    InterfaceGroup,
    SonarrInterface,
    PlexInterface
)
from app.core.cards import create_episode_cards, delete_cards
from app.core.episodes import refresh_episode_data
from app.core.series import (
    add_series,
    delete_series,
    load_episode_title_card,
)
from app.core.sources import download_episode_source_images
from app.core.sync import get_sonarr_libraries
from app.core.translate import translate_episode
from app.core.webhooks import process_rating_key
from app.info.episode import EpisodeInfo
from app.info.series import SeriesInfo
from app.interfaces.base import WatchedStatus
from app.models.card import Card
from app.models.connection import Connection
from app.models.episode import Episode
from app.models.loaded import Loaded
from app.models.series import Series
from app.schemas.series import NewSeries
from app.schemas.webhooks import PlexWebhook, SonarrWebhook
from app.logging.logger import Logger


# Create sub router for all /webhooks API requests
webhook_router = APIRouter(
    prefix='/webhooks',
    tags=['Webhooks'],
)


@webhook_router.post('/plex/rating-key', tags=['Plex'])
def create_cards_for_plex_rating_key(
        key: int = Body(...),
        snapshot: bool = Query(default=True),
        db: Session = Depends(get_database),
        plex_interface: PlexInterface = Depends(require_plex_interface),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Create the Title Card for the item associated with the given Plex
    Rating Key. This item can be a Show, Season, or Episode. This
    endpoint does NOT require an authenticated User so that Tautulli can
    trigger this without any credentials.

    - interface_id: Interface ID of the Plex Connection associated with
    this Key.
    - key: Rating Key within Plex that identifies the item to create the
    Card(s) for.
    - snapshot: Whether to take snapshot of the database after all Cards
    have been processed.
    """

    return process_rating_key(
        db, plex_interface, key, snapshot=snapshot, log=log
    )


@webhook_router.post('/plex', tags=['Plex'])
async def process_plex_webhook(
        request: Request,
        # FastAPI cannot parse the payload, for some reason, so this needs to
        # be parsed from the request.form() directly
        # webhook: PlexWebhook = Form(...),
        snapshot: bool = Query(default=True),
        require_owner: bool = Query(default=True),
        trigger_on: str = Query(default='library.new,media.scrobble'),
        timeout: int = Query(min=5, max=600, default=300),
        db: Session = Depends(get_database),
        plex_interface: PlexInterface = Depends(require_plex_interface),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Process the items defined in the given Plex Webhook. The Webhook
    data must be passed as a multipart Form inside the Request payment.

    - interface_id: Interface ID of the Plex Connection associated with
    this Key.
    - snapshot: Whether to take snapshot of the database after all Cards
    have been processed.
    - require_owner: Whether to only process triggers which come from
    the owner of the server.
    - trigger_on: String containing webhook event types to trigger on.
    - timeout: Maximum amount of time allowed for the API request before
    the request is terminated.
    """

    # Parse Webhook from payload
    try:
        form = cast(
            dict[str, bytes],
            await wait_for(request.form(), timeout=timeout)
        )
        webhook = PlexWebhook.parse_raw(form.get('payload', b''))
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail='Webhook format is invalid'
        ) from exc
    except Exception as exc:
        log.exception('Error occurred while parsing Webhook')
        raise HTTPException(
            status_code=422,
            detail='Error occurred while parsing Webhook'
        ) from exc

    # Skip if not in the trigger list or if not the owner
    if (webhook.event not in trigger_on
        and (not require_owner or (require_owner and webhook.owner))):
        log.trace(f'Skipping Webhook of trigger "{webhook.event}"')
        return None

    try:
        await wait_for(
            run_in_threadpool(
                process_rating_key,
                db,
                plex_interface,
                webhook.Metadata.ratingKey,
                new_only=webhook.event == 'library.new',
                snapshot=snapshot,
                log=log,
            ),
            timeout=timeout,
        )
    except AsyncTimeoutError as exc:
        log.exception('Webhook request has timed out')
        raise HTTPException(
            status_code=504,
            detail='Webhook has timed out'
        ) from exc


@webhook_router.post('/sonarr/cards', tags=['Sonarr'])
def create_cards_for_sonarr_webhook(
        webhook: SonarrWebhook = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Create the Title Card for the items associated with the given Sonarr
    Webhook payload. This is practically identical to the `/key`
    endpoint.

    - webhook: Webhook payload containing Series and Episode details to
    create the Title Cards of.
    """

    # Skip if payload has no Episodes to create Cards for
    if not webhook.episodes:
        return None

    # Create SeriesInfo for this payload's series
    series_info = SeriesInfo(
        name=webhook.series.title,
        year=webhook.series.year,
        imdb_id=webhook.series.imdbId,
        tvdb_id=webhook.series.tvdbId,
        tvrage_id=webhook.series.tvRageId,
    )

    # Search for this Series
    series = db.query(Series)\
        .filter(series_info.filter_conditions(Series))\
        .first()

    # Series is not found, exit
    if series is None:
        log.info(f'Cannot find Series {series_info}')
        return None

    def _find_episode(episode_info: EpisodeInfo) -> Episode | None:
        """Attempt to find the associated Episode up to three times."""

        for _ in range(3):
            # Search for this Episode
            episode = db.query(Episode)\
                .filter(Episode.series_id==series.id,
                        episode_info.filter_conditions(Episode))\
                .first()

            # Episode exists, return it
            if episode:
                return episode

            # Sleep and re-query Episode data
            log.debug(f'Cannot find Episode, waiting..')
            sleep(15)
            refresh_episode_data(db, series, log=log)

        return None

    # Find each Episode in the payload
    for webhook_episode in webhook.episodes:
        episode_info = EpisodeInfo(
            title=webhook_episode.title,
            season_number=webhook_episode.seasonNumber,
            episode_number=webhook_episode.episodeNumber,
            tvdb_id=webhook_episode.tvdbId,
        )

        # Find this Episode
        if (episode := _find_episode(episode_info)) is None:
            log.info(f'Cannot find Episode for {series_info} {episode_info}')
            return None

        # Assume Episode is unwatched in all libraries which do not
        # already have a defined watched status
        for library in series.libraries:
            iid, name = library['interface_id'], library['name']
            if episode.get_watched_status(iid, name) is None:
                episode.add_watched_status(
                    WatchedStatus(iid, name, False), log=log
                )

        # Look for source, add translation, create Card if source exists
        images = download_episode_source_images(db, episode, log=log)
        translate_episode(db, episode, log=log)
        if not images:
            log.info(f'{episode} has no source image - skipping')
            continue
        create_episode_cards(db, episode, log=log)

        # Refresh this Episode so that relational Card objects are
        # updated, preventing stale (deleted) Cards from being used in
        # the Loaded asset evaluation. Not sure why this is required
        # because SQLAlchemy should update child objects when the DELETE
        # is committed; but this does not happen.
        db.refresh(episode)

        # Reload into all associated libraries
        for library in series.libraries:
            iid = library['interface_id']
            if (interface := get_media_interface(iid, raise_exc=False)):
                load_episode_title_card(
                    episode,
                    db,
                    library['name'],
                    iid,
                    interface,
                    attempts=6,
                    log=log,
                )
            else:
                log.debug(
                    f'Not loading {series_info} {episode_info} into library '
                    f'"{library["name"]}" - no valid Connection'
                )
                continue

    return None


@webhook_router.post('/sonarr/series/delete', tags=['Sonarr'])
def delete_series_via_sonarr_webhook(
        webhook: SonarrWebhook,
        delete_title_cards: bool = Query(default=True),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Delete the Series defined in the given Webhook.

    - webhook: Webhook payload containing the details of the Series to
    delete.
    - delete_title_cards: Whether to delete Title Cards.
    """

    # Skip if Webhook type is not a Series deletion
    if webhook.eventType != 'SeriesDelete':
        return None

    # Create SeriesInfo for this payload's series
    series_info = SeriesInfo(
        name=webhook.series.title,
        year=webhook.series.year,
        imdb_id=webhook.series.imdbId,
        tvdb_id=webhook.series.tvdbId,
        tvrage_id=webhook.series.tvRageId,
    )

    # Search for this Series
    series = db.query(Series)\
        .filter(series_info.filter_conditions(Series))\
        .first()

    # Series is not found, exit
    if series is None:
        raise HTTPException(
            status_code=404,
            detail=f'Series {series_info} not found',
        )

    # Delete Card, Loaded, and Series, as well all child content
    if delete_title_cards:
        delete_cards(
            db,
            db.query(Card).filter_by(series_id=series.id),
            db.query(Loaded).filter_by(series_id=series.id),
            log=log,
        )
    delete_series(db, series, log=log)
    return None


@webhook_router.post('/sonarr/series/add', tags=['Sonarr'])
def add_series_via_sonarr_webhook(
        background_tasks: BackgroundTasks,
        webhook: SonarrWebhook,
        connection_id: int | None = Query(default=None),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
        sonarr_interfaces: InterfaceGroup[int, SonarrInterface] = Depends(
            get_sonarr_interfaces
        ),
    ) -> None:
    """
    Add the Series defined in the given Webhook.

    - webhook: Webhook payload containing the details of the Series to
    add.
    """

    if webhook.eventType != 'SeriesAdd':
        log.debug(f'Skipping Webhook type "{webhook.eventType}"')
        return None

    # Add Series to the page
    series = add_series(
        NewSeries(
            name=webhook.series.title,
            year=webhook.series.year,
            imdb_id=webhook.series.imdbId,
            tvdb_id=webhook.series.tvdbId,
            tvrage_id=webhook.series.tvRageId,
        ),
        background_tasks=background_tasks,
        db=db,
        log=log
    )

    # If a Connection ID is provided, use it to assign libraries to the
    # new Series
    if connection_id is not None:
        # Get Connection of this ID
        connection = db.query(Connection).filter_by(id=connection_id).first()
        if connection is None:
            log.error(f'Connection with ID {connection_id} not found')
            return None
        if (interface := sonarr_interfaces.get(connection_id)) is None:
            log.error(
                f'SonarrInterface with ID {connection.interface_id} not found'
            )
            return None

        # Get the path of the series from Sonarr
        if (directory := interface.get_series_path(series.id)) is None:
            log.error(f'Series with ID {series.id} not found')
            return None

        libraries = get_sonarr_libraries(db, directory, connection, log=log)
        if libraries:
            series.libraries = libraries
            log.debug(f'Series[{series.id}].libraries = {libraries}')
            db.commit()

    return None


from requests import post
@webhook_router.post('/background-removal')
def remove_image_background(
        request: Request,
        file: UploadFile | None = None,
        episode_id: int | None = Query(default=None),
        url: str = Query(...),
        timeout: int = Query(default=30, min=5, max=240),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> StreamingResponse:
    """"""

    if file:
        try:
            response = post(
                url,
                stream=True,
                timeout=timeout,
                files={
                    'file': (
                        file.filename,
                        file.file,
                        file.content_type or 'image/jpg'
                    )
                },
            )
        except ConnectionError as exc:
            log.exception('Unable to submit BGR API request')
            raise HTTPException(
                status_code=400,
                detail='Invalid BGR Request',
            ) from exc
    elif episode_id:
        episode = get_episode(db, episode_id, raise_exc=True)
        source = episode.get_source_file('unique')
        with source.open('rb') as file_io:
            try:
                response = post(
                    url,
                    # stream=True,
                    timeout=timeout,
                    files={ 'file': file_io }
                )
            except ConnectionError as exc:
                log.exception('Unable to submit BGR API request')
                raise HTTPException(
                    status_code=400,
                    detail='Invalid BGR Request',
                ) from exc
    else:
        raise HTTPException(
            status_code=422,
            detail='File or episode ID is required'
        )

    # Stream the response back to the client
    def iterfile():
        for chunk in response.iter_content(chunk_size=4096):
            yield chunk

    return StreamingResponse(iterfile(), media_type='image/png')
