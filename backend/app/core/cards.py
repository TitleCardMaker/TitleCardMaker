from pathlib import Path
from time import sleep
from typing import Any, cast

from app.schemas.schedule import Hours
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import OperationalError, PendingRollbackError
from sqlalchemy.orm import Query, Session, load_only
from sqlalchemy.orm.session import object_session

from app.cards.base import BaseCardType
from app.cards.episode_ranges import SeasonTitleRanges
from app.cards.loader import RemoteCardType, RemoteFile
from app.cards.title import Title
from app.cards.types import BUILTIN_CARD_TYPES
from app.core.availability import expire_cache, get_remote_card_hash
from app.core.cache import cache_result, invalidate_card_cache
from app.core.episodes import refresh_episode_data
from app.core.sources import download_episode_source_images
from app.core.templates import get_effective_templates
from app.core.translate import translate_episode
from app.db.query import get_font, get_media_interface
from app.dependencies import get_database
from app.exceptions import (
    InvalidCardSettings,
    InvalidFormatString,
    MissingSourceImage,
    UnknownCardType,
)
from app.logging.logger import Logger, log
from app.models.card import Card
from app.models.episode import Episode
from app.models.font import Font
from app.models.loaded import Loaded
from app.models.series import Library, Series
from app.models.template import Template
from app.schemas.base import Base, BaseCardModel
from app.schemas.font import DefaultFont
from app.schemas.card import NewTitleCard, TitleCardReduced
from app.schemas.card_type import LocalCardTypeModels
from app.settings import settings
from app.utils.fstring import FormatString
from app.utils.paths import CleanPath
from app.utils.tiered_settings import TieredSettings


def create_all_title_cards(*, log: Logger = log) -> None:
    """
    Schedule-able function to re/create all Title Cards for all Series
    and Episodes in the Database.

    Args:
        log: Logger for all log messages.
    """

    with next(get_database()) as db:
        # Get all Series
        failures = 0 
        for series in db.query(Series).filter(Series.status !='disabled').all():
            log.trace(f'Starting to process {series}')
            try:
                # Refresh Episode data if Series is monitored
                if series.status == 'monitored':
                    try:
                        refresh_episode_data(
                            db, series, refresh_all_ids=True, log=log
                        )
                    except HTTPException:
                        log.exception(f'Cannot refresh Episode data of {series}')
                else:
                    log.trace(
                        f'{series} is unmonitored, not refreshing Episode '
                        f'data'
                    )

                # Set watch statuses of all Episodes
                try:
                    get_watched_statuses(db, series,series.episodes,log=log)
                except HTTPException as exc:
                    log.debug(
                        f'Cannot query watched statuses of {series} - {exc}'
                    )

                # Add translations if monitored
                if series.status == 'monitored':
                    for episode in series.episodes:
                        translate_episode(db, episode, commit=False, log=log)
                    db.commit()
                else:
                    log.trace(f'{series} is unmonitored, skipping translations')

                # Download Source Images
                if series.status == 'monitored':
                    for episode in series.episodes:
                        download_episode_source_images(
                            db, episode, raise_exc=False, log=log
                        )
                    db.commit()
                else:
                    log.trace(
                        f'{series} is unmonitored, skipping Source Image '
                        f'selection'
                    )

                # Create Cards for all Episodes
                for episode in series.episodes:
                    try:
                        create_episode_cards(
                            db, episode, raise_exc=False, log=log
                        )
                    except InvalidCardSettings:
                        log.trace(f'{episode} - skipping Card creation')
                        continue
                    except HTTPException as exc:
                        if exc.status_code != 404:
                            log.exception(f'{episode} - skipping Card')
            except (PendingRollbackError, OperationalError):
                if failures > 10:
                    log.exception('Database is extremely busy, stopping Task')
                    break
                failures += 1
                log.exception('Database is busy, sleeping..')
                sleep(30)
            except Exception as exc:
                if failures > 10:
                    log.critical('Many errors have occurred - exiting')
                    raise exc 

                failures += 1
                log.exception('Error ocurred while processing Series')
                sleep(10)


