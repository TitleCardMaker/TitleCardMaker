from asyncio import gather as async_gather
from pathlib import Path
from re import match, IGNORECASE
from shutil import copyfile, move as move_file
from typing import Any, Literal

from app.core.series import load_series_title_cards
from curl_cffi import CurlHttpVersion
from curl_cffi.requests import AsyncSession
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.cards import (
    add_card_to_database,
    resolve_card_settings,
    validate_card_type_model
)
from app.db.query import get_media_interface
from app.exceptions import InvalidCardSettings
from app.interfaces.web import WebInterface
from app.logging.logger import Logger, log
from app.models.card import Card as CardModel
from app.models.episode import Episode
from app.models.series import Library, Series
from app.schemas.card import NewTitleCard
from app.schemas.imports import KometaYaml
from app.schemas.preferences import CardExtension


type YamlDict = dict[str, Any]


def import_cards(
        db: Session,
        series: Series,
        directory: Path | None,
        image_extension: CardExtension,
        force_reload: bool,
        *,
        log: Logger = log,
    ) -> None:
    """
    Import any existing Title Cards for the given Series. This finds
    card files by filename, and makes the assumption that each file
    exactly matches the Episode's currently specified config.

    Args:
        db: Database to query for existing Cards.
        series: Series whose Cards are being imported.
        directory: Directory to search for Cards to import. If omitted,
            then the Series default card directory is used.
        image_extension: Extension of images to search for.
        force_reload: Whether to replace any existing Card entries for
            Episodes identified while importing.
        log: Logger for all log messages.
    """

    # If explicit directory was not provided, use Series default
    directory = directory or series.card_directory

    # Glob directory for images to import - return if no images to import
    if not (all_images := list(directory.glob(f'**/*{image_extension}'))):
        log.debug(f'No Cards identified within "{directory}" to import')
        return None

    # For each image, identify associated Episode
    for image in all_images:
        if (groups := match(r'.*s(\d+).*e(\d+)', image.name, IGNORECASE)):
            season_number, episode_number = map(int, groups.groups())
        else:
            log.warning(f'Cannot identify index of {image.resolve()} - skipping')
            continue

        # Find associated Episode
        episode = (
            db.query(Episode)
                .filter_by(
                    series_id=series.id,
                    season_number=season_number,
                    episode_number=episode_number
                )
                .first()
        )

        # No associated Episode, skip
        if episode is None:
            log.warning(
                f'{series} No associated Episode for {image.resolve()} - '
                f'skipping'
            )
            continue

        # Episode has an existing Card, skip if not forced
        if episode.cards and not force_reload:
            log.debug(f'{episode} has an associated Card - skipping')
            continue

        # Episode has card, delete if reloading
        if episode.cards and force_reload:
            for card in episode.cards:
                log.debug(f'{card} deleting record')
                db.query(CardModel).filter_by(id=card.id).delete()
                log.debug(f'{episode} has associated Card - reloading')

        # Get finalized Card settings for this Episode, override card file
        try:
            card_settings = resolve_card_settings(episode, log=log)
        except (HTTPException, InvalidCardSettings) as exc:
            log.exception(
                f'{episode} Cannot import Card - settings are invalid {exc}'
            )
            continue

        # Get a validated card class, and card type Pydantic model
        _, CardTypeModel = validate_card_type_model(card_settings, log=log)

        # Card is valid, create and add to Database
        card_settings['card_file'] = image
        title_card = NewTitleCard(
            **card_settings,
            series_id=series.id,
            episode_id=episode.id,
        )

        card = add_card_to_database(
            db, title_card, CardTypeModel, card_settings['card_file'], None,
            commit=False,
        )
        log.debug(f'{episode} Imported {image.resolve()}')

    db.commit()

    return None


