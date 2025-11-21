from datetime import datetime
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    Form,
    HTTPException,
    Query,
    UploadFile
)
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import paginate as paginate_sequence
from PIL import Image
from pydantic import ValidationError
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, load_only
from unidecode import unidecode

from app import models
from app.dependencies import (
    get_database,
    require_interface,
    require_tmdb_interface,
    TMDbInterface
)
from app.db.pagination import Page
from app.db.query import get_interface, get_series, require_series
from app.core.series import (
    add_series,
    delete_series,
    download_series_poster,
    lookup_series,
    process_series,
    query_and_filter_series,
    update_series_config,
)
from app.db.users import get_current_user
from app.interfaces.plex import PlexInterface
from app.interfaces.web import WebInterface
from app.logging.logger import log
from app.models.series import Series as SeriesModel
from app.schemas.filter import SeriesFilter
from app.schemas.series import (
    BatchUpdateSeries,
    NewSeries,
    SearchResult,
    Series,
    SeriesOrder,
    SeriesOverview,
    SeriesOverviewWithCounts,
    SeriesSearchResult,
    Status,
    UpdateSeries
)
from app.settings import settings


series_router = APIRouter(
    prefix='/series',
    tags=['Series'],
    dependencies=[Depends(get_current_user)],
)


@series_router.get('/all')
def get_all_series(
        db: Session = Depends(get_database),
        order_by: SeriesOrder = Query(default='alphabetical'),
        filter_: str = Query(alias='filter', default=None),
    ) -> Page[SeriesOverview]: # type: ignore
    """
    Get all defined Series.

    - order_by: How to order the Series in the returned list.
    - filter: Optional filter conditions to apply the list of returned
    Series.
    """

    try:
        filter = SeriesFilter.model_validate_json(filter_) if filter_ else None
    except ValidationError as exc:
        log.exception('Invalid filter definition')
        raise HTTPException(
            status_code=422,
            detail='Filter definition is invalid',
        ) from exc

    return paginate_sequence(
        query_and_filter_series(db, filter, order_by=order_by, extended=False)
    )


@series_router.get('/all-extended')
def get_all_series_including_counts(
        db: Session = Depends(get_database),
        order_by: SeriesOrder = Query(default='alphabetical'),
        filter_: str = Query(alias='filter', default=None),
    ) -> Page[SeriesOverviewWithCounts]: # type: ignore
    """
    Get all defined Series.

    - order_by: How to order the Series in the returned list.
    - filter: Optional filter conditions to apply the list of returned
    Series.
    """

    try:
        filter = SeriesFilter.model_validate_json(filter_) if filter_ else None
    except ValidationError as exc:
        log.exception('Invalid filter definition')
        raise HTTPException(
            status_code=422,
            detail='Filter definition is invalid',
        ) from exc

    return paginate_sequence(
        query_and_filter_series(db, filter, order_by=order_by, extended=True)
    )


@series_router.get('/recent')
def get_recently_added_series(
        db: Session = Depends(get_database),
        after: datetime = Query(...),
    ) -> Page[Series]: # type: ignore
    """
    Get all recently created Series after the given date.

    - after: Date which to exclude Series created before. 
    """

    return paginate(
        db.query(SeriesModel)
            .filter(SeriesModel.created > settings.config.localize(after))
    )