def clean_database(*, log: Logger = log) -> None:
    """
    Schedule-able function to remove bad / stale Loaded objects from the
    database.

    Args:
        log: Logger for all log messages.
    """

    with next(get_database()) as db:
        # Delete Loaded assets with no associated Card
        bad_loaded = db.query(Loaded).filter(Loaded.card_id.is_(None))
        if (bad_count := bad_loaded.count()) > 0:
            log.debug(f'Deleting {bad_count} outdated Loaded records')
            bad_loaded.delete()
        db.commit()

        # Delete Cards with no Series ID, Series, Episode ID, or Episode
        unlinked_cards = db.query(Card)\
            .filter(or_(Card.episode_id.is_(None),
                        Card.series_id.is_(None)))\
            .all()
        unlinked_cards += [
            card for card in db.query(Card)
            if card.episode is None or card.series is None
        ]
        for card in set(unlinked_cards):
            log.debug(f'Deleting unlinked {card}')
            card.file.unlink(missing_ok=True)
            db.delete(card)
        db.commit()

        # Delete Episodes with no Series ID, or Series
        for episode in db.query(Episode).all():
            if episode.series_id is None or episode.series is None:
                log.debug(f'Deleting unlinked Episode {episode.id}')
                db.delete(episode)
        db.commit()

        # Delete Episodes which are duplicates
        subquery = db\
            .query(
                Episode.series_id,
                Episode.season_number,
                Episode.episode_number,
                func.min(Episode.id).label('min_id')
            )\
            .group_by(
                Episode.series_id,
                Episode.season_number,
                Episode.episode_number
            )\
            .subquery()
        to_delete = db.query(Episode).filter(
            Episode.series_id == subquery.c.series_id,
            Episode.season_number == subquery.c.season_number,
            Episode.episode_number == subquery.c.episode_number,
            Episode.id != subquery.c.min_id,
        )
        for episode in to_delete.all():
            log.trace(f'Deleting duplicate Episode {episode}')
            db.delete(episode)
        db.commit()

        # Delete duplicate Cards
        if not settings.library_unique_cards:
            subquery = db\
                .query(
                    Card.episode_id,
                    func.max(Card.id).label('max_id'),
                )\
                .group_by(Card.episode_id)\
                .subquery()
            to_delete = db.query(Card).filter(
                Card.episode_id == subquery.c.episode_id,
                Card.id != subquery.c.max_id,
            )
            for card in to_delete.all():
                log.debug(f'Deleting duplicate {card}')
                card.file.unlink(missing_ok=True)
                db.delete(card)
            db.commit()


def refresh_all_card_types(*, log: Logger = log) -> None:
    """
    Schedule-able function to refresh all specified RemoteCardTypes.

    Args:
        log: Logger for all log messages.
    """

    settings.parse_local_card_types(log=log)

    with next(get_database()) as db:
        refresh_remote_card_types(db, reset=True, log=log)


def refresh_remote_card_types(
        db: Session,
        reset: bool = False,
        *,
        log: Logger = log,
    ) -> None:
    """
    Refresh all specified RemoteCardTypes. This re-downloads all
    RemoteCardType and RemoteFile files.

    Args:
        db: Database to query for remote card type identifiers.
        reset: Whether to reset the existing RemoteFile database.
        log: Logger for all log messages.
    """

    # Function to get all unique card types for the table model
    def _get_unique_card_types(
        model: type[Episode] | type[Series] | type[Template]
    ) -> set[str]:
        return set(obj[0] for obj in db.query(model.card_type).distinct().all())

    # Get all card types globally, from Templates, Series, and Episodes
    card_identifiers = {settings.default_card_type} \
        | _get_unique_card_types(Template) \
        | _get_unique_card_types(Series) \
        | _get_unique_card_types(Episode)

    # Reset loaded remote file(s)
    if reset:
        RemoteFile.reset_loaded_database()
        expire_cache()

    # Refresh all remote card types
    for card_identifier in card_identifiers:
        # Skip blank identifiers, and builtin or local cards
        if (card_identifier is None
            or card_identifier in BUILTIN_CARD_TYPES
            or card_identifier in settings.local_card_types
        ):
            continue

        # If not resetting, skip already loaded types
        if not reset and card_identifier in settings.remote_card_types:
            continue

        # Get reference hash of card
        if not (card_hash := get_remote_card_hash(card_identifier, log=log)):
            log.error(
                f'Cannot validate RemoteCardType[{card_identifier}] - skipping'
            )
            continue

        # Load new type
        log.debug(f'Loading RemoteCardType[{card_identifier}]..')
        card_type = RemoteCardType(card_identifier, card_hash, log=log)
        if card_type.valid and card_type is not None and card_type.card_class:
            settings.remote_card_types[card_identifier] =card_type.card_class


