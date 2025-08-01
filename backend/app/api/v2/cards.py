from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import paginate as paginate_sequence
from sqlalchemy import not_
from sqlalchemy.orm import Session
import pytz

from app.db.query import (
    get_card,
    get_episode,
    get_font,
    get_interface,
    get_series
)
from app.db.pagination import Page
from app.dependencies import get_database, get_logger, get_preferences
from app.db.users import get_current_user
from app.core.cards import (
    create_episode_cards,
    delete_cards,
    get_watched_statuses,
    resolve_card_settings,
    validate_card_type_model,
    get_series_cards_with_cache,
    get_series_cards_reduced_with_cache,
    get_episode_cards_with_cache,
    get_card_with_cache,
)
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
from app.logging.logger import Logger
from app.models.card import Card
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
from modules.FormatString import FormatString
from modules.preferences import Preferences
from modules.TieredSettings import TieredSettings


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
        preferences: Preferences = Depends(get_preferences),
    ) -> str:
    """
    Create a preview title card. This uses a fixed source file and
    writes the created card only to a temporary directory. Returns a
    URI to the created card.

    - card: Card definition to create.
    """

    # Get the effective card class
    CardClass = preferences.get_card_type_class(card.card_type, log=log)
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
        'logo_file': preferences.INTERNAL_ASSET_DIRECTORY / 'logo.png',
        'poster_file': preferences.INTERNAL_ASSET_DIRECTORY / 'preview' / 'poster.webp',
        'backdrop_file': preferences.INTERNAL_ASSET_DIRECTORY / 'preview' / 'art.jpg',
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
                (card.episode_text_format or CardClass.EPISODE_TEXT_FORMAT),
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
    preview_dir = preferences.INTERNAL_ASSET_DIRECTORY / 'preview'
    source = preview_dir / (('art' if 'art' in card.style else 'unique') + '.jpg')
    output = preview_dir / f'card-{card.style}{preferences.card_extension}'

    # Resolve all settings
    card_settings = TieredSettings.new_settings(
        preferences.global_extras.get(card.card_type, {}),
        format_data,
        DefaultFont,
        preferences.card_properties,
        font_template_dict,
        {'source_file': source, 'card_file': output},
        card.model_dump(),
        card.extras,
    )

    # Add card default font stuff
    if card_settings.get('font_file') is None:
        card_settings['font_file'] = CardClass.TITLE_FONT
    if card_settings.get('font_color') is None:
        card_settings['font_color'] = CardClass.TITLE_COLOR

    # Turn manually entered \n into newline
    card_settings['title_text'] = card_settings['title_text'].replace(r'\n', '\n')

    # Apply title text case function
    if card_settings.get('font_title_case') is None:
        case_func = CardClass.CASE_FUNCTIONS[CardClass.DEFAULT_FONT_CASE]
    else:
        case_func = CardClass.CASE_FUNCTIONS[card_settings['font_title_case']]
    card_settings['title_text'] = case_func(card_settings['title_text'])

    # Delete output if it exists, then create Card
    CardClass, CardTypeModel = validate_card_type_model(card_settings, log=log)
    output.unlink(missing_ok=True)
    card_maker = CardClass(**CardTypeModel.dict(), preferences=preferences)
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
        preferences: Preferences = Depends(get_preferences),
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
    output = preferences.INTERNAL_ASSET_DIRECTORY / 'preview' \
        / f'card-unique{preferences.card_extension}'
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
    card_maker = CardClass(**CardTypeModel.dict(), preferences=preferences)
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
    """Get all recently created Title Cards after the given date."""

    # Convert to UTC timezone for DB comparison - assume after is in TZ
    # timezone if none was provided
    if after.tzinfo is None:
        after = settings.TIMEZONE.localize(after)
    after = after.astimezone(pytz.timezone('UTC'))

    return paginate(
        db.query(Card)
            .filter(Card.created > after, not_(Card.episode_id.is_(None)))
            .order_by(Card.created.desc())
    )


@card_router.get('/card/{card_id}')
def get_title_card(
        card_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> TitleCard:
    """
    Get the details of the given TitleCard.

    - card_id: ID of the TitleCard to get the details of.
    """

    return get_card_with_cache(db, card_id, log=log) or get_card(db, card_id, raise_exc=True)


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
def get_series_cards(
        series_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> Page[TitleCard]: # type: ignore
    """
    Get all Title Cards for the given Series. Cards are returned in the
    order of their release (e.g. season number, episode number).

    - series_id: ID of the Series to get the cards of.
    """

    cards = get_series_cards_with_cache(db, series_id, log=log)
    return paginate_sequence(cards)


@card_router.get('/series/{series_id}/reduced', tags=['Series'])
def get_series_cards_reduced_models(
        series_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> Page[TitleCardReduced]: # type: ignore
    """
    Get all Title Cards for the given Series. Cards are returned in the
    order of their release (e.g. season number, episode number). This is
    a reduced return model.

    - series_id: ID of the Series to get the cards of.
    """

    reduced_cards = get_series_cards_reduced_with_cache(db, series_id, log=log)
    return paginate_sequence(reduced_cards)


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


@card_router.put('/series/{series_id}/load/library', deprecated=True)
def load_series_title_cards_into_library(
        series_id: int,
        interface_id: int = Query(...),
        library_name: str = Query(...),
        reload: bool = Query(default=False),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Load the Title Cards for the given Series into the library with the
    given index.

    - series_id: ID of the Series whose Cards are being loaded.
    - interface_id: ID of the interface whose library is being loaded.
    - library_name: Name of the library in the given interface to load
    the Title Cards into.
    - reload: Whether to "force" reload all Cards, even those that have
    already been loaded. If false, only Cards that have not been loaded
    previously (or that have changed) are loaded.
    """

    # Get this Series and Interface, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)
    interface = get_interface(interface_id, raise_exc=True)

    # Verify the interface ID was a valid type
    if interface.INTERFACE_TYPE not in ('Emby', 'Jellyfin', 'Plex'):
        raise HTTPException(
            status_code=400,
            detail='Cannot load Cards into a non-media-server Connection'
        )

    # Load Cards
    load_series_title_cards(
        series, library_name, interface_id, db, interface, reload, log=log,
    )


@card_router.put('/series/{series_id}/load', tags=['Series'])
def load_series_title_cards_(
        series_id: int,
        interface_id: int | None = Query(default=None),
        library_name: str | None = Query(default=None),
        reload: bool = Query(default=False),
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
    """

    # Interface ID and library name must be provided together or not at all
    if bool(interface_id) != bool(library_name):
        raise HTTPException(
            status_code=422,
            detail='Both interface ID and library name must be provided'
        )

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Load Title Cards into only the specified library
    if library_name and interface_id:
        interface = get_interface(interface_id, raise_exc=True)
        if interface.INTERFACE_TYPE not in ('Emby', 'Jellyfin', 'Plex'):
            raise HTTPException(
                status_code=400,
                detail='Cannot load Cards into a non-media-server Connection'
            )
        # Load Cards
        load_series_title_cards(
            series, library_name, interface_id, db, interface, reload, log=log,
        )
    # Load Title Cards into all libraries
    else:
        load_all_series_title_cards(series, db, force_reload=reload, log=log)


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
        log: Logger = Depends(get_logger),
    ) -> Page[TitleCard]: # type: ignore
    """
    Get all TitleCards for the given Episode.

    - episode_id: ID of the Episode to get the cards of.
    """

    cards = get_episode_cards_with_cache(db, episode_id, log=log)
    return paginate(cards)


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
            detail=f'Invalid Card settings',
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
