from shutil import copyfile
from typing import Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import ValidationError
from sqlalchemy.orm import Session
from yaml import safe_load
from yaml.parser import ParserError

from app.core.imports import (
    import_card_content,
    import_cards,
    import_mediux_yaml,
    parse_emby,
    parse_fonts,
    parse_jellyfin,
    parse_plex,
    parse_preferences,
    parse_raw_yaml,
    parse_series,
    parse_sonarr,
    parse_syncs,
    parse_templates,
    parse_tmdb,
)
from app.core.series import download_series_poster, set_series_database_ids
from app.core.sources import download_series_logo
from app.db.query import get_all_templates, get_series
from app.dependencies import get_database, get_logger
from app.db.users import get_current_user
from app.logging.logger import Logger
from app.models.font import Font as FontModel
from app.models.series import Series as SeriesModel
from app.models.sync import Sync as SyncModel
from app.models.template import Template as TemplateModel
from app.schemas.font import NamedFont
from app.schemas.imports import (
    ImportCardDirectory,
    ImportYaml,
    KometaYaml,
    MultiCardImport,
)
from app.schemas.preferences import Preferences
from app.schemas.series import Series, Template
from app.schemas.sync import Sync
from app.settings import settings


import_router = APIRouter(
    prefix='/import',
    tags=['Import'],
    dependencies=[Depends(get_current_user)],
)


@import_router.post('/yaml/preferences/options')
def import_global_options_yaml(
        import_yaml: ImportYaml = Body(...),
        log: Logger = Depends(get_logger),
    ) -> Preferences:
    """
    Import the global options from the preferences defined in the given
    YAML. This imports the options and imagemagick sections.

    - import_yaml: The YAML string to parse.
    """

    # Parse raw YAML into dictionary
    if not (yaml_dict := parse_raw_yaml(import_yaml.yaml)):
        return settings # type: ignore

    # Modify the preferences  from the YAML dictionary
    try:
        return parse_preferences(settings, yaml_dict, log=log) # type: ignore
    except ValidationError as exc:
        log.exception('Invalid YAML')
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {exc}'
        ) from exc