def _card_type_model_to_json(model: Base) -> dict:
    """
    Convert the given Pydantic card type model to JSON (dict) for
    comparison and storing in the Card.model_json Column.

    Args:
        model: Pydantic model to convert.

    Returns:
        JSON conversion of the model (as a dict). All default variables
        are excluded, as well as the `source_file` and `card_file`
        variables.
    """

    return {
        key: str(val.name) if isinstance(val, Path) else str(val)
        for key, val in
        model.model_dump(
            exclude_defaults=True,
            exclude={'source_file', 'card_file'},
        ).items()
    }


def add_card_to_database(
        db: Session,
        card_model: NewTitleCard,
        CardTypeModel: Base,
        card_file: Path,
        library: Library | None,
        *,
        commit: bool = True,
    ) -> Card:
    """
    Add the given Card to the Database.

    Args:
        db: Database to add the Card entry to.
        card_model: NewTitleCard model being added to the Database.
        CardTypeModel: Pydantic model containing the card JSON to store.
        card_file: Path to the Card associated with the given model
            being added to the Database.
        library: Library the Card is associated with.
        commit: Whether to commit the Database transaction.

    Returns:
        Card entry created within the Database.
    """

    # Add Card to database
    card_model.filesize = card_file.stat().st_size
    card = Card(
        **card_model.model_dump(),
        model_json=_card_type_model_to_json(CardTypeModel),
    )
    db.add(card)

    # Add library details if provided
    if library:
        card.interface_id = library['interface_id']
        card.library_name = library['name']
    if commit:
        db.commit()

    return card


def validate_card_type_model(
        card_settings: dict,
        *,
        log: Logger = log,
    ) -> tuple[type[BaseCardType], Base]:
    """
    Validate the given Card settings into the associated Pydantic model
    and BaseCardType class.

    Args:
        card_settings: Dictionary of Card settings.
        log: Logger for all log messages.

    Returns:
        Tuple of the `BaseCardType` class (to create the card) and the
        Pydantic model of that card (to validate the card parameters).
    """

    # Initialize class of the card type being created
    CardClass = settings.get_card_type_class(
        card_settings['card_type'], log=log
    )
    if CardClass is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f'Cannot create Card - invalid card type '
                f'{card_settings["card_type"]}'
            ),
        )

    # Get Pydantic model for this card type
    if card_settings['card_type'] in LocalCardTypeModels:
        CardTypeModel = LocalCardTypeModels[card_settings['card_type']]
    # Remove card types
    elif hasattr(CardClass, 'CardModel'):
        CardTypeModel = cast(type[Base], CardClass.CardModel) # type: ignore
    else:
        raise HTTPException(
            status_code=400,
            detail='Cannot create Card - invalid card class'
        )

    try:
        return CardClass, CardTypeModel(**card_settings)
    except ValidationError as exc:
        log.exception('Card validation failed')
        raise HTTPException(
            status_code=400,
            detail=exc.errors(),
        )
    except Exception as exc:
        log.exception('Card validation failed')
        raise HTTPException(
            status_code=400,
            detail=f'Cannot create Card - invalid card settings ({exc})',
        ) from exc