def import_card_content(
        db: Session,
        series: Series,
        files: list[tuple[str, bytes]],
        library: Library | None = None,
        force_reload: bool = True,
        as_textless: bool = False,
        *,
        log: Logger = log,
    ) -> None:
    """
    Import the Title Card files to the given Series.

    Args:
        db: Database to query for existing Cards.
        series: Series whose Cards are being imported.
        files: List of tuples of the filename and image (bytes) being
            imported.
        force_reload: Whether to replace any existing Card entries for
            Episodes identified while importing.
        as_textless: Whether to set the imported Episode's card type to
            textless.
        log: Logger for all log messages.
    """

    # For each image, identify associated Episode
    for filename, file in files:
        if (groups := match(r'.*s(\d+).*e(\d+)', filename, IGNORECASE)):
            season_number, episode_number = map(int, groups.groups())
        else:
            log.warning(f'Cannot identify index of {filename} - skipping')
            continue

        # Find associated Episode
        episode = (
            db.query(Episode)
                .filter_by(
                    series_id=series.id,
                    season_number=season_number,
                    episode_number=episode_number
                )
                .first()
        )

        # No associated Episode, skip
        if episode is None:
            log.warning(
                f'{series} No associated Episode for {filename} - skipping'
            )
            continue

        # Episode has an existing Card, skip if not forced
        if episode.cards and not force_reload:
            log.debug(f'{episode} has an associated Card - skipping')
            continue

        # Episode has card, delete if reloading
        if episode.cards and force_reload:
            for card in episode.cards:
                if (not library
                    or (library and card.library_name == library['name'])):
                    log.debug(f'{card} deleting record')
                    db.query(CardModel).filter_by(id=card.id).delete()
                    log.debug(f'{episode} has associated Card - reloading')

        # If setting textless, change card type
        if as_textless:
            episode.card_type = 'textless'
            log.debug(f'{episode}.card_type = textless')
            source_file = episode.get_source_file('unique')
            source_file.write_bytes(file)
            log.debug(f'Wrote {len(file):,} bytes to {source_file}')

        # Get finalized Card settings for this Episode
        try:
            card_settings = resolve_card_settings(episode, library, log=log)
        except (HTTPException, InvalidCardSettings):
            log.exception(f'{episode} Cannot import Card - settings are invalid')
            continue

        # Get a validated card class, and card type Pydantic model
        try:
            _, CardTypeModel = validate_card_type_model(card_settings, log=log)
        except HTTPException:
            log.exception(f'{episode} Cannot import Card - settings are invalid')
            continue

        # Write card file to file
        card_settings['card_file'].parent.mkdir(exist_ok=True, parents=True)
        card_settings['card_file'].write_bytes(file)

        # Card is valid, create and add to Database
        title_card = NewTitleCard(
            **card_settings,
            series_id=series.id,
            episode_id=episode.id,
        )

        card = add_card_to_database(
            db,
            title_card,
            CardTypeModel,
            card_settings['card_file'],
            library,
            commit=False,
        )
        log.debug(f'{episode} Imported {filename}')

    db.commit()


def import_card_files(
        db: Session,
        series: Series,
        files: list[tuple[Episode, Path]],
        library: Library | None = None,
        force_reload: bool = True,
        *,
        log: Logger = log,
    ) -> None:
    """
    Import the Title Card files to the given Series.

    Args:
        db: Database to query for existing Cards.
        series: Series whose Cards are being imported.
        files: List of tuples of the Episode, and card files to import.
        force_reload: Whether to replace any existing Card entries for
            Episodes identified while importing.
        log: Logger for all log messages.
    """

    # For each image, identify associated Episode
    for episode, file in files:
        # Episode has an existing Card, skip if not forced
        if not force_reload and episode.cards:
            log.debug(f'{episode} has an associated Card - skipping')
            continue

        # Episode has Card, delete if reloading
        if force_reload and episode.cards:
            for card in episode.cards:
                if (not library
                    or (library and card.library_name == library['name'])):
                    log.debug(f'{card} deleting record')
                    db.query(CardModel).filter_by(id=card.id).delete()
                    log.debug(f'{episode} has associated Card - reloading')

        # Get finalized Card settings for this Episode, override card file
        try:
            card_settings = resolve_card_settings(episode, library, log=log)
        except (HTTPException, InvalidCardSettings) as exc:
            log.exception(
                f'{episode} Cannot import Card - settings are invalid {exc}'
            )
            continue

        # Get a validated card class, and card type Pydantic model
        _, CardTypeModel = validate_card_type_model(card_settings, log=log)

        # Rename existing Card to expected card location
        card_settings['card_file'].parent.mkdir(exist_ok=True, parents=True)
        try:
            move_file(file, card_settings['card_file'])
        except OSError: # Can be caused by cross-platform move on Linux/Docker
            log.exception('Error occurred while moving Card file - skipping')
            continue

        # Card is valid, create and add to Database
        title_card = NewTitleCard(
            **card_settings,
            series_id=series.id,
            episode_id=episode.id,
        )

        card = add_card_to_database(
            db,
            title_card,
            CardTypeModel,
            card_settings['card_file'],
            library,
            commit=False,
        )
        log.debug(f'{episode} imported "{file.resolve()}"')

    # Commit any changes to the Database
    db.commit()


async def download_image(
        session: AsyncSession,
        url: str,
        episode: Episode,
        temp_images: list[Path],
        *,
        log: Logger = log,
    ) -> tuple[Path, Episode] | None:
    """
    Asynchronously download the given URL with the given session.

    Args:
        session: Async session to download the URL with.
        url: URL of the image being downloaded.
        episode: Episode associated with the URL being downloaded.
        temp_images: List of temporary image files to be cleaned up.
            This is added to.
        log: Logger for all log messages.

    Returns:
        Tuple of the downloaded image path and the associated Episode.
        None if the download failed for any reason. `temp_images` is
        also appended to.
    """

    # Download URL
    log.trace(f'Downloading "{url}"..')
    response = await session.get(url)

    # Validate content (also done in WebInterface)
    if not response.ok:
        log.error(f'Failed to download "{url} ({response.status_code})')
        return None
    if 'image' not in (type_ := response.headers.get('Content-Type', '')):
        log.error(f'URL "{url}" returned content of type "{type_}"')
        return None

    filename = WebInterface.get_random_filename(
        WebInterface._TEMP_DIR / f'temp_{url[-5:]}', 'jpg'
    )
    temp_images.append(filename)
    if WebInterface.download_image(response.content, filename, log=log):
        return filename, episode

    return None


