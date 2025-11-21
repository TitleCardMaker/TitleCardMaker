from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.db.query import get_all_templates, get_sync
from app.db.users import get_current_user
from app.dependencies import get_database
from app.core.series import delete_series
from app.core.sync import add_sync, run_sync, CURRENTLY_RUNNING_SYNC
from app.logging.logger import log
from app.models.sync import Sync as SyncModel
from app.schemas.sync import (
    EmbySync,
    JellyfinSync,
    NewEmbySync,
    NewJellyfinSync,
    NewPlexSync,
    NewSonarrSync,
    PlexSync,
    SonarrSync,
    Sync,
    UpdateSync,
)
from app.schemas.series import Series


# Create sub router for all /sync API requests
sync_router = APIRouter(
    prefix='/sync',
    tags=['Sync'],
    dependencies=[Depends(get_current_user)],
)


@sync_router.post('/emby/new', tags=['Emby'])
def create_new_emby_sync(
        new_sync: NewEmbySync = Body(...),
        db: Session = Depends(get_database),
    ) -> EmbySync:
    """
    Create a new Sync that interfaces with Emby.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync)


@sync_router.post('/jellyfin/new', tags=['Jellyfin'])
def create_new_jellyfin_sync(
        new_sync: NewJellyfinSync = Body(...),
        db: Session = Depends(get_database),
    ) -> JellyfinSync:
    """
    Create a new Sync that interfaces with Jellyfin.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync)


@sync_router.post('/plex/new', tags=['Plex'])
def create_new_plex_sync(
        new_sync: NewPlexSync = Body(...),
        db: Session = Depends(get_database),
    ) -> PlexSync:
    """
    Create a new Sync that interfaces with Plex.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync)


@sync_router.post('/sonarr/new', tags=['Sonarr'])
def create_new_sonarr_sync(
        new_sync: NewSonarrSync = Body(...),
        db: Session = Depends(get_database),
    ) -> SonarrSync:
    """
    Create a new Sync that interfaces with Sonarr.

    - new_sync: Sync definition to create.
    """

    return add_sync(db, new_sync)


@sync_router.patch('/{sync_id}')
def edit_sync(
        sync_id: int,
        update_sync: UpdateSync = Body(...),
        db: Session = Depends(get_database),
    ) -> Sync:
    """
    Update the Sync with the given ID. Only provided fields are updated.

    - sync_id: ID of the Sync to update.
    - update_sync: UpdateSync containing fields to update.
    """

    # Get existing Sync, raise 404 if DNE
    sync = get_sync(db, sync_id, raise_exc=True)
    update_sync_dict = update_sync.dict(exclude_unset=True)

    # Verify any indicated Templates exist and update Sync
    changed = False
    if (template_ids := update_sync_dict.pop('template_ids', None)) is not None:
        if template_ids != sync.template_ids:
            templates = get_all_templates(db, template_ids)
            sync.assign_templates(templates)
            changed = True

    # Update Sync itself
    for attribute, value in update_sync_dict.items():
        if getattr(sync, attribute) != value:
            setattr(sync, attribute, value)
            log.debug(f'Sync[{sync.id}].{attribute} = {value}')
            changed = True

    # If Sync was changed, update database
    if changed:
        db.commit()

    return sync


@sync_router.delete('/delete/{sync_id}', status_code=204)
def delete_sync(
        sync_id: int,
        delete_series_: bool = Query(default=False, alias='delete_series'),
        db: Session = Depends(get_database),
    ) -> None:
    """
    Delete the Sync with the given ID.

    - sync_id: ID of the Sync to delete.
    - delete_series: Whether to delete Series that were added by this
    Sync.
    """

    # Get associated Sync, raise 404 if DNE
    sync = get_sync(db, sync_id, raise_exc=True)

    # If deleting Series, iterate and delete Series and all Episodes
    if delete_series_:
        for series in sync.series:
            delete_series(
                db, series, commit_changes=False
            )

    db.delete(sync)
    db.commit()


@sync_router.get('/all')
def get_all_syncs(
        db: Session = Depends(get_database),
    ) -> list[Sync]:
    """Get all defined Syncs."""

    return [Sync.model_validate(sync) for sync in db.query(SyncModel).all()]


@sync_router.get('/emby/all', tags=['Emby'])
def get_all_emby_syncs(
        db: Session = Depends(get_database),
    ) -> list[EmbySync]:
    """Get all defined Syncs that interface with Emby."""

    return [
        EmbySync.model_validate(sync)
        for sync in
        db.query(SyncModel).filter_by(interface='Emby').all()
    ]


@sync_router.get('/jellyfin/all', tags=['Jellyfin'])
def get_all_jellyfin_syncs(
        db: Session = Depends(get_database),
    ) -> list[JellyfinSync]:
    """Get all defined Syncs that interface with Jellyfin."""

    return [
        JellyfinSync.model_validate(sync)
        for sync in
        db.query(SyncModel).filter_by(interface='Jellyfin').all()
    ]


@sync_router.get('/plex/all', tags=['Plex'])
def get_all_plex_syncs(
        db: Session = Depends(get_database),
    ) -> list[PlexSync]:
    """Get all defined Syncs that interface with Plex."""

    return [
        PlexSync.model_validate(sync)
        for sync in
        db.query(SyncModel).filter_by(interface='Plex').all()
    ]


@sync_router.get('/sonarr/all', tags=['Sonarr'])
def get_all_sonarr_syncs(
        db: Session = Depends(get_database),
    ) -> list[SonarrSync]:
    """Get all defined Syncs that interface with Sonarr."""

    return [
        SonarrSync.model_validate(sync)
        for sync in
        db.query(SyncModel).filter_by(interface='Sonarr').all()
    ]


@sync_router.get('/{sync_id}')
def get_sync_by_id(
        sync_id: int,
        db: Session = Depends(get_database),
    ) -> Sync:
    """
    Get the Sync with the given ID.

    - sync_id: ID of the Sync to retrieve.
    """

    return get_sync(db, sync_id, raise_exc=True)


@sync_router.post('/{sync_id}')
def run_sync_(
        background_tasks: BackgroundTasks,
        sync_id: int,
        db: Session = Depends(get_database),
    ) -> list[Series]:
    """
    Run the given Sync by querying the assigned interface, adding any
    new series to the database. Return a list of any new Series.

    - sync_id: ID of the Sync to run.
    """

    # Do not run Sync if any Sync is already running
    if CURRENTLY_RUNNING_SYNC is not None:
        raise HTTPException(
            status_code=422,
            detail=f'Sync {CURRENTLY_RUNNING_SYNC} is already running',
        )

    # Get existing Sync, raise 404 if DNE
    return run_sync(db, get_sync(db, sync_id, raise_exc=True), background_tasks)