def create_card(
        db: Session,
        card_model: NewTitleCard,
        CardClass: type[BaseCardType],
        CardTypeModel: BaseCardModel,
        library: Library | None,
        *,
        log: Logger = log,
    ) -> Card | None:
    """
    Create the given Card, adding the resulting entry to the Database.

    Args:
        db: Database to add the Card entry to.
        card_model: TitleCard model to update and add to the Database.
        CardClass: Class to initialize for Card creation.
        CardTypeModel: Pydantic model for this Card to pass the
            attributes of to the CardClass.
        library: Library associated with Card.
        log: Logger for all log messages.

    Returns:
        The created Card, or None if the Card creation failed.
    """

    # Create Card
    card_maker = CardClass(**CardTypeModel.model_dump())
    card_maker.create()

    # If file exists, card was created successfully - add to database
    if (card_file := CardTypeModel.card_file).exists():
        card = add_card_to_database(
            db, card_model, CardTypeModel, card_file, library, commit=True
        )
        log.info(f'Created {card}')

        return card

    log.warning(f'Card creation failed')
    card_maker.image_magick.print_command_history(log=log)
    return None


def resolve_card_settings(
        episode: Episode,
        library: Library | None = None,
        *,
        log: Logger = log,
    ) -> dict:
    """
    Resolve the Title Card settings for the given Episode. This evalutes
    all global, Series, and Template overrides.

    Args:
        episode: Episode whose Card settings are being resolved.
        library: Library associated with this Card.
        log: Logger for all log messages.

    Returns:
        The resolved Card settings as a dictionary.

    Raises:
        HTTPException (404): A specified Template or Font is missing.
        MissingSourceImage: The required Source Image is missing.
        UnknownCardType: The indicated card type is unknown/invalid.
            Most likely this is a remote card type which needs to be
            downloaded.
    """

    # Get effective Template(s) for this Series and Episode
    series = episode.series
    global_template, series_template, episode_template =get_effective_templates(
        series, episode, library
    )

    global_template_dict, series_template_dict, episode_template_dict = {},{},{}
    if global_template is not None:
        global_template_dict = global_template.card_properties
    if series_template is not None:
        series_template_dict = series_template.card_properties
    if episode_template is not None:
        episode_template_dict = episode_template.card_properties

    # Determine the card type
    card_type: str = TieredSettings.resolve_singular_setting(
        settings.default_card_type,
        global_template_dict.get('card_type'),
        series_template_dict.get('card_type'),
        series.card_type,
        episode_template_dict.get('card_type'),
        episode.card_type,
    )

    # Get effective Font for this Series and Episode
    global_font_dict, series_font_dict, episode_font_dict = {}, {}, {}
    if episode.font:
        episode_font_dict = episode.font.card_properties
    elif episode_template and episode_template.font:
        episode_font_dict = episode_template.font.card_properties
    elif series.font:
        series_font_dict = series.font.card_properties
    elif series_template and series_template.font:
        series_font_dict = series_template.font.card_properties
    elif global_template and global_template.font:
        global_font_dict = global_template.font.card_properties
    elif settings.default_fonts.get(card_type) is not None:
        global_font_dict = get_font(
            object_session(episode), # type: ignore
            settings.default_fonts[card_type],
            raise_exc=True,
        ).card_properties

    # Resolve all settings from global -> Episode
    card_settings: dict[str, Any] = TieredSettings.new_settings(
        {'hide_season_text': False, 'hide_episode_text': False},
        DefaultFont,
        settings.card_properties,
        {
            'logo_file': series.get_logo_file(
                episode.season_number
                if episode.series.use_per_season_assets
                else None,
                fallback=True,
            ),
            'backdrop_file': series.get_backdrop_file(
                episode.season_number
                if episode.series.use_per_season_assets
                else None,
                fallback=True,
            ),
            'poster_file': series.get_series_poster()
        },
        global_template_dict,
        global_font_dict,
        series_template_dict,
        series_font_dict,
        series.card_properties,
        episode_template_dict,
        episode_font_dict,
        episode.get_card_properties(library),
        # Always-present base settings
        base={'absolute_number': None, 'airdate': None},
    )

    # Resolve all extras
    card_extras = TieredSettings.new_settings(
        settings.global_extras.get(card_settings['card_type'], {}),
        global_template_dict.get('extras', {}),
        series_template_dict.get('extras', {}),
        series.extras, # type: ignore
        episode_template_dict.get('extras', {}),
        episode.extras, # type: ignore
    )

    # Override settings with extras, and merge translations into extras
    TieredSettings(card_extras, episode.translations)
    TieredSettings(card_settings, card_extras)
    card_settings['extras'] = card_extras | episode.translations

    # Resolve logo file format string if indicated
    logo_file = Path(card_settings['logo_file'])
    filename = FormatString.new(
        logo_file.stem,
        data=card_settings,
        name='logo filename',
        series=series, episode=episode, log=log,
    )
    card_settings['logo_file'] = series.source_directory \
        / f'{filename}{logo_file.suffix}'

    # Get the effective card class
    CardClass = settings.get_card_type_class(
        card_settings['card_type'], log=log
    )
    if CardClass is None:
        raise UnknownCardType(card_settings['card_type'])

    # Add card default font stuff
    if card_settings.get('font_file', None) is None:
        card_settings['font_file'] = CardClass.CardConfig.font_file
    if card_settings.get('font_color', None) is None:
        card_settings['font_color'] = CardClass.CardConfig.font_color

    # Resolve auto color detection
    if (card_settings['font_color'] in ('{logo_color}', '{logo_color_no_white}')
        or 'get_image_color(' in str(card_settings['font_color'])
    ):
        # Substitute actual function calls for the common variables
        if card_settings['font_color'] == '{logo_color}':
            card_settings['font_color'] = (
                '{get_image_color(logo_file, '
                + 'fallback=' + repr(CardClass.CardConfig.font_color) + ''
                + ')}'
            )
        elif card_settings['font_color'] == '{logo_color_no_white}':
            card_settings['font_color'] = (
                '{get_image_color(logo_file, '
                + 'fallback=' + repr(CardClass.CardConfig.font_color) + ', '
                + 'white_threshold=210'
                + ')}'
            )

        # Perform actual FormatString resolution
        card_settings['font_color'] = FormatString.new(
            str(card_settings['font_color']),
            data=card_settings,
            name='font color',
            series=series,
            episode=episode,
            log=log,
        )

    # Apply Font pre-replacements
    repl_in = list(CardClass.CardConfig.font_replacements.keys())
    repl_out = list(CardClass.CardConfig.font_replacements.values())
    if card_settings.get('font_replacements_in', []):
        repl_in = card_settings['font_replacements_in']
    if card_settings.get('font_replacements_out', []):
        repl_out = card_settings['font_replacements_out']
    card_settings['title'] = Font.apply_replacements(
        card_settings['title'], repl_in, repl_out, pre=True
    )

    # Determine effective title text
    if card_settings.get('auto_split_title', True):
        card_settings['title_text'] = Title(card_settings['title']).split(
            *CardClass.get_title_split_characteristics(
                CardClass.CardConfig.title_max_line_width,
                CardClass.CardConfig.title_max_line_count,
                CardClass.CardConfig.title_split_style,
                CardClass.CardConfig.font_file,
                card_settings
            )
        )
    else:
        card_settings['title_text'] = card_settings['title'].replace('\\n','\n')

    # Apply title text case function
    if card_settings.get('font_title_case') is None:
        case_func = CardClass.CASE_FUNCTIONS[CardClass.CardConfig.font_case]
    else:
        case_func = CardClass.CASE_FUNCTIONS[card_settings['font_title_case']]
    card_settings['title_text'] = case_func(card_settings['title_text'])

    # Apply Font post-replacements
    card_settings['title_text'] = Font.apply_replacements(
        card_settings['title_text'], repl_in, repl_out, pre=False,
    )

    # Apply title text format if indicated
    if (title_format := card_settings.pop('title_text_format', None)) is not None:
        card_settings['title_text'] = FormatString.new(
            title_format, data=card_settings,
            name='title text format', series=series, episode=episode, log=log
        )

    # Add season title specification
    episode_info = episode.as_episode_info
    season_title_ranges = SeasonTitleRanges(
        card_settings.get('season_titles', {}),
        fallback=getattr(CardClass, 'SEASON_TEXT_FORMATTER', None),
        log=log,
    )
    card_settings['season_title'] = season_title_ranges.get_season_text(
        episode_info, card_settings,
    )

    # If no season text was indicated, determine
    if card_settings.get('season_text') is None:
        # Season text defaults to the season title
        card_settings['season_text'] = card_settings['season_title']

        # If a custom season text format was provided, use
        if (stf := card_settings.pop('season_text_format', None)) is not None:
            card_settings['season_text'] = FormatString.new(
                stf, data=card_settings, name='season text format',
                series=series, episode=episode, log=log,
            )
    card_settings['season_text'] = card_settings['season_text'].replace('\\n','\n')

    # If no episode text was indicated, determine using ETF
    if card_settings.get('episode_text') is None:
        card_settings['episode_text'] = FormatString.new(
            card_settings.pop(
                'episode_text_format', CardClass.CardConfig.episode_text_format,
            ),
            data=card_settings,
            name='episode text format', series=series, episode=episode, log=log,
        )
    card_settings['episode_text'] = card_settings['episode_text'].replace('\\n','\n')

    # Determine watched status and style toggles; if there is a library
    # then use it to determine the individual watched status
    if library:
        watched = episode.get_watched_status(
            library['interface_id'], library['name']
        )
        style = card_settings[
            'watched_style' if watched is True else 'unwatched_style'
        ]
    # No library present, determine watched status by total watched
    # status of all libraries (or default if indeterminate)
    else:
        if (watched := episode.is_completely_watched or None) is None:
            if card_settings['watched_style']==card_settings['unwatched_style']:
                style = card_settings['watched_style']
            else:
                style = 'unique'
        else:
            style = card_settings[('' if watched else 'un') + 'watched_style']
    card_settings['blur'] = 'blur' in style
    card_settings['grayscale'] = 'grayscale' in style

    # Add source file
    if card_settings.get('source_file') is None:
        card_settings['source_file'] = episode.get_source_file(
            card_settings['watched_style' if watched else 'unwatched_style'],
        )
    else:
        card_settings['source_file'] = CleanPath(
            settings.source_directory \
                / series.path_safe_name \
                / FormatString.new(
                    card_settings['source_file'],
                    data=card_settings,
                    name='source file format',
                    series=series,
                    episode=episode,
                    log=log,
                )
            ).sanitize()

    # Exit if the source file does not exist
    if (CardClass.CardConfig.uses_source_images
        and not card_settings['source_file'].exists()):
        log.debug((
            f'{episode} Card source image ({card_settings["source_file"]}) is '
            f'missing'
        ))
        raise MissingSourceImage

    # Get card folder
    if card_settings.get('directory') is None:
        series_directory = Path(settings.card_directory) \
            / series.path_safe_name
    else:
        series_directory = Path(card_settings['directory'][:254])

    # If an explicit card file was indicated, use it vs. default
    if card_settings.get('card_file') is None:
        card_settings['title'] = card_settings['title'].replace('\\n', '')
        filename = FormatString.new_path(
            card_settings.pop('card_filename_format'), data=card_settings,
            name='title card filename', series=series, episode=episode, log=log,
        )
        # Add library-specific identifier to filename if indicated
        if library is not None and settings.library_unique_cards:
            filename += f' [{library["interface"]} {library["name"]}]'
        card_settings['card_file'] = series_directory \
            / settings.get_folder_format(episode_info) \
            / filename
    else:
        card_settings['card_file'] = series_directory \
            / settings.get_folder_format(episode_info) \
            / CleanPath.sanitize_name(card_settings['card_file'])

    # Add extension if needed
    card_file_name = card_settings['card_file'].name
    if not card_file_name.endswith(settings.config.VALID_IMAGE_EXTENSIONS):
        new_name = card_file_name + settings.card_extension
        card_settings['card_file'] = card_settings['card_file'].parent /new_name
    card_settings['card_file'] =CleanPath(card_settings['card_file']).sanitize()

    # Perform any card-class specific format string evaluations
    card_settings = CardClass.resolve_format_strings(card_settings)

    # Perform any generic format string evaluations
    for key, value in card_settings.items():
        if isinstance(value, str) and '{' in value and '}' in value:
            key_name = str(key).replace('_', ' ')
            try:
                card_settings[key] = FormatString.new(
                    value,
                    data=card_settings,
                    name=key_name,
                    series=series,
                    episode=episode,
                    log=log,
                )
            except InvalidFormatString:
                log.debug(f'Cannot parse {key_name} as a FormatString')
                continue

    return card_settings