@import_router.post('/yaml/preferences/connection/{connection}')
def import_connection_yaml(
        connection: Literal['all', 'emby', 'jellyfin', 'plex', 'sonarr', 'tmdb'],
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Import the connection preferences defined in the given YAML. This
    does NOT import any Sync settings.

    - connection: Which connection is being modified.
    - import_yaml: The YAML string to parse.
    """

    # Parse raw YAML into dictionary
    if not (yaml_dict := parse_raw_yaml(import_yaml.yaml)):
        return None

    try:
        if connection in ('all', 'emby'):
            parse_emby(db, yaml_dict, log=log)
        if connection in ('all', 'jellyfin'):
            parse_jellyfin(db, yaml_dict, log=log)
        if connection in ('all', 'plex'):
            parse_plex(db, yaml_dict, log=log)
        if connection in ('all', 'sonarr'):
            parse_sonarr(db, yaml_dict, log=log)
        if connection in ('all', 'tmdb'):
            parse_tmdb(db, yaml_dict, log=log)
    except ValidationError as exc:
        log.exception('Invalid YAML')
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {exc}'
        ) from exc


@import_router.post('/yaml/preferences/sync')
def import_sync_yaml(
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> list[Sync]:
    """
    Import all Syncs defined in the given YAML.

    - import_yaml: The YAML string to parse.
    """

    # Parse raw YAML into dictionary
    if not (yaml_dict := parse_raw_yaml(import_yaml.yaml)):
        return []

    # Create New*Sync objects from the YAML dictionary
    try:
        new_syncs = parse_syncs(db, yaml_dict)
    except ValidationError as exc:
        log.exception('Invalid YAML')
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {exc}'
        ) from exc

    # Add each defined Sync to the database
    all_syncs = []
    for new_sync in new_syncs:
        new_sync_dict = new_sync.dict()
        templates = get_all_templates(db, new_sync_dict)
        sync = SyncModel(**new_sync_dict)
        db.add(sync)
        db.commit()
        log.info(f'{sync} imported to Database')
        all_syncs.append(sync)

        # Assign Templates
        sync.assign_templates(templates, log=log)
        db.commit()

    return all_syncs


@import_router.post('/yaml/fonts')
def import_fonts_yaml(
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> list[NamedFont]:
    """
    Import all Fonts defined in the given YAML. This does NOT import any
    custom font files - these will need to be added separately.

    - import_yaml: The YAML string to parse.
    import.
    """

    # Parse raw YAML into dictionary
    if not (yaml_dict := parse_raw_yaml(import_yaml.yaml)):
        return []

    # Create NewNamedFont objects from the YAML dictionary
    try:
        new_fonts = parse_fonts(yaml_dict)
    except ValidationError as exc:
        log.exception('Invalid YAML')
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {exc}'
        ) from exc

    # Add each defined Font to the database
    all_fonts = []
    for new_font, font_file in new_fonts:
        font = FontModel(**new_font.dict())
        db.add(font)
        db.commit()
        log.info(f'{font} imported to Database')
        all_fonts.append(font)

        # If there is a Font file, copy into asset directory
        if font_file is not None:
            if font_file.exists():
                font_directory = settings.asset_directory / 'fonts'
                file_path = font_directory / str(font.id) / font_file.name
                copyfile(font_file, file_path)

                # Update object and database
                font.file_name = file_path.name
                db.commit()
            else:
                log.error(f'Font File "{font_file.resolve()}" does not exist')

    return all_fonts


@import_router.post('/yaml/templates')
def import_template_yaml(
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> list[Template]:
    """
    Import all Templates defined in the given YAML.

    - import_yaml: The YAML string to parse.
    """

    # Parse raw YAML into dictionary
    if not (yaml_dict := parse_raw_yaml(import_yaml.yaml)):
        return []

    # Create NewTemplate objects from the YAML dictionary
    try:
        new_templates = parse_templates(db, settings, yaml_dict)
    except ValidationError as exc:
        log.exception('Invalid YAML')
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {exc}'
        ) from exc

    # Add each defined Template to the database
    all_templates = []
    for new_template in new_templates:
        template = TemplateModel(**new_template.dict())
        db.add(template)
        log.info(f'{template} imported to Database')
        all_templates.append(template)
    db.commit()

    return all_templates


@import_router.post('/yaml/series')
def import_series_yaml(
        background_tasks: BackgroundTasks,
        import_yaml: ImportYaml = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> list[Series]:
    """
    Import all Series defined in the given YAML.

    - import_yaml: The YAML string and default library name to parse.
    """

    # Parse raw YAML into dictionary
    if not (yaml_dict := parse_raw_yaml(import_yaml.yaml)):
        return []

    # Create NewSeries objects from the YAML dictionary
    try:
        new_series = parse_series(db, settings, yaml_dict, log=log)
    except ValidationError as exc:
        log.exception('Invalid YAML')
        raise HTTPException(
            status_code=422,
            detail=f'YAML is invalid - {exc}'
        ) from exc

    # Add each defined Series to the database
    all_series = []
    for series in new_series:
        # Add to batabase
        new_series_dict = series.model_dump()
        templates = get_all_templates(db, new_series_dict)
        series = SeriesModel(**new_series_dict)
        db.add(series)
        db.commit()
        log.info(f'{series} imported to Database')

        # Assign Templates
        series.assign_templates(templates, log=log)
        db.commit()

        # Add background tasks for setting ID's, downloading poster and logo
        background_tasks.add_task(
            set_series_database_ids,
            series, db, log=log,
        )
        background_tasks.add_task(
            download_series_poster,
            db, series, log=log,
        )
        background_tasks.add_task(
            download_series_logo,
            series, log=log,
        )
        all_series.append(series)
    db.commit()

    return all_series


@import_router.post(
    '/series/{series_id}/cards/files',
    tags=['Title Cards', 'Series']
)
async def import_card_files_for_series(
        series_id: int,
        cards: list[UploadFile] = [],
        force_reload: bool = Query(default=True),
        textless: bool = Query(default=True),
        library_name: str | None = Query(default=None),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Import any existing Title Cards for the given Series. This finds
    card files by filename, and makes the assumption that each file
    exactly matches the Episode's currently specified config.

    - series_id: ID of the Series whose cards are being imported.
    - cards: List of uploaded Card files to import.
    """

    # Get this Series, raise 404 if DNE
    series = get_series(db, series_id, raise_exc=True)

    # Download all files
    card_files = [
        (card.filename, await card.read())
        for card in cards
        if card.filename
    ]

    import_card_content(
        db,
        series,
        card_files,
        None if library_name is None else series.get_library(library_name),
        force_reload=force_reload,
        as_textless=textless,
        log=log,
    )


@import_router.post('/series/{series_id}/cards/mediux')
async def import_mediux_yaml_for_series(
        series_id: int,
        yaml_str: str = Body(..., alias='yaml'),
        import_poster: bool = Query(default=False),
        import_backdrop: bool = Query(default=False),
        import_season_posters: bool = Query(default=True),
        force_reload: bool = Query(default=True),
        textless: bool = Query(default=True),
        library_names: list[str] = Query(default=[]),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Import Cards, posters, and backgrounds from the given Kometa YAML
    for the given Series.

    - series_id: ID of the Series to import into.
    - yaml_str: Raw YAML to import.
    - import_poster: Whether to parse and import posters.
    - import_backdrop: Whether to parse and import backdrops.
    - import_season_posters: Whether to parse and import season posters.
    - force_reload: Whether to replace any existing Cards.
    - textless: Whether to change any affected Episode's card type to
    Textless.
    - library_names: Names of the libraries to import the Cards into. If
    provided, then these assets are loaded into the associated
    server(s).
    """

    # Validate provided string as YAML
    try:
        full_yaml = KometaYaml(yaml=safe_load(yaml_str))
    except (ParserError, ValidationError) as exc:
        log.exception('Kometa YAML is invalid')
        raise HTTPException(
            status_code=422,
            detail='YAML is invalid',
        ) from exc

    await import_mediux_yaml(
        db,
        full_yaml,
        get_series(db, series_id, raise_exc=True),
        library_names=library_names,
        import_poster=import_poster,
        import_backdrop=import_backdrop,
        import_season_posters=import_season_posters,
        force_reload=force_reload,
        textless=textless,
        log=log,
    )


@import_router.post(
    '/series/{series_id}/cards/directory',
    tags=['Title Cards', 'Series']
)
def import_card_directory_for_series(
        series_id: int,
        card_directory: ImportCardDirectory = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Import any existing Title Cards for the given Series. This finds
    card files by filename, and makes the assumption that each file
    exactly matches the Episode's currently specified config.

    - series_id: ID of the Series whose cards are being imported.
    - card_directory: Directory details to parse for cards to import.
    """

    import_cards(
        db,
        get_series(db, series_id, raise_exc=True),
        card_directory.directory,
        card_directory.image_extension,
        card_directory.force_reload,
        log=log,
    )


@import_router.post('/series/cards', tags=['Title Cards', 'Series'])
def import_cards_for_multiple_series(
        card_import: MultiCardImport = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Import any existing Title Cards for all the given Series. This finds
    card files by filename, and makes the assumption that each file
    exactly matches the Episode's currently specified config.

    - card_import: Import details to parse for all Cards to import.
    """

    # Import Card for each identified Series
    for series_id in card_import.series_ids:
        import_cards(
            db,
            get_series(db, series_id, raise_exc=True),
            None,
            card_import.image_extension,
            card_import.force_reload,
            log=log,
        )


@import_router.post('/mediux')
async def import_mediux_yaml_(
        yaml_str: str = Body(..., alias='yaml'),
        import_poster: bool = Query(default=False),
        import_backdrop: bool = Query(default=False),
        import_season_posters: bool = Query(default=True),
        force_reload: bool = Query(default=True),
        textless: bool = Query(default=True),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Import Cards, posters, and backgrounds from the given Kometa YAML.
    Note that this will import into all libraries.

    - yaml_str: Raw YAML to import.
    - import_poster: Whether to parse and import posters.
    - import_backdrop: Whether to parse and import backdrops.
    - import_season_posters: Whether to parse and import season posters.
    - force_reload: Whether to replace any existing Cards.
    - textless: Whether to change any affected Episode's card type to
    Textless.
    """

    # Validate provided string as YAML
    try:
        full_yaml = KometaYaml(yaml=safe_load(yaml_str))
    except (ParserError, ValidationError) as exc:
        log.exception('Kometa YAML is invalid')
        raise HTTPException(
            status_code=422,
            detail='YAML is invalid',
        ) from exc

    # Find associated Series, raise 404 if DNE
    tvdb_id = list(full_yaml.yaml.keys())[0]
    if (series := db.query(SeriesModel).filter_by(tvdb_id=tvdb_id).first()) is None:
        raise HTTPException(
            status_code=404,
            detail='Associated Series not found',
        )

    await import_mediux_yaml(
        db,
        full_yaml,
        series,
        library_names='all',
        import_poster=import_poster,
        import_backdrop=import_backdrop,
        import_season_posters=import_season_posters,
        force_reload=force_reload,
        textless=textless,
        log=log,
    )
