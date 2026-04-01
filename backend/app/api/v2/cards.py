from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Query,
)
from fastapi.responses import FileResponse
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import not_
from sqlalchemy.orm import Session, contains_eager, load_only, selectinload

from app.db.query import (
    get_card,
    get_episode,
    get_font,
    get_interface,
    get_series,
    get_template
)
from app.db.pagination import Page
from app.dependencies import get_database
from app.db.users import get_current_user
from app.core.cards import (
    create_episode_cards,
    delete_cards,
    get_watched_statuses,
    resolve_card_settings,
    validate_card_type_model,
)
from app.core.config import INTERNAL_ASSET_DIRECTORY
from app.core.episodes import update_episode_config
from app.core.series import (
    load_all_series_title_cards,
    load_episode_title_card,
    load_series_title_cards,
    load_title_card,
    update_series_config,
)
from app.exceptions import (
    InvalidCardSettings,
    MissingSourceImage,
    UnknownCardType,
)
from app.interfaces.v2 import EmbyInterface, JellyfinInterface, PlexInterface
from app.logging.logger import log
from app.models.card import Card
from app.models.episode import Episode
from app.models.loaded import Loaded
from app.schemas.card import (
    CardActions,
    TitleCard,
    TitleCardExtended,
    TitleCardReduced,
)
from app.schemas.episode import UpdateEpisode
from app.schemas.font import UpdateNamedFont
from app.schemas.series import UpdateSeries, UpdateTemplate
from app.settings import settings
from app.utils.tzip import TemporaryZip


# Create sub router for all /cards API requests
card_router = APIRouter(
    prefix='/cards',
    tags=['Title Cards'],
    dependencies=[Depends(get_current_user)],
)


@card_router.post('/preview/episode/{episode_id}', tags=['Episodes'])
def create_preview_card_for_episode(
        episode_id: int,
        update_episode: UpdateEpisode = Body(...),
        update_series: UpdateSeries = Body(...),
        update_font: UpdateNamedFont | None = Body(default=None),
        query_watched_statuses: bool = Query(default=False),
        db: Session = Depends(get_database),
    ) -> str:
    """
    Create a preview Title Card for the given Episode. This allows for
    previewing live-edits to the given Episode, Series, or Font. Any
    changes made to these objects in the given body will be reflected in
    the card, but will not be saved to the database.

    - episode_id: ID of the Episode to create the Title Card for.
    - update_episode: UpdateEpisode containing fields to update.
    - update_series: UpdateSeries containing fields to update.
    - update_font: UpdateNamedFont containing fields to update.
    - query_watched_statuses: Whether to query the watched statuses
    associated with this Episode.
    """

    # Find associated Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Raise exception if Template IDs are part of update object; cannot
    # be reflected in the live preview because relationship objects will
    # not be reflected until a database commit
    e_dict = update_episode.model_dump(exclude_unset=True)
    s_dict = update_series.model_dump(exclude_unset=True)
    if ((
            e_dict.get('template_ids') is not None
            and e_dict.get('template_ids') != episode.template_ids
        ) or (
            s_dict.get('template_ids') is not None
            and s_dict.get('template_ids') != episode.series.template_ids
        )
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                'Preview Cards cannot reflect Template changes - save these '
                'changes and try again'
            )
        )

    update_episode_config(db, episode, update_episode)
    update_series_config(db, episode.series, update_series, commit=False)

    # Update Font if indicated
    if update_font is not None and update_font.id is not None:
        font = get_font(db, update_font.id, raise_exc=True)
        for attribute, value in update_font.model_dump(exclude_unset=True).items():
            if getattr(font, attribute) != value:
                setattr(font, attribute, value)
                log.debug(f'Font[{font.id}].{attribute} = {value}')

    # Set watch status(es) of the Episode
    if query_watched_statuses:
        get_watched_statuses(db, episode.series, [episode])

    # Determine appropriate Source and Output file
    if not (source := episode.get_source_file('unique')).exists():
        log.debug('Source image does not exist, using fallback')
        source = INTERNAL_ASSET_DIRECTORY / 'preview' / 'unique.jpg'
    episode.source_file = str(source)
    output = (
        INTERNAL_ASSET_DIRECTORY
        / 'preview'
        / f'card-unique{settings.card_extension}'
    )
    output.unlink(missing_ok=True)

    # If a library is available, use the first one
    library = None
    if episode.series.libraries:
        library = episode.series.libraries[0]

    # Create Card for this Episode
    try:
        card_settings = resolve_card_settings(episode, library)
        card_settings['card_file'] = output
    except UnknownCardType as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                'Preview cards cannot be created from un-initialized card '
                'types - save the card type and try again'
            )
        ) from exc
    except MissingSourceImage as exc:
        raise HTTPException(
            status_code=404,
            detail='Missing the required Source Image',
        ) from exc
    except (HTTPException, InvalidCardSettings) as exc:
        raise HTTPException(
            status_code=400,
            detail='Invalid Card settings',
        ) from exc

    # Delete output if it exists, then create Card
    CardClass, CardTypeModel = validate_card_type_model(card_settings)
    card_maker = CardClass(**CardTypeModel.model_dump(), preferences=settings)
    card_maker.create()

    # Card created, return URI
    if output.exists():
        return f'/public/preview/{output.name}'

    card_maker.image_magick.print_command_history()
    raise HTTPException(
        status_code=500,
        detail='Failed to create preview card'
    )