def create_episode_card(
        db: Session,
        episode: Episode,
        library: Library | None,
        *,
        raise_exc: bool = True,
        log: Logger = log,
    ) -> Card | None:
    """
    Create the singular Title Card for the given Episode in the given
    library.

    Args:
        db: Database to query and update.
        episode: Episode whose Cards are being created.
        raise_exc: Whether to raise any HTTPExceptions.
        log: Logger for all log messages.

    Returns:
        The created Card, or None if the Card creation failed.

    Raises:
        HTTPException: If the card settings are invalid and `raise_exc`
            is True.
        InvalidCardSettings: If the card settings are invalid and
            `raise_exc` is True.
    """

    # Resolve Card settings
    series = episode.series
    try:
        card_settings = resolve_card_settings(episode, library, log=log)
    except (HTTPException, InvalidCardSettings) as exc:
        if raise_exc:
            raise exc
        return None

    # Get a validated card class, and card type Pydantic model
    CardClass, CardTypeModel = validate_card_type_model(card_settings, log=log)

    # Create NewTitleCard object for these settings
    card = NewTitleCard(
        **card_settings,
        series_id=series.id,
        episode_id=episode.id,
    )

    # Create Card parent directories if needed
    card_settings['card_file'].parent.mkdir(parents=True, exist_ok=True)

    # Find existing Card
    existing_card: Card | None = None
    # Library unique mode is disabled, look for any Card for this Episode
    if not settings.library_unique_cards or not library:
        existing_card = db.query(Card).filter_by(episode_id=episode.id).first()
    elif library:
        # Look for Card associated with this library OR no library (if
        # the library was just added to the Series)
        existing_card = (
            db.query(Card)
                .filter(Card.episode_id==episode.id,
                        or_(and_(Card.interface_id==library['interface_id'],
                                 Card.library_name==library['name']),
                            and_(Card.interface_id.is_(None),
                                 Card.library_name.is_(None))))
                .first()
        )

    # No existing Card, begin creation
    if not existing_card:
        return create_card(db, card, CardClass, CardTypeModel, library, log=log)

    # Existing Card file doesn't exist anymore, remove from db and recreate
    if not existing_card.exists:
        log.debug(f'{episode} Card not found - creating')
        db.delete(existing_card)
        db.commit()
        return create_card(db, card, CardClass, CardTypeModel, library, log=log)

    # Function to get the existing val
    def _get_existing(attribute: str) -> Any:
        return existing_card.model_json.get(
            attribute,
            CardTypeModel.__fields__[attribute].default,
        )

    # Determine if this Card is different than existing Card
    new_model_json = _card_type_model_to_json(CardTypeModel)
    different = False
    if card.card_type != existing_card.card_type:
        log.trace(
            f'{episode}.card_type = {existing_card.card_type} -> {card.card_type}'
        )
        different = True
    elif card.source_file != existing_card.source_file:
        log.trace((
            f'{episode}.source_file = {existing_card.source_file} -> '
            f'{card.source_file}'
        ))
        different = True
    else:
        for attr in existing_card.model_json:
            if attr not in new_model_json:
                log.trace(f'{episode}.{attr} reverting to default')
                different = True
                break
        if not different:
            for attr, new_val in new_model_json.items():
                if (not attr.endswith('_rotation_angle')
                    and str(new_val) != str(_get_existing(attr))):
                    log.trace((
                        f'{episode}.{attr} = {_get_existing(attr)!r} -> '
                        f'{new_val!r}'
                    ))
                    different = True
                    break

    # Not different, nothing else to do
    if not different:
        return None

    # If different, delete existing file, remove from database, create Card
    log.debug(f'{episode} Card config changed - recreating')
    Path(existing_card.card_file).unlink(missing_ok=True)
    db.delete(existing_card)
    db.commit()

    return create_card(db, card, CardClass, CardTypeModel, library, log=log)


