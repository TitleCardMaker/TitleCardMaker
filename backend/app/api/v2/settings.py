from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.db.query import get_font, get_template
from app.dependencies import get_database, get_logger, get_preferences
from app.db.users import get_current_user
from app.core.backup import list_available_backups
from app.core.cards import refresh_remote_card_types
from app.core.settings import (
    apply_card_type_blur_profiles,
    get_episode_data_sources
)
from app.models.connection import Connection
from modules.preferences import Preferences as PreferencesModel
from app.schemas.base import UNSPECIFIED
from app.schemas.preferences import (
    EpisodeDataSourceToggle,
    ImageSourceToggle,
    Preferences,
    SystemBackup,
    UpdatePreferences,
)
from modules.Debug import Logger


# Create sub router for all /settings API requests
settings_router = APIRouter(
    prefix='/settings',
    tags=['Settings'],
    dependencies=[Depends(get_current_user)],
)


@settings_router.get('/settings')
def get_global_settings(
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> Preferences:
    """Get the global settings"""

    return preferences # type: ignore


@settings_router.get('/version')
def get_current_version(
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> str:
    """Get the version of TitleCardMaker that is currently running."""

    return str(preferences.current_version)


@settings_router.patch('/update')
def update_global_settings(
        update_preferences: UpdatePreferences = Body(...),
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> Preferences:
    """
    Update all global settings.

    - update_preferences: UpdatePreferences containing fields to update.
    """

    # Verify any specified Fonts/Templates exist
    if 'default_fonts' in update_preferences.model_fields_set:
        for font_id in update_preferences.default_fonts.values():
            get_font(db, font_id, raise_exc=True)
    if 'default_templates' in update_preferences.model_fields_set:
        for template_id in update_preferences.default_templates:
            get_template(db, template_id, raise_exc=True)

    preferences.update_values(
        **update_preferences.model_dump(exclude_unset=True),
        log=log
    )
    refresh_remote_card_types(db, log=log)
    preferences.determine_imagemagick_prefix(log=log)

    # Update card type object blur profiles
    apply_card_type_blur_profiles()

    return preferences # type: ignore


@settings_router.get('/episode-data-source')
def get_global_episode_data_source(
        db: Session = Depends(get_database),
    ) -> list[EpisodeDataSourceToggle]:
    """Get the list of Episode data sources."""

    return get_episode_data_sources(db)


@settings_router.get('/image-source-priority')
def get_image_source_priority(
        db: Session = Depends(get_database),
        log: Logger = Depends(get_logger),
        preferences: PreferencesModel = Depends(get_preferences),
    ) -> list[ImageSourceToggle]:
    """Get the global image source priority."""

    # Add all selected Connections
    sources, source_ids = [], []
    for interface_id in preferences.image_source_priority:
        if (isp_connection := db.get(Connection, interface_id)) is None:
            log.warning(f'No Connection with ID {interface_id}')
            continue

        source_ids.append(interface_id)
        sources.append({
            'interface': isp_connection.interface_type,
            'interface_id': interface_id,
            'name': isp_connection.name,
            'selected': True,
        })

    # Add remaining non-Sonarr Connections
    connections = db.query(Connection)\
        .filter(Connection.interface_type != 'Sonarr')\
        .all()
    for connection in connections:
        if connection.id not in source_ids:
            sources.append({
                'interface': connection.interface_type,
                'interface_id': connection.id,
                'name': connection.name,
                'selected': False,
            })

    return sources


@settings_router.get('/backups', deprecated=True)
def get_available_system_backups(
        log: Logger = Depends(get_logger),
    ) -> list[SystemBackup]:
    """Get a list detailing all the available system backups."""

    return list_available_backups(log=log)


@settings_router.get('/background-tasks')
def get_pending_background_tasks() -> list[tuple[str, str | None]]:
    from modules.BackgroundTasks import task_queue

    return [
        (
            task[1].__name__,
            task[1].__doc__,
        )
        for task in task_queue
    ]
