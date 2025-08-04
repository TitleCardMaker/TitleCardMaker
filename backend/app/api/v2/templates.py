from typing import Literal

from fastapi import APIRouter, Body, Depends
from fastapi_pagination import paginate
from sqlalchemy.orm import Session

from app.db.query import get_connection, get_font, get_template
from app.db.pagination import Page
from app.dependencies import get_database, get_logger, get_preferences
from app.db.users import get_current_user
from app.core.cards import refresh_remote_card_types
from modules.preferences import Preferences
from app.models.template import Template as TemplateModel
from app.schemas.base import UNSPECIFIED
from app.schemas.series import NewTemplate, Template, UpdateTemplate
from app.logging.logger import Logger


# Create sub router for all /templates API requests
template_router = APIRouter(
    prefix='/templates',
    tags=['Templates'],
    dependencies=[Depends(get_current_user)],
)


@template_router.get('/all')
def get_all_templates(
        order: Literal['id', 'name'] = 'name',
        db: Session = Depends(get_database),
    ) -> list[Template]:
    """
    Get all defined Templates.

    - order: How to order the returned Templates.
    """

    order_by = {
        'id': TemplateModel.id,
        'name': TemplateModel.sort_name,
    }[order]

    return db.query(TemplateModel).order_by(order_by).all()


@template_router.post('/template/new')
def create_template(
        new_template: NewTemplate = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> Template:
    """
    Create a new Template. Any referenced font_id must exist.

    - new_template: Template definition to create.
    """

    # Validate Font ID if provided
    get_font(db, new_template.font_id, raise_exc=True)

    template = TemplateModel(**new_template.dict())
    db.add(template)
    db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    return template


@template_router.get('/template/{template_id}')
def get_template_by_id(
        template_id: int,
        db: Session = Depends(get_database),
    ) -> Template:
    """
    Get the Template with the given ID.

    - template_id: ID of the Template.
    """

    return get_template(db, template_id, raise_exc=True)


@template_router.patch('/template/{template_id}')
def update_template_(
        template_id: int,
        update_template: UpdateTemplate = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
    ) -> Template:
    """
    Update the Template with the given ID. Only provided fields are
    updated.

    - template_id: ID of the Template to update.
    - update_template: UpdateTemplate containing fields to update.
    """

    # Query for Template, raise 404 if DNE
    template = get_template(db, template_id, raise_exc=True)

    # If a Font ID was specified, verify it exists
    get_font(db, getattr(update_template, 'font_id', None), raise_exc=True)

    # Verify Image Source Priority if it was provided
    if (isp := getattr(update_template, 'image_source_priority', None)):
        [get_connection(db, id_, raise_exc=True) for id_ in isp]

    # Update each attribute of the object
    changed = False
    for attr, value in update_template.model_dump(exclude_defaults=True).items():
        if value != UNSPECIFIED and getattr(template, attr) != value:
            setattr(template, attr, value)
            log.debug(f'Template[{template_id}].{attr} = {value}')
            changed = True

    # If any values were changed, commit to database
    if changed:
        db.commit()

    # Refresh card types in case new remote type was specified
    refresh_remote_card_types(db, log=log)

    return template


@template_router.delete('/template/{template_id}')
def delete_template(
        template_id: int,
        db: Session = Depends(get_database),
        preferences: Preferences = Depends(get_preferences),
    ) -> None:
    """
    Delete the specified Template.

    - template_id: ID of the Template to delete.
    """

    # Query for Template, raise 404 if DNE
    get_template(db, template_id, raise_exc=True)

    # Delete from global template list, if present
    if template_id in preferences.default_templates:
        preferences.default_templates = [
            tid for tid in preferences.default_templates if tid != template_id
        ]
        preferences.commit()

    # Delete Template from database
    db.delete(get_template(db, template_id, raise_exc=True))
    db.commit()