def create_episode_cards(
        db: Session,
        episode: Episode,
        *,
        raise_exc: bool = True,
        log: Logger = log,
    ) -> bool:
    """
    Create all the Title Card for the given Episode.

    Args:
        db: Database to query and update.
        episode: Episode whose Cards are being created.
        raise_exc: Whether to raise any HTTPExceptions.
        log: Logger for all log messages.

    Returns:
        True if any new Cards were created, False otherwise.

    Raises:
        HTTPException: The card settings are invalid and `raise_exc` is
            True.
    """

    # If parent Series has multiple libraries
    if episode.series.libraries:
        # In library unique mode, create Card for each library
        if settings.library_unique_cards:
            changed = False
            for library in episode.series.libraries:
                changed |= create_episode_card(
                    db, episode, library, raise_exc=raise_exc, log=log
                ) is not None
            return changed

        # Only create Card for primary library
        return create_episode_card(
            db, episode, episode.series.libraries[0],
            raise_exc=raise_exc, log=log,
        )

    result = create_episode_card(
        db, episode, None, raise_exc=raise_exc, log=log
    )

    # Invalidate caches since we created new cards
    if result:
        invalidate_card_cache(result)

    return result


def get_watched_statuses(
        db: Session,
        series: Series,
        episodes: list[Episode],
        *,
        log: Logger = log,
    ) -> None:
    """
    Update the watch statuses of the given Episodes for the given
    Series. This queries all libraries of this Series.

    Args:
        series: Series whose Episodes are being updated.
        episodes: List of Episodes to update the statuses of.
        log: Logger for all log messages.
    """

    # Get statuses for each library of this Series
    changed = False
    for library in series.libraries:
        interface = get_media_interface(library['interface_id'],raise_exc=False)
        if interface:
            changed |= interface.update_watched_statuses(
                library['name'], series.as_series_info, episodes, log=log,
            )

    if changed:
        db.commit()


