from fastapi import (
    APIRouter,
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
    import_mediux_yaml
)
from app.db.query import get_series
from app.dependencies import get_database, get_logger
from app.db.users import get_current_user
from app.logging.logger import Logger
from app.models.series import Series as SeriesModel
from app.schemas.imports import ImportCardDirectory, KometaYaml, MultiCardImport


import_router = APIRouter(
    prefix='/import',
    tags=['Import'],
    dependencies=[Depends(get_current_user)],
)


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
