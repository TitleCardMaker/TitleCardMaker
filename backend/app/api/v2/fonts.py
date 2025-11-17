from string import printable, punctuation, whitespace
from typing import Literal

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Query,
    UploadFile
)
from sqlalchemy.orm import Session
from unidecode import unidecode

from app.core.font import delete_font_files, get_missing_characters
from app.db.query import get_font
from app.dependencies import get_database, get_logger
from app.db.users import get_current_user
from app.logging.logger import Logger
from app.models.episode import Episode
from app.models.font import Font
from app.schemas.font import (
    FontAnalysis,
    NamedFont,
    NewNamedFont,
    UpdateNamedFont
)
from app.settings import settings


"""Common character replacements to try when querying replacements"""
COMMON_REPLACEMENTS = {
    '`': "'",
    '’': "'",
    '&': 'and',
    '–': '-',
    '…': '...',
    'ø': 'o',
    'Ø': 'O',
}


# Create sub router for all /fonts API requests
font_router = APIRouter(
    prefix='/fonts',
    tags=['Fonts'],
    dependencies=[Depends(get_current_user)],
)


@font_router.get('/all')
def get_all_fonts(
        order: Literal['id', 'name'] = 'name',
        db: Session = Depends(get_database),
    ) -> list[NamedFont]:
    """Get all defined Fonts."""

    return [
        NamedFont.model_validate(font)
        for font in db.query(Font)
            .order_by(Font.id if order == 'id' else Font.sort_name)
            .all()
    ]


@font_router.post('/font/new')
def create_font(
        new_font: NewNamedFont = Body(...),
        db: Session = Depends(get_database),
    ) -> NamedFont:
    """
    Create a new Font.

    - new_font: Font definition to create.
    """

    # Add to database
    font = Font(**new_font.model_dump())
    db.add(font)
    db.commit()

    return font