@card_router.post(
    '/preview/episode/{episode_id}/template/{template_id}',
    tags=['Templates']
)
def create_preview_card_for_template(
        episode_id: int,
        template_id: int,
        update_template: UpdateTemplate = Body(...),
        db: Session = Depends(get_database),
    ) -> str:
    """
    Create a preview Title Card for the given Episode, reflecting the
    changes to the given Template. These changes will not be saved to
    the database. This Template will be added to the Episode and
    temporarily commited to the database (necessary to update the
    association table for Episode:Template relationships), but any
    commits will be reverted after the card is created. Changes to the
    Template will also be reverted.

    - episode_id: ID of the Episode to create the Title Card for.
    - template_id: ID of the Template to create the Title Card for.
    - update_template: UpdateTemplate containing fields to update.
    """

    episode = get_episode(db, episode_id)
    template = get_template(db, template_id)

    # Apply temporary changes to the Template
    reversions: dict[str, Any] = {}
    update_model = update_template.model_dump(exclude_unset=True)
    for attribute, value in update_model.items():
        if getattr(template, attribute) != value:
            reversions[attribute] = getattr(template, attribute)
            setattr(template, attribute, value)
            log.debug(f'Template[{template.id}].{attribute} = {value}')

    # This whole block should be wrapped in a try/except block
    # so that any errors result in the Template assignment being reverted
    episode_template_ids = episode.template_ids
    output: Path | None = None
    try:
        # Add the Template to the Episode IF it is not already assigned to
        # the Episode or the parent Series
        if (template_id not in episode.template_ids
            and template_id not in episode.series.template_ids):
            log.debug(f'Adding Template[{template.id}] to Episode[{episode.id}]')
            episode.assign_templates([template])
            db.commit()

        # Determine appropriate Source and Output file
        if not (source := episode.get_source_file('unique')).exists():
            log.debug('Source image does not exist, using fallback')
            source = INTERNAL_ASSET_DIRECTORY / 'preview' / 'unique.jpg'
        episode.source_file = str(source)
        output = (
            INTERNAL_ASSET_DIRECTORY
            / 'preview'
            / f'card-unique{settings.card_extension}'
        )
        output.unlink(missing_ok=True)

        # If a library is available, use the first one
        library = None
        if episode.series.libraries:
            library = episode.series.libraries[0]

        # Create Card for this Episode
        try:
            card_settings = resolve_card_settings(episode, library)
            card_settings['card_file'] = output
        except UnknownCardType as exc:
            raise HTTPException(
                status_code=422,
                detail=(
                    'Preview cards cannot be created from un-initialized card '
                    'types - save the card type and try again'
                )
            ) from exc
        except MissingSourceImage as exc:
            raise HTTPException(
                status_code=404,
                detail='Missing the required Source Image',
            ) from exc
        except (HTTPException, InvalidCardSettings) as exc:
            raise HTTPException(
                status_code=400,
                detail='Invalid Card settings',
            ) from exc

        # Delete output if it exists, then create Card
        CardClass, CardTypeModel = validate_card_type_model(card_settings)
        card_maker = CardClass(**CardTypeModel.model_dump(), preferences=settings)
        card_maker.create()
    # Post Card creation, revert Template assignment if needed
    finally:
        for attribute, value in reversions.items():
            setattr(template, attribute, value)
            log.debug(f'Template[{template.id}].{attribute} = {value}')

        if episode.template_ids != episode_template_ids:
            episode.assign_templates([
                get_template(db, tid) for tid in episode_template_ids
            ])
            db.commit()

    # Card created, return URI
    if output is not None and output.exists():
        return f'/public/preview/{output.name}'

    raise HTTPException(
        status_code=500,
        detail='Failed to create preview card'
    )