async def import_mediux_yaml(
        db: Session,
        full_yaml: KometaYaml,
        series: Series,
        *,
        library_names: list[str] | Literal['all'] = [],
        import_poster: bool = False,
        import_backdrop: bool = False,
        import_season_posters: bool = False,
        force_reload: bool = True,
        textless: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Import Cards, posters, and backgrounds from the given Kometa YAML
    for the given Series.

    Args:
        db: Database to query for existing Cards.
        full_yaml: The full Kometa YAML to import.
        series_id: ID of the Series to import into.
        library_names: Names of the libraries to import the Cards into. If
            provided, then these assets are loaded into the associated
            server(s).
        import_poster: Whether to parse and import posters.
        import_backdrop: Whether to parse and import backdrops.
        import_season_posters: Whether to parse and import season posters.
        force_reload: Whether to replace any existing Cards.
        textless: Whether to change any affected Episode's card type to
            Textless.
        log: Logger for all log messages.
    """

    # Get just the YAML after the TVDb ID
    if not full_yaml.yaml:
        return None
    yaml = list(full_yaml.yaml.values())[0]

    # Parse all indicated files
    background, poster = None, None
    if import_backdrop and yaml.url_background:
        background = str(yaml.url_background)
    if import_poster and yaml.url_poster:
        poster = str(yaml.url_poster)
    cards: list[tuple[Episode, Path]] = []
    season_posters: dict[int, str] = {}

    # Parse each season
    tasks = []
    temp_images: list[Path] = []
    async with AsyncSession(
        max_clients=5, timeout=15, http_version=CurlHttpVersion.V1_1
    ) as session:
        for season_number, season_yaml in yaml.seasons.items():
            # Parse season posters if a library was provided and specified
            if library_names and import_season_posters:
                season_posters[season_number] = str(season_yaml.url_poster)

            # Parse all episodes of this season
            for episode_number, episode_yaml in season_yaml.episodes.items():
                # Skip download if there is no matching Episode
                episode = (
                    db.query(Episode)
                        .filter_by(
                            series_id=series.id,
                            season_number=season_number,
                            episode_number=episode_number
                        )
                        .first()
                )
                if not episode:
                    log.debug((
                        f'No associated Episode for S{season_number:02}'
                        f'E{episode_number:02}'
                    ))
                    continue

                # Skip if not forcing and has Cards
                if not force_reload and episode.cards:
                    log.debug(f'Skipping {episode.index_str} - has Cards')
                    continue

                # Episode exists, download image
                tasks.append(
                    download_image(
                        session,
                        str(episode_yaml.url_poster),
                        episode,
                        temp_images,
                        log=log,
                    )
                )

        # Wait for all downloads to finish
        contents: list[tuple[Path, Episode]] = [
            _return for _return in await async_gather(*tasks)
            if _return is not None
        ]

        # Add Episode and files to list, copy to source image if textless
        for card_file, episode in contents:
            cards.append((episode, card_file))
            if textless:
                episode.card_type = 'textless'
                log.debug(f'{episode}.card_type = textless')
                if (source := episode.get_source_file('unique')).exists():
                    log.debug((
                        f'{episode} Source Image ({source.name}) exists - '
                        f'replacing'
                    ))
                try:
                    copyfile(card_file, source)
                except OSError:
                    log.exception('Error occurred while copying Card file')
                    continue

    # Commit any changes to the Episode card types
    if cards and textless:
        db.commit()

    # Import content into all specified libraries
    if library_names == 'all':
        library_names = [library['name'] for library in series.libraries]

    log.debug(f'Identified {len(cards)} Cards to import')
    for library_name in library_names:
        # If the library cannot be found, skip
        if (not (library := series.get_library(library_name)) or not
            (iface := get_media_interface(library['interface_id'], raise_exc=False))):
            log.warning(f'Cannot import to library "{library_name}"')
            continue

        if cards:
            import_card_files(
                db, series, cards, library, force_reload=force_reload, log=log,
            )

            # Load Cards into library
            load_series_title_cards(
                series,
                library['name'],
                library['interface_id'],
                db,
                iface,
                episodes=[episode for episode, _ in cards],
                log=log,
            )

        # Load series backgrounds/poster, or season posters
        if background:
            iface.load_series_background(
                library_name, series.as_series_info, background, log=log,                         
            )
        if poster:
            iface.load_series_poster(
                library_name, series.as_series_info, poster, log=log,
            )
        if season_posters:
            iface.load_season_posters(
                library_name, series.as_series_info, season_posters, # type: ignore
                log=log,
            )

    # No libraries specified import Cards without a library
    if not library_names:
        import_card_files(
            db, series, cards, library=None, force_reload=force_reload, log=log,
        )
        if season_posters or poster or background:
            log.warning('Cannot import non-Card images without a library')

    # Delete any downloaded images after they've been uploaded
    for image in temp_images:
        image.unlink(missing_ok=True)
        log.trace(f'Deleted temporary image ({image})')
