from datetime import datetime

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
from sqlalchemy.orm import Session, load_only

from app.db.query import (
    get_card,
    get_episode,
    get_font,
    get_interface,
    get_series
)
from app.db.pagination import Page
from app.dependencies import get_database, get_logger
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
from app.info.episode import EpisodeInfo
from app.interfaces.v2 import EmbyInterface, JellyfinInterface, PlexInterface
from app.logging.logger import Logger
from app.models.card import Card
from app.models.episode import Episode
from app.models.loaded import Loaded
from app.schemas.card import (
    CardActions,
    PreviewTitleCard,
    TitleCard,
    TitleCardExtended,
    TitleCardReduced,
)
from app.schemas.episode import UpdateEpisode
from app.schemas.font import DefaultFont
from app.schemas.series import UpdateSeries
from app.settings import settings
from app.utils.fstring import FormatString
from app.utils.tiered_settings import TieredSettings
from app.utils.tzip import TemporaryZip


# Create sub router for all /cards API requests
card_router = APIRouter(
    prefix='/cards',
    tags=['Title Cards'],
    dependencies=[Depends(get_current_user)],
)


@card_router.post('/preview')
def create_preview_card(
        card: PreviewTitleCard = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> str:
    """
    Create a preview title card. This uses a fixed source file and
    writes the created card only to a temporary directory. Returns a
    URI to the created card.

    - card: Card definition to create.
    """

    # Get the effective card class
    CardClass = settings.get_card_type_class(card.card_type, log=log)
    if CardClass is None:
        raise HTTPException(
            status_code=400,
            detail=(
                'Cannot create previews for Remote Card Types which have not '
                'been saved first - save this change and try again'
            ),
        )

    # Fake data
    format_data = {
        'series_full_name': 'Test Series (2020)', 'series_name': 'Test Series',
        'season_episode_max': 10, 'series_episode_max': 20,
        'logo_file': INTERNAL_ASSET_DIRECTORY / 'logo.png',
        'poster_file': INTERNAL_ASSET_DIRECTORY / 'preview' / 'poster.webp',
        'backdrop_file': INTERNAL_ASSET_DIRECTORY / 'preview' / 'art.jpg',
    }

    # Get preview season and episode text
    if card.season_text is None:
        # Apply season text formatting if indicated
        try:
            if getattr(CardClass, 'SEASON_TEXT_FORMATTER', None) is None:
                card.season_text = FormatString(
                    'Season {season_number}',
                    data=format_data | card.model_dump(),
                ).result
            else:
                fake_ei = EpisodeInfo(
                    title=card.title_text, season_number=card.season_number,
                    episode_number=card.episode_number,
                    absolute_number=card.absolute_number
                )
                card.season_text = FormatString(
                    getattr(CardClass, 'SEASON_TEXT_FORMATTER')(fake_ei),
                    data=format_data | card.model_dump(),
                ).result
        except InvalidCardSettings as exc:
            raise HTTPException(
                status_code=400,
                detail='Invalid season text format',
            ) from exc
    if card.episode_text is None:
        try:
            card.episode_text = FormatString(
                (
                    card.episode_text_format
                    or CardClass.CardConfig.episode_text_format
                ),
                data=format_data | card.model_dump(),
            ).result
        except InvalidCardSettings as exc:
            raise HTTPException(
                status_code=400,
                detail='Invalid episode text format',
            ) from exc

    # Get Font if indicated
    font_template_dict = {}
    if getattr(card, 'font_id', None) is not None and card.font_id:
        font = get_font(db, card.font_id, raise_exc=True)
        font_template_dict = font.card_properties

    # Determine appropriate Source and Output file
    preview_dir = INTERNAL_ASSET_DIRECTORY / 'preview'
    source = preview_dir / (('art' if 'art' in card.style else 'unique') + '.jpg')
    output = preview_dir / f'card-{card.style}{settings.card_extension}'

    # Resolve all settings
    card_settings = TieredSettings.new_settings(
        settings.global_extras.get(card.card_type, {}),
        format_data,
        DefaultFont,
        settings.card_properties,
        font_template_dict,
        {'source_file': source, 'card_file': output},
        card.model_dump(),
        card.extras,
    )

    # Add card default font stuff
    if card_settings.get('font_file') is None:
        card_settings['font_file'] = str(CardClass.CardConfig.font_file)
    if card_settings.get('font_color') is None:
        card_settings['font_color'] = CardClass.CardConfig.font_color

    # Turn manually entered \n into newline
    card_settings['title_text'] = card_settings['title_text'].replace(r'\n', '\n')

    # Apply title text case function
    if card_settings.get('font_title_case') is None:
        case_func = CardClass.CASE_FUNCTIONS[CardClass.CardConfig.font_case]
    elif card_settings['font_title_case'] in CardClass.CASE_FUNCTIONS:
        case_func = CardClass.CASE_FUNCTIONS[card_settings['font_title_case']]
    else:
        case_func = CardClass.CASE_FUNCTIONS[CardClass.CardConfig.font_case]
    card_settings['title_text'] = case_func(card_settings['title_text'])

    # Delete output if it exists, then create Card
    CardClass, CardTypeModel = validate_card_type_model(card_settings, log=log)
    output.unlink(missing_ok=True)
    card_maker = CardClass(**CardTypeModel.model_dump(), preferences=settings)
    card_maker.create()

    # Card created, return URI
    if output.exists():
        return f'/public/preview/{output.name}'

    raise HTTPException(
        status_code=500,
        detail='Failed to create preview card'
    )


@card_router.post('/preview/episode/{episode_id}', tags=['Episodes'])
def create_preview_card_for_episode(
        episode_id: int,
        update_episode: UpdateEpisode = Body(...),
        update_series: UpdateSeries = Body(...),
        query_watched_statuses: bool = Query(default=False),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> str:
    """
    Create a preview Title Card for the given Episode.

    - episode_id: ID of the Episode to create the Title Card for.
    
    - query_watched_statuses: Whether to query the watched statuses
    associated with this Episode.
    """

    # Find associated Episode, raise 404 if DNE
    episode = get_episode(db, episode_id, raise_exc=True)

    # Raise exception if Template IDs are part of update object; cannot
    # be reflected in the live preview because relationship objects will
    # not be reflected until a database commit
    if (getattr(update_episode, 'template_ids', []) != episode.template_ids or
        getattr(update_series,'template_ids',[]) !=episode.series.template_ids):
        raise HTTPException(
            status_code=422,
            detail=(
                'Preview Cards cannot reflect Template changes - save these '
                'changes and try again'
            )
        )

    update_episode_config(db, episode, update_episode, log=log)
    update_series_config(db, episode.series, update_series, commit=False, log=log)

    # Set watch status(es) of the Episode
    if query_watched_statuses:
        get_watched_statuses(db, episode.series, [episode], log=log)

    # Determine appropriate Source and Output file
    output = (
        INTERNAL_ASSET_DIRECTORY
        / 'preview'
        / f'card-unique{settings.card_extension}'
    )
    output.unlink(missing_ok=True)

    # Create Card for this Episode
    library = None
    if episode.series.libraries:
        library = episode.series.libraries[0]

    try:
        card_settings = resolve_card_settings(episode, library, log=log)
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
    CardClass, CardTypeModel = validate_card_type_model(card_settings, log=log)
    card_maker = CardClass(**CardTypeModel.model_dump(), preferences=settings)
    card_maker.create()

    # Card created, return URI
    if output.exists():
        return f'/public/preview/{output.name}'

    card_maker.image_magick.print_command_history(log=log)
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
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Create the Title Cards for the given Series. This deletes and
    remakes any outdated existing Cards.

    - series_id: ID of the Series to create Title Cards for.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Set watch statuses of the Episodes
    get_watched_statuses(db, series, series.episodes, log=log)
    db.commit()

    # Create each associated Episode's Card
    for episode in series.episodes:
        try:
            create_episode_cards(db, episode, log=log)
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
                )
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
        log: Logger = Depends(get_logger),
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

        tzip.add_file(card_path, log=log)
        files_added += 1

    # Check if any files were actually added
    if files_added == 0:
        raise HTTPException(
            status_code=404,
            detail='No Title Card files exist on disk'
        )

    log.info(f'Creating zip with {files_added} Title Cards for {series}')

    # Create and return the zip file
    zip_path = tzip.zip(log=log)
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
        log: Logger = Depends(get_logger),
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

    load_all_series_title_cards(series, db, force_reload=reload, log=log)


@card_router.put('/series/{series_id}/load', tags=['Series'])
def load_series_title_cards_(
        series_id: int,
        interface_id: int | None = Query(default=None),
        library_name: str | None = Query(default=None),
        reload: bool = Query(default=False),
        season_number: int | None = Query(default=None),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
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
            log=log,
        )
    # Load Title Cards into all libraries
    else:
        load_all_series_title_cards(
            series,
            db,
            force_reload=reload,
            episodes=episodes,
            log=log,
        )


@card_router.put('/episode/{episode_id}/load', tags=['Episodes'])
def force_reload_episode_cards(
        episode_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
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
            log=log,
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
        log: Logger = Depends(get_logger),
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
            log=log,
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
                log=log,
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
        log: Logger = Depends(get_logger),
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
    deleted = delete_cards(db, card_query, loaded_query, log=log)

    return CardActions(deleted=len(deleted))


@card_router.delete('/episode/{episode_id}', tags=['Episodes'])
def delete_episode_title_cards(
        episode_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
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
    deleted = delete_cards(db, card_query, loaded_query, log=log)

    return CardActions(deleted=len(deleted))


@card_router.delete('/card/{card_id}')
def delete_title_card(
        card_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
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
    deleted = delete_cards(db, card_query, loaded_query, log=log)

    return CardActions(deleted=len(deleted))


@card_router.post('/episode/{episode_id}', tags=['Episodes'])
def create_card_for_episode(
        episode_id: int,
        query_watched_statuses: bool = Query(default=False),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
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
        get_watched_statuses(
            db, episode.series, [episode], log=log,
        )

    # Create Card for this Episode
    try:
        create_episode_cards(db, episode, log=log)
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
        log: Logger = Depends(get_logger),
    ) -> CardActions:
    """
    Batch delete all the Title Cards associated with the given Series.

    - series_ids: List of IDs of Series whose Title Cards are being
    deleted.
    """

    cards = db.query(Card)\
        .filter(Card.series_id.in_(series_ids))

    return CardActions(deleted=len(delete_cards(db, cards, log=log)))


@card_router.put('/batch/load')
def batch_load_title_cards_into_all_libraries(
        series_ids: list[int] = Body(...),
        reload: bool = Query(default=False),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
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
            log=log,
        )