@series_router.get('/series/{series_id}/previous')
def get_previous_series(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> Series | None:
    """
    Get the previous Series (sorted alphabetically, year, then by ID).

    - series_id: ID of the reference Series.
    """

    # Get the reference Series
    series = get_series(db, series_id, raise_exc=True)

    return (
        db.query(SeriesModel)
            .filter(
                SeriesModel.id.is_not(series_id),
                or_(
                    SeriesModel.comes_before(series.sort_name),
                    and_(
                        SeriesModel.sort_name == series.sort_name,
                        SeriesModel.year < series.year
                    )
                )
            )
            .order_by(
                SeriesModel.sort_name.desc(),
                SeriesModel.year.desc(),
                SeriesModel.id.desc()
            )
            .first()
    )


@series_router.get('/series/{series_id}/next')
def get_next_series(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> Series | None:
    """
    Get the next Series (sorted alphabetically, year, then by ID).

    - series_id: ID of the reference Series.
    """

    # Get the reference Series
    series = get_series(db, series_id, raise_exc=True)

    return (
        db.query(SeriesModel)
            .filter(
                SeriesModel.id.is_not(series_id),
                or_(
                    SeriesModel.comes_after(series.sort_name),
                    and_(
                        SeriesModel.sort_name == series.sort_name,
                        SeriesModel.year > series.year
                    )
                )
            )
            .order_by(
                SeriesModel.sort_name,
                SeriesModel.year,
                SeriesModel.id
            )
            .first()
    )


@series_router.post('/new')
def add_new_series(
        background_tasks: BackgroundTasks,
        new_series: NewSeries = Body(...),
        db: Session = Depends(get_database),
    ) -> Series:
    """
    Create a new Series. This also creates background tasks to set the
    database ID's of the series, as well as find and download a poster.

    - new_series: Series definition to create.
    """

    return add_series(new_series, background_tasks, db)


@series_router.delete('/series/{series_id}')
def delete_series_(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Delete the Series with the given ID. This also deletes the poster.

    - series_id: ID of the Series to delete.
    """

    # Find series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Delete Series and all child content
    delete_series(db, series)


@series_router.get('/search')
def search_existing_series(
        name: str | None = None,
        sync_id: int | None = None,
        template_id: int | None = None,
        db: Session = Depends(get_database),
    ) -> Page[SeriesSearchResult]: # type: ignore
    """
    Query all defined defined series by the given parameters. This
    performs an AND operation with the given conditions.

    - name: Name to fuzzy match the Series against.
    - *_id: Associated object ID to filter the results by.
    """

    # Perform query on subset of Series data
    query = db.query(SeriesModel).options(
        load_only(
            SeriesModel.clean_name,
            SeriesModel.id,
            SeriesModel.name,
            SeriesModel.poster_url,
            SeriesModel.sort_name,
            SeriesModel.sync_id,
            SeriesModel.year,
        )
    )

    # Generate conditions for the given arguments
    conditions = []
    if name is not None:
        conditions.append(or_(
            SeriesModel.name.contains(name),
            SeriesModel.fuzzy_matches(name),
            SeriesModel.clean_name.contains(unidecode(name, errors='preserve')),
        ))
    if sync_id is not None:
        conditions.append(SeriesModel.sync_id==sync_id)

    # Template ID filtering has alternate filter logic
    if template_id is not None:
        return paginate(
            db.query(SeriesModel)
                .join(models.template.SeriesTemplates.series)
                .filter(models.template.SeriesTemplates.template_id==template_id)
                .filter(*conditions)
                .order_by(SeriesModel.sort_name)
        )

    # Query by all given conditions - if by name, sort by str difference
    results = query.filter(*conditions)
    if name is not None:
        return paginate(
            results
                .order_by(SeriesModel.diff_ratio(name).desc())
                .order_by(func.lower(SeriesModel.sort_name))
        )

    return paginate(results.order_by(func.lower(SeriesModel.sort_name)))


@series_router.get('/lookup')
def lookup_new_series(
        name: str = Query(..., min_length=1),
        db: Session = Depends(get_database),
        interface = Depends(require_interface),
    ) -> Page[SearchResult]: # type: ignore
    """
    Look up the given Series name on the indicated Interface. Returned
    results are not necessary already added to TCM - use the `/search`
    endpoint to query existing Series.

    - name: Series name or substring to look up.
    - interface_id: ID of the interface to query.
    """

    return paginate_sequence(lookup_series(db, interface, name))


@series_router.get('/series/{series_id}')
def get_series_config(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> Series:
    """
    Get the config for the given Series.

    - series_id: ID of the series to get the config of.
    """

    return get_series(db, series_id, raise_exc=True)


@series_router.patch('/series/{series_id}')
def update_series(
        series_id: int,
        update: UpdateSeries = Body(...),
        db: Session = Depends(get_database),
    ) -> Series:
    """
    Update the config of the given Series.

    - series_id: ID of the Series to update.
    - update_series: Attributes of the Series to update.
    """

    series = get_series(db, series_id, raise_exc=True)
    update_series_config(db, series, update, commit=True)

    return series


@series_router.put('/series/{series_id}/copy')
def copy_series_config(
        series_id: int,
        from_series_id: int = Query(...),
        reset_series: bool = Query(default=True),
        reset_episodes: bool = Query(default=False),
        db: Session = Depends(get_database),
    ) -> Series:
    """

    """

    # Get to- and from-Series
    to_series = get_series(db, series_id, raise_exc=True)
    from_series = get_series(db, from_series_id, raise_exc=True)

    # Reset Series/Episode if indicated
    if reset_series:
        to_series.reset_card_config()
        log.debug(f'Reset {to_series}')
    if reset_episodes:
        for episode in to_series.episodes:
            episode.reset_card_config()
            log.debug(f'Reset {episode}')

    # Copy config over
    to_series.copy_card_config(from_series)
    log.info(f'Copied Card config from {from_series} to {to_series}')

    # Commit changes
    db.commit()
    return to_series


@series_router.put('/series/{series_id}/toggle-monitor')
def toggle_series_monitored_status(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> Series:
    """
    Toggle the monitored attribute of the given Series. This cycles
    statuses like "monitored" -> "unmonitored" -> "disabled" (looping).

    - series_id: ID of the Series to toggle the monitored attribute of.
    """

    # Query for this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Toggle status, update Database
    statuses = ['monitored', 'unmonitored', 'disabled']
    current_index = statuses.index(series.status)
    series.status = statuses[(current_index + 1) % len(statuses)]
    db.commit()

    return series


@series_router.post('/series/{series_id}/process')
def process_series_(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Completely process the given Series. This does all major "tasks,"
    including:

    1. Refreshing Episode data.
    2. Downloading Source images
    3. Adding any Episode translations
    4. Updating Episode watch statuses
    5. Create Title Cards for all Episodes

    - series_id: ID of the Series to process.
    """

    process_series(
        db,
        get_series(db, series_id, raise_exc=True),
        None,
    )


@series_router.delete('/series/{series_id}/plex-labels/library')
def remove_series_labels(
        series_id: int,
        interface_id: int = Query(...),
        library_name: str = Query(...),
        labels: list[str] = Query(default=['TCM', 'Overlay']),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Remove the given labels from the given Series' Episodes within Plex.
    This can be used to reset PMM overlays.

    - series_id: ID of the Series whose Episode labels are being remove.
    - interface_id: ID of the Interface whose library is being removed.
    - library_name: Name of the library to remove labels from.
    - labels: Any labels to remove.
    """

    # Get this Series and Interface, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)
    interface = get_interface(interface_id, raise_exc=True)

    if not isinstance(interface, PlexInterface):
        raise HTTPException(
            status_code=422,
            detail='Provided interface ID must be a Plex Connection'
        )

    # Remove labels from specified library
    interface.remove_series_labels(
        library_name, series.as_series_info, labels
    )


@series_router.get('/series/{series_id}/poster')
def download_series_poster_(
        series: SeriesModel = Depends(require_series),
        db: Session = Depends(get_database),
    ) -> str:
    """
    Download a poster for the given Series.

    - series_id: ID of the Series whose poster to download.
    """

    download_series_poster(db, series)

    return series.poster_url


@series_router.delete('/series/{series_id}/poster')
def delete_series_poster(series: SeriesModel = Depends(require_series)) -> None:
    """
    Delete the poster for the given Series.

    - series_id: ID of the Series to delete the poster of.
    """

    poster_path = settings.asset_directory / str(series.id) / 'poster.jpg'
    small_poster = poster_path.parent / 'poster-750.jpg'

    poster_path.unlink(missing_ok=True)
    small_poster.unlink(missing_ok=True)


@series_router.get('/series/{series_id}/poster/query')
def query_series_poster(
        series_id: int,
        db: Session = Depends(get_database),
        tmdb_interface: TMDbInterface = Depends(require_tmdb_interface)
    ) -> str | None:
    """
    Query for a poster of the given Series.

    - series_id: Series being queried.
    """

    return tmdb_interface.get_series_poster(
        get_series(db, series_id, raise_exc=True).as_series_info
    )


@series_router.put('/series/{series_id}/poster')
async def set_series_poster(
        series_id: int,
        url: str | None = Form(default=None),
        file: UploadFile | None = None,
        db: Session = Depends(get_database),
    ) -> str:
    """
    Set the poster for the given series.

    - series_id: ID of the series whose poster is being updated.
    - poster_url: URL to the new poster.
    - poster_file: New poster file.
    """

    # Find Series with this ID, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Get poster contents
    uploaded_file = b''
    if file is not None:
        uploaded_file = await file.read()

    # Send error if both a URL and file were provided
    if url is not None and len(uploaded_file) > 0:
        raise HTTPException(
            status_code=422,
            detail='Cannot provide multiple posters'
        )

    # Send error if neither were provided
    if url is None and len(uploaded_file) == 0:
        raise HTTPException(
            status_code=422,
            detail='URL or file are required'
        )

    # If an uploaded file was provided, use that
    if len(uploaded_file) > 0:
        poster_content = uploaded_file

    # If only URL was required, attempt to download, error if unable
    if url is not None:
        poster_content = WebInterface.download_image_raw(url)
        if poster_content is None:
            raise HTTPException(
                status_code=400,
                detail='Unable to download poster'
            )

    # Valid poster provided, download into asset directory
    poster_path = settings.asset_directory / str(series.id) / 'poster.jpg'  
    series.poster_file = str(poster_path)
    poster_path.parent.mkdir(exist_ok=True, parents=True)
    poster_path.write_bytes(poster_content) # type: ignore

    # Create resized poster for preview
    img = Image.open(poster_path)
    img.convert('RGB').resize(
        (750, int(750 / img.width * img.height)),
        Image.Resampling.LANCZOS
    ).save(poster_path.parent / 'poster-750.jpg')

    # Update poster, commit to database
    series.poster_url = f'/assets/{series.id}/poster.jpg'
    db.commit()

    return series.poster_url


@series_router.patch('/batch')
def batch_update_series(
        updates: list[BatchUpdateSeries] = Body(...),
        db: Session = Depends(get_database),
    ) -> list[Series]:
    """
    Update the config of all the given Series.

    - updates: List of Series IDs and the associated changes to make for
    that Series.
    """

    # Iterate through all provided Series
    all_series, changed = [], False
    for update in updates:
        # Get Series with the specified ID
        series = get_series(db, update.series_id, raise_exc=True)
        all_series.append(series)

        # Update this Series
        changed |= update_series_config(db, series, update.update, commit=False)

    # Commit changes to DB if necessary
    if changed:
        db.commit()

    return all_series


@series_router.put('/batch/monitor', deprecated=True)
def batch_monitor_series(
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> list[Series]:
    """
    Mark the Series with the given IDs as monitored.

    - series_ids: List of IDs of Series to mark as monitored.
    """

    all_series = []
    for series_id in series_ids:
        # Query for this Series, raise 404 if DNE
        series = get_series(db, series_id, raise_exc=True)
        all_series.append(series)

        # Update monitored attribute
        series.status = 'monitored'
        log.debug(f'{series}.status = "monitored"')

    db.commit()

    return all_series


@series_router.put('/batch/unmonitor', deprecated=True)
def batch_unmonitor_series(
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> list[Series]:
    """
    Mark the Series with the given IDs as unmonitored.

    - series_ids: List of IDs of Series to mark as monitored.
    """

    all_series = []
    for series_id in series_ids:
        # Query for this Series, raise 404 if DNE
        series = get_series(db, series_id, raise_exc=True)
        all_series.append(series)

        # Update monitored attribute
        series.status = 'unmonitored'
        log.debug(f'{series}.status = "unmonitored"')

    db.commit()

    return all_series


@series_router.patch('/batch/status/{status}')
def batch_update_series_status(
        status: Status,
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> list[Series]:
    """
    Update the status of all the given Series.

    - status: Status to set all the given Series to.
    - series_ids: List of IDs of Series to update the status of.
    """

    all_series = []
    for series_id in series_ids:
        series = get_series(db, series_id, raise_exc=True)
        all_series.append(series)

        series.status = status
        log.debug(f'{series}.status = {status}')

    db.commit()

    return all_series


@series_router.delete('/batch/delete')
def batch_delete_series(
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Batch operation to delete all the given Series.

    - series_ids: List of IDs of Series to delete.
    """

    for series_id in series_ids:
        series = get_series(db, series_id, raise_exc=True)
        delete_series(db, series)


@series_router.post('/batch/process')
def batch_process_series(
        background_tasks: BackgroundTasks,
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Completely process all the given Series.

    - series_ids: List of IDs of Series to process.
    """

    for series_id in series_ids:
        process_series(
            db,
            get_series(db, series_id, raise_exc=True),
            background_tasks,
        )