@font_router.put('/font/{font_id}/file')
async def add_font_file(
        font_id: int,
        file: UploadFile,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> NamedFont:
    """
    Add a custom font file to the specified Font.

    - font_id: ID of the font to upload the font file to.
    - file: Font file to attach to the specified font.
    """

    # Download file, raise 400 if contentless
    if not (file_content := await file.read()):
        raise HTTPException(
            status_code=400,
            detail='Font file is invalid',
        )

    # Get existing font object, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Delete existing file (if present)
    if (existing_font := font.file):
        try:
            existing_font.unlink(missing_ok=True)
        except OSError as exc:
            log.exception('Unable to delete Font file')
            raise HTTPException(
                status_code=400,
                detail=f'Error deleting Font file - {exc}',
            )

    # Write to file
    font_directory = settings.asset_directory / 'fonts'
    file_path = font_directory / str(font.id) / file.filename # type: ignore
    file_path.parent.mkdir(exist_ok=True, parents=True)
    file_path.write_bytes(file_content)

    # Update object and database
    font.file_name = file_path.name
    db.commit()

    return font


@font_router.delete('/font/{font_id}/file')
def delete_font_file(
        font_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> NamedFont:
    """
    Delete the font file associated with the given Font.

    - font_id: ID of the Font to delete the file of.
    """

    # Get existing font object, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Font has no file, raise 404
    if font.file is None:
        raise HTTPException(
            status_code=404,
            detail=f'Font {font.name} has no file',
        )

    # Delete files, update font name reference
    delete_font_files(font, log=log)
    font.file_name = None
    db.commit()

    return font


@font_router.patch('/font/{font_id}')
def update_font(
        font_id: int,
        update_font: UpdateNamedFont = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> NamedFont:
    """
    Update the Font with the given ID. Only provided fields are updated.

    - font_id: ID of the Font to update.
    - update_font: UpdateFont containing fields to update.
    """

    # Get existing font object, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Update other attributes
    changed = False
    for attribute, value in update_font.model_dump(exclude_unset=True).items():
        if getattr(font, attribute) != value:
            setattr(font, attribute, value)
            changed = True
            log.debug(f'Font[{font_id}].{attribute} = {value}')

    # If object was changed, update DB
    if changed:
        db.commit()

    return font


@font_router.get('/font/{font_id}')
def get_font_by_id(
        font_id: int,
        db: Session = Depends(get_database),
    ) -> NamedFont:
    """
    Get the Font with the given ID.

    - font_id: ID of the Font to retrieve.
    """

    return get_font(db, font_id, raise_exc=True)


@font_router.delete('/font/{font_id}', status_code=204)
def delete_font(
        font_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> None:
    """
    Delete the Font with the given ID. This also deletes the font's
    font file if it exists.

    - font_id: ID of the Font to delete.
    """

    # Get specified Font, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Delete from global setting if indicated
    if font_id in settings.default_fonts.values():
        settings.default_fonts = {
            card_type: id_
            for card_type, id_ in settings.default_fonts.items()
            if id_ != font_id
        }
        log.debug(f'{settings.default_fonts = }')

    # Delete all files and the Font itself
    delete_font_files(font, log=log)
    db.delete(font)
    db.commit()
    settings.commit(log=log)


@font_router.get('/font/{font_id}/analysis')
def get_suggested_font_replacements(
        font_id: int,
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> FontAnalysis:
    """
    Analyze the Font file associated with the Font with the given ID and
    determine a suggested set of character replacements, along with a
    list of which characters have no suitable replacements. This looks
    at the leters of all associated Episodes that use this Font (through
    Series, Templates, etc.), as well as the standard alphanumberic
    set of English characters and punctuation.

    - font_id: ID of the Font to analyze. If this Font does not have a
    custom Font file, then no analysis is performed.
    """

    # Get Font with this ID, raise 404 if DNE
    font = get_font(db, font_id, raise_exc=True)

    # Font has no custom file, make no suggestions
    if font.file_name is None or font.file is None:
        log.debug(f'{font} has no custom File - no replacements to suggest')
        return FontAnalysis()

    # Get ANY titles associated with this Font; if the Font is being
    # globally specified, query all Episode titles and translations
    if font_id in settings.default_fonts.values():
        titles: set[str] = (
            set(val[0] for val in db.query(Episode.title).all())
            | set(
                translation
                for val in db.query(Episode.translations).all()
                for key, translation in val[0].items()
                if key == 'preferred_title'
            )
        )
    # Font is not globally specified, query only associated objects
    else:
        titles = (
            # Episode titles using this Font
            set(episode.title for episode in font.episodes)
            | set(
                # Translated titles using this Font
                translation
                for episode in font.episodes
                for key, translation in episode.translations.items()
                if key == 'preferred_title'
            ) | set(
                # Episode titles of Series using this Font
                episode.title
                for series in font.series
                for episode in series.episodes
            ) | set(
                # Translated titles of Series using this Font
                translation
                for series in font.series
                for episode in series.episodes
                for key, translation in episode.translations.items()
                if key == 'preferred_title'
            ) | set(
                # Episode titles using Templates using this Font
                episode.title
                for template in font.templates
                for episode in template.episodes
            ) | set(
                # Translated titles of Templates using this Font
                translation
                for template in font.templates
                for episode in template.episodes
                for key, translation in episode.translations.items()
                if key == 'preferred_title'
            ) | set(
                # Episode titles whose Series are using Templates using
                # this Font
                episode.title
                for template in font.templates
                for series in template.series
                for episode in series.episodes
            ) | set(
                # Translated titles of Episodes of Series using
                # Templates using this Font
                translation
                for template in font.templates
                for series in template.series
                for episode in series.episodes
                for key, translation in episode.translations.items()
                if key == 'preferred_title'
            )
        )

    # Get all (non-whitespace) letters in these titles, add base printables
    title_letters = set(''.join(titles).lower()) | set(''.join(titles).upper())
    letters = (title_letters | set(printable)) - set(whitespace)

    # Query FontValidator for this Font
    if (missing := get_missing_characters(font.file, letters)):
        log.debug(f'Identified missing characters: {" ".join(missing)}')

    # Attempt to find replacements for all missing characters
    bad, replacements = [], {}
    for char in missing:
        # Remove any unicode non-spacing combining marks - e.g. é -> ´e -> e
        replacement = unidecode(char, errors='preserve')

        # See if there is a common replacement for this
        if (replacement in missing
            and char in COMMON_REPLACEMENTS
            and all(c not in missing for c in COMMON_REPLACEMENTS[char])):
            replacement = COMMON_REPLACEMENTS[char]

        # If this replacement is missing, try the other case-equivalent
        if replacement in missing and replacement.lower() not in missing:
            replacement = replacement.lower()
        if replacement in missing and replacement.upper() not in missing:
            replacement = replacement.upper()

        # If replacement is still missing, suggest deletion if character is
        # punctuation
        if replacement in missing and char in punctuation:
            replacement = ''

        # If the replacement is defined, add to replacements set
        if replacement not in missing:
            replacements[char] = replacement
        else:
            bad.append(char)

    # Replace \ with post:\ so that manually entered newline characters
    # are not ignored
    if '\\' in replacements:
        replacements['\\'] = 'post:\\'

    return FontAnalysis(
        replacements=replacements,
        missing=bad,
    )


@font_router.put('/transfer')
def transfer_font_references(
        to_id: int = Query(..., alias='to'),
        from_id: int = Query(..., alias='from'),
        delete_from: bool = Query(default=False),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> NamedFont:
    """
    Transfer all references for the given `from` Font to the given `to`
    Font.

    - to: ID of the Font to transfer _to_.
    - from: ID of the Font to transfer _from_.
    - delete_from: Whether to delete the _from_ Font after the
    references are reassigned.
    """

    # Get specified Fonts, raise 404 if DNE
    to_font = get_font(db, to_id, raise_exc=True)
    from_font = get_font(db, from_id, raise_exc=True)

    # Perform reference transfer
    # Reassign global Fonts
    for card_type, id_ in settings.default_fonts.items():
        if id_ == from_id:
            log.debug(
                f'Settings.default_fonts[{card_type}] = {from_id} -> {to_id}'
            )
            settings.default_fonts[card_type] = to_id
    # Reassign Template Fonts
    for template in from_font.templates:
        log.debug(f'Template[{template.id}].font_id = {from_id} -> {to_id}')
        template.font_id = to_id
    # Reassign Series Fonts
    for series in from_font.series:
        log.debug(f'Series[{series.id}].font_id = {from_id} -> {to_id}')
        series.font_id = to_id
    # Reassign Episode Fonts
    for episode in from_font.episodes:
        log.debug(f'Episode[{episode.id}].font_id = {from_id} -> {to_id}')
        episode.font_id = to_id

    # Delete transferred Font, if indicated
    if delete_from:
        delete_font_files(from_font, log=log)
        db.delete(from_font)
        log.debug(f'Deleting Font[{from_id}]')

    db.commit()

    return to_font