def delete_cards(
        db: Session,
        card_query: Query,
        loaded_query: Query | None = None,
        *,
        commit: bool = True,
        log: Logger = log,
    ) -> list[str]:
    """
    Delete all Title Card files for the given card Query. Also remove
    the two queries from the Database.

    Args:
        db: Database to commit the query deletion to.
        card_query: SQL query for Cards whose card files to delete.
            Query contents itself are also deleted.
        loaded_query: SQL query for loaded assets to delete.
        commit: Whether to commit the deletion to the database.
        log: Logger for all log messages.

    Returns:
        List of file names of the deleted cards.
    """

    # Delete all associated Card files
    deleted = []
    for card in card_query.all():
        if (card_file := Path(card.card_file)).exists():
            card_file.unlink()
            log.debug(f'Deleted "{card_file.resolve()}" Title Card')
            deleted.append(str(card_file))
            invalidate_card_cache(card)

    # Delete from database
    if card_query:
        card_query.delete()
    if loaded_query:
        loaded_query.delete()
    if commit:
        db.commit()

    return deleted


@cache_result(ttl=Hours(12), key_prefix='series')
def get_series_cards(db: Session, series_id: int) -> list[Card]:
    """
    # TODO: Document function.
    """

    return (
        db.query(Card)
            .filter_by(series_id=series_id)
            .join(Episode)
            .order_by(
                Episode.season_number,
                Episode.episode_number,
                Episode.absolute_number,
            )
            .all()
    )


@cache_result(ttl=Hours(12), key_prefix='series')
def get_series_reduced_cards_with_cache(
        db: Session,
        series_id: int,
    ) -> list[TitleCardReduced]:
    """
    # TODO: Document function.
    """

    # Get from database with reduced fields
    cards = (
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
            .all()
    )

    # Convert to reduced format
    return [
        TitleCardReduced.model_validate(card)
        for card in cards
    ]