@card_router.get('/all')
def get_all_title_cards(
        db: Session = Depends(get_database),
    ) -> Page[TitleCard]: # type: ignore
    """Get all defined Title Cards."""

    return paginate(db.query(Card))


@card_router.get('/recent')
def get_recently_created_title_cards(
        db: Session = Depends(get_database),
        after: datetime = Query(...),
    ) -> Page[TitleCardExtended]: # type: ignore
    """
    Get all recently created Title Cards after the given date.

    - after: Date which to exclude Title Cards create before. 
    """

    return paginate(
        db.query(Card)
            .filter(
                Card.created > settings.config.localize(after),
                not_(Card.episode_id.is_(None))
            )
            .order_by(Card.created.desc())
    )


@card_router.get('/card/{card_id}')
def get_title_card(
        card_id: int,
        db: Session = Depends(get_database),
    ) -> TitleCard:
    """
    Get the details of the given TitleCard.

    - card_id: ID of the TitleCard to get the details of.
    """

    if not (card := db.get(Card, card_id)):
        raise HTTPException(
            status_code=404,
            detail='Title Card not found',
        )

    return card


@card_router.post('/series/{series_id}', tags=['Series'])
def create_cards_for_series(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Create the Title Cards for the given Series. This deletes and
    remakes any outdated existing Cards.

    - series_id: ID of the Series to create Title Cards for.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Set watch statuses of the Episodes
    get_watched_statuses(db, series, series.episodes)
    db.commit()

    # Create each associated Episode's Card
    for episode in series.episodes:
        try:
            create_episode_cards(db, episode)
        except Exception as exc:
            log.exception(f'{episode} Card creation failed - {exc}')


@card_router.get('/series/{series_id}', tags=['Series'])
def get_series_cards_(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> Page[TitleCard]: # type: ignore
    """
    Get all Title Cards for the given Series. Cards are returned in the
    order of their release (e.g. season number, episode number).

    - series_id: ID of the Series to get the cards of.
    """

    return paginate(
        db.query(Card)
            .filter_by(series_id=series_id)
            .join(Episode, Card.episode_id==Episode.id)
            .order_by(
                Episode.season_number,
                Episode.episode_number,
                Episode.absolute_number,
            )
    )


@card_router.get('/series/{series_id}/reduced', tags=['Series'])
def get_series_cards_reduced_models(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> Page[TitleCardReduced]: # type: ignore
    """
    Get all Title Cards for the given Series. Cards are returned in the
    order of their release (e.g. season number, episode number). This is
    a reduced return model.

    - series_id: ID of the Series to get the cards of.
    """

    return paginate(
        db.query(Card)
            .options(
                load_only(
                    Card.id,
                    Card.episode_id,
                    Card.card_file,
                    Card.filesize,
                    Card.library_name,
                ),
                contains_eager(Card.episode).load_only(
                    Episode.id,
                    Episode.season_number,
                    Episode.episode_number,
                    Episode.absolute_number,
                ),
                selectinload(Card.loaded).load_only(
                    Loaded.id,
                    Loaded.card_id,
                    Loaded.library_name,
                ),
            )
            .filter_by(series_id=series_id)
            .join(Episode, Episode.id == Card.episode_id)
            .order_by(
                Episode.season_number,
                Episode.episode_number,
                Episode.absolute_number,
                Card.library_name,
            )
    )


@card_router.get('/series/{series_id}/download', tags=['Series'])
def download_series_title_cards_zip(
        background_tasks: BackgroundTasks,
        series_id: int,
        season_number: int | None = Query(default=None),
        db: Session = Depends(get_database),
    ) -> FileResponse:
    """
    Download all Title Cards for the given Series as a zip file. Cards
    are organized in the zip file by season folders.

    - series_id: ID of the Series to download the cards of.
    - season_number: Optional season number to filter cards by. If
    provided, only cards for this season are included.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Build query for Cards
    card_query = (
        db.query(Card)
            .filter_by(series_id=series_id)
            .join(Episode, Card.episode_id == Episode.id)
    )

    # Filter by season number if provided
    if season_number is not None:
        card_query = card_query.filter(Episode.season_number == season_number)

    # Order cards by episode order
    cards = card_query.order_by(
        Episode.season_number,
        Episode.episode_number,
        Episode.absolute_number,
    ).all()

    # Check if any cards exist
    if not cards:
        raise HTTPException(
            status_code=404,
            detail='No Title Cards found for this Series'
        )

    # Create temporary zip directory
    tzip = TemporaryZip(settings.temporary_directory, background_tasks)

    # Track if any files were added
    files_added = 0

    # Add each card file to the zip
    for card in cards:
        # Skip if card file doesn't exist
        if not (card_path := card.file).exists():
            log.warning(f'Card file does not exist: {card.card_file}')
            continue

        tzip.add_file(card_path)
        files_added += 1

    # Check if any files were actually added
    if files_added == 0:
        raise HTTPException(
            status_code=404,
            detail='No Title Card files exist on disk'
        )

    log.info(f'Creating zip with {files_added} Title Cards for {series}')

    # Create and return the zip file
    zip_path = tzip.zip()
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=f'{series.path_safe_name} Title Cards.zip'
    )


@card_router.put('/series/{series_id}/load/all', deprecated=True)
def load_all_series_title_cards_(
        series_id: int,
        reload: bool = Query(default=False),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Load the Title Cards for the given Series into all libraries.

    - series_id: ID of the Series whose Cards are being loaded.
    - reload: Whether to "force" reload all Cards, even those that have
    already been loaded. If false, only Cards that have not been loaded
    previously (or that have changed) are loaded.
    """

    # Get this Series and Interface, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    load_all_series_title_cards(series, db, force_reload=reload)


@card_router.put('/series/{series_id}/load', tags=['Series'])
def load_series_title_cards_(
        series_id: int,
        interface_id: int | None = Query(default=None),
        library_name: str | None = Query(default=None),
        reload: bool = Query(default=False),
        season_number: int | None = Query(default=None),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Load the Title Cards for the given Series into the library of the
    associated interface.

    - series_id: ID of the Series whose Cards are being loaded.
    - interface_id: Optional ID of the Connection to load into.
    - library_name: Optional name of the specific library to load Cards
    into.
    - reload: Whether to "force" reload all Cards, even those that have
    already been loaded. If false, only Cards that have not been loaded
    previously (or that have changed) are loaded.
    - season_number: Optional season number to load the Title Cards for.
    If omitted, all seasons are loaded.
    """

    # Interface ID and library name must be provided together or not at all
    if bool(interface_id) != bool(library_name):
        raise HTTPException(
            status_code=422,
            detail='Both interface ID and library name must be provided'
        )

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Filter by season number if indicated
    episodes = None
    if season_number is not None:
        episodes = [
            episode for episode in series.episodes
            if episode.season_number == season_number
        ]

    # Load Title Cards into only the specified library
    if library_name and interface_id:
        interface = get_interface(interface_id, raise_exc=True)
        if not isinstance(
            interface,
            (EmbyInterface, JellyfinInterface, PlexInterface)
        ):
            raise HTTPException(
                status_code=400,
                detail='Can only load Cards into Emby, Jellyfin, or Plex'
            )

        load_series_title_cards(
            series,
            library_name,
            interface_id,
            db,
            interface,
            reload,
            episodes=episodes,
        )
    # Load Title Cards into all libraries
    else:
        load_all_series_title_cards(
            series,
            db,
            force_reload=reload,
            episodes=episodes,
        )


@card_router.put('/episode/{episode_id}/load', tags=['Episodes'])
def force_reload_episode_cards(
        episode_id: int,
        db: Session = Depends(get_database),
    ) -> None:
    """
    Reload the Title Cards associated with the given Episode. This is a
    "force" reload.

    - episode_id: ID of the Episode whose Cards to load.
    """

    # Get this Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Load Cards for all libraries
    loaded = True
    for library in episode.series.libraries:
        loaded &= load_episode_title_card(
            episode,
            db,
            library['name'],
            library['interface_id'],
            get_interface(library['interface_id']), # type: ignore
        )

    if not loaded:
        raise HTTPException(
            status_code=400,
            detail='Failed to load Title Card',
        )


@card_router.put('/card/{card_id}/load')
def reload_card(
        card_id: int,
        interface_id: int | None = Query(default=None),
        library_name: str | None = Query(default=None),
        uid: int | str | None = Query(default=None),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Reload the Title Card. This is a "force" reload.

    - card_id: ID of the Card to load.
    - interface_id: Optional ID of the Connection to load into.
    - library_name: Optional name of the specific library to load Cards
    into.
    - uid: Optional unique ID of an episode in the associated Interface
    and library to force load the given Card into. For PlexInterfaces,
    this is the RatingKey, for Emby and Jellyfin this is the item ID.
    """

    # Interface ID and library name must be provided together or not at all
    if bool(interface_id) != bool(library_name):
        raise HTTPException(
            status_code=422,
            detail='Both interface ID and library name must be provided'
        )

    # Get this Card, raise 404 if DNE
    card = get_card(db, card_id, raise_exc=True)

    # Load Title Cards into only the specified library
    if library_name and interface_id:
        loaded = load_title_card(
            card,
            db,
            library_name,
            interface_id,
            get_interface(interface_id), # type: ignore
            uid=uid,
        )
    # Load Cards for all libraries
    else:
        loaded = True
        for library in card.episode.series.libraries:
            loaded &= load_title_card(
                card,
                db,
                library['name'],
                library['interface_id'],
                get_interface(library['interface_id']), # type: ignore
            )

    if not loaded:
        raise HTTPException(
            status_code=400,
            detail='Failed to load Title Card',
        )


@card_router.get('/episode/{episode_id}', tags=['Episodes'])
def get_episode_cards(
        episode_id: int,
        db: Session = Depends(get_database),
    ) -> Page[TitleCard]:
    """
    Get all TitleCards for the given Episode.

    - episode_id: ID of the Episode to get the cards of.
    """

    return paginate(
        db.query(Card)
            .filter(Card.episode_id==episode_id)
            .order_by(Card.library_name)
    )


@card_router.delete('/series/{series_id}', tags=['Series'])
def delete_series_title_cards(
        series_id: int,
        db: Session = Depends(get_database),
    ) -> CardActions:
    """
    Delete all TitleCards for the given Series. Return a list of the
    deleted files.

    - series_id: ID of the Series whose TitleCards to delete.
    """

    # Create queries for Cards of this Series
    card_query = db.query(Card).filter_by(series_id=series_id)
    loaded_query = db.query(Loaded).filter_by(series_id=series_id)

    # Delete cards
    deleted = delete_cards(db, card_query, loaded_query)

    return CardActions(deleted=len(deleted))


@card_router.delete('/episode/{episode_id}', tags=['Episodes'])
def delete_episode_title_cards(
        episode_id: int,
        db: Session = Depends(get_database),
    ) -> CardActions:
    """
    Delete all Title Cards for the given Episode. Return a list of the
    deleted files.

    - episode_id: ID of the Episode whose TitleCards to delete.
    """

    # Create Queries for Cards of this Episode
    card_query = db.query(Card).filter_by(episode_id=episode_id)
    loaded_query = db.query(Loaded).filter_by(episode_id=episode_id)

    # Delete cards
    deleted = delete_cards(db, card_query, loaded_query)

    return CardActions(deleted=len(deleted))


@card_router.delete('/card/{card_id}')
def delete_title_card(
        card_id: int,
        db: Session = Depends(get_database),
    ) -> CardActions:
    """
    Delete the Title Card with the given ID. Also removes the associated
    Loaded object (if it exists).

    - card_id: ID of the Title Card to delete.
    """

    # Create Queries for Cards of this Episode
    card_query = db.query(Card).filter_by(id=card_id)
    loaded_query = db.query(Loaded).filter_by(id=card_id)

    # Delete cards
    deleted = delete_cards(db, card_query, loaded_query)

    return CardActions(deleted=len(deleted))


@card_router.post('/episode/{episode_id}', tags=['Episodes'])
def create_card_for_episode(
        episode_id: int,
        query_watched_statuses: bool = Query(default=False),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Create the Title Cards for the given Episode. This deletes and
    remakes the existing Title Card if it is outdated.

    - episode_id: ID of the Episode to create the Title Card for.
    - query_watched_statuses: Whether to query the watched statuses
    associated with this Episode.
    """

    # Find associated Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Set watch status of the Episode
    if query_watched_statuses:
        get_watched_statuses(db, episode.series, [episode])

    # Create Card for this Episode
    try:
        create_episode_cards(db, episode)
    except MissingSourceImage as exc:
        raise HTTPException(
            status_code=404,
            detail='Missing the required Source Image',
        ) from exc
    except InvalidCardSettings as exc:
        raise HTTPException(
            status_code=400,
            detail='Invalid Card settings',
        ) from exc


@card_router.delete('/batch')
def batch_delete_title_cards(
        series_ids: list[int] = Body(...),
        db: Session = Depends(get_database),
    ) -> CardActions:
    """
    Batch delete all the Title Cards associated with the given Series.

    - series_ids: List of IDs of Series whose Title Cards are being
    deleted.
    """

    cards = db.query(Card).filter(Card.series_id.in_(series_ids))

    return CardActions(deleted=len(delete_cards(db, cards)))


@card_router.put('/batch/load')
def batch_load_title_cards_into_all_libraries(
        series_ids: list[int] = Body(...),
        reload: bool = Query(default=False),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Batch operation to load all Title Cards for all Series into all
    libraries.

    - series_ids: IDs of the Series whose Cards are being loaded.
    - reload: Whether to "force" reload all Cards, even those that have
    already been loaded. If false, only Cards that have not been loaded
    previously (or that have changed) are loaded.
    """

    for series_id in series_ids:
        load_all_series_title_cards(
            get_series(db, series_id, raise_exc=True),
            db,
            force_reload=reload,
        )
