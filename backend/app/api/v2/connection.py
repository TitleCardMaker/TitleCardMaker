from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.backup import backup_data
from app.core.cards import delete_cards
from app.core.connection import add_connection, update_connection
from app.db.query import get_connection
from app.db.users import get_current_user
from app.dependencies import (
    InterfaceGroup,
    get_database,
    get_emby_interfaces,
    get_jellyfin_interfaces,
    get_plex_interfaces,
    get_sonarr_interfaces,
    get_tmdb_interfaces,
    get_tvdb_interfaces,
)
from app.interfaces.v2 import (
    EmbyInterface,
    JellyfinInterface,
    PlexInterface,
    SonarrInterface,
    TautulliInterface,
    TMDbInterface,
    TVDbInterface,
)
from app.logging.logger import log
from app.models.card import Card
from app.models.connection import Connection
from app.models.episode import Episode
from app.models.loaded import Loaded
from app.models.series import Series, Library as SeriesLibrary
from app.models.sync import Sync
from app.models.template import Template
from app.schemas.connection import (
    AnyConnection,
    EmbyConnection,
    JellyfinConnection,
    NewEmbyConnection,
    NewJellyfinConnection,
    NewPlexConnection,
    NewSonarrConnection,
    NewTautulliConnection,
    NewTMDbConnection,
    NewTVDbConnection,
    PlexConnection,
    PotentialSonarrLibrary,
    SonarrConnection,
    TMDbConnection,
    TVDbConnection,
    TautulliIntegrationStatus,
    UpdateEmby,
    UpdateJellyfin,
    UpdatePlex,
    UpdateSonarr,
    UpdateTMDb,
    UpdateTVDb,
)
from app.settings import settings


# Create sub router for all /connection API requests
connection_router = APIRouter(
    prefix='/connection',
    tags=['Connections'],
    dependencies=[Depends(get_current_user)],
)


@connection_router.post('/emby/new')
def add_emby_connection(
        new_connection: NewEmbyConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: (
            InterfaceGroup[int, EmbyInterface]
        ) = Depends(get_emby_interfaces),
    ) -> EmbyConnection:
    """
    Create a new Connection to Emby; adding it to the Database and
    adding an initialized Interface to the InterFaceGroup.

    - new_connection: Details of the new Connection to add and create.
    """

    return add_connection(db, new_connection, interface_group)


@connection_router.post('/jellyfin/new')
def add_jellyfin_connection(
        new_connection: NewJellyfinConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: (
            InterfaceGroup[int, EmbyInterface]
        ) = Depends(get_jellyfin_interfaces),
    ) -> JellyfinConnection:
    """
    Create a new Connection to Jellyfin; adding it to the Database and
    adding an initialized Interface to the InterFaceGroup.

    - new_connection: Details of the new Connection to add and create.
    """

    return add_connection(db, new_connection, interface_group)


@connection_router.post('/plex/new')
def add_plex_connection(
        new_connection: NewPlexConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: (
            InterfaceGroup[int, EmbyInterface]
        ) = Depends(get_plex_interfaces),
    ) -> PlexConnection:
    """
    Create a new Connection to Sonarr; adding it to the Database and
    adding an initialized Interface to the InterFaceGroup.

    - new_connection: Details of the new Connection to add and create.
    """

    return add_connection(db, new_connection, interface_group)


@connection_router.post('/sonarr/new')
def add_sonarr_connection(
        new_connection: NewSonarrConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: (
            InterfaceGroup[int, SonarrInterface]
        ) = Depends(get_sonarr_interfaces),
    ) -> SonarrConnection:
    """
    Create a new Connection to sonarr; adding it to the Database and
    adding an initialized Interface to the InterFaceGroup.

    - new_connection: Details of the new Connection to add and create.
    """

    return add_connection(db, new_connection, interface_group)


@connection_router.post('/tmdb/new')
def add_tmdb_connection(
        new_connection: NewTMDbConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: (
            InterfaceGroup[int, TMDbInterface]
        ) = Depends(get_tmdb_interfaces),
    ) -> TMDbConnection:
    """
    Create a new Connection to TMDb; adding it to the Database and
    adding an initialized Interface to the InterfaceGroup.

    - new_connection: Details of the new Connection to add and create.
    """

    return add_connection(db, new_connection, interface_group)


@connection_router.post('/tvdb/new')
def add_tvdb_connection(
        new_connection: NewTVDbConnection = Body(...),
        db: Session = Depends(get_database),
        interface_group: (
            InterfaceGroup[int, TVDbInterface]
        ) = Depends(get_tvdb_interfaces),
    ) -> TVDbConnection:
    """
    Create a new Connection to TVDb; adding it to the Database and
    adding an initialized Interface to the InterfaceGroup.

    - new_connection: Details of the new Connection to add and create.
    """

    return add_connection(db, new_connection, interface_group)


@connection_router.put('/{connection_type}/{interface_id}/{status}')
def enable_or_disable_connection_by_id(
        connection_type: Literal['emby', 'jellyfin', 'plex', 'sonarr', 'tmdb'],
        interface_id: int,
        status: Literal['enable', 'disable'],
        db: Session = Depends(get_database),
        emby_interfaces: (
            InterfaceGroup[int, EmbyInterface]
        ) = Depends(get_emby_interfaces),
        jellyfin_interfaces: (
            InterfaceGroup[int, JellyfinInterface]
        ) = Depends(get_jellyfin_interfaces),
        plex_interfaces: (
            InterfaceGroup[int, PlexInterface]
        ) = Depends(get_plex_interfaces),
        sonarr_interfaces: (
            InterfaceGroup[int, SonarrInterface]
        ) = Depends(get_sonarr_interfaces),
        tmdb_interfaces: (
            InterfaceGroup[int, TMDbInterface]
        ) = Depends(get_tmdb_interfaces),
        tvdb_interfaces: (
            InterfaceGroup[int, TVDbInterface]
        ) = Depends(get_tvdb_interfaces),
    ) -> AnyConnection:
    """
    Set the enabled/disabled status of the given connection.

    - connection_type: Interface name whose connection is being toggled.
    - interface_id: ID of the Interface to toggle.
    - status: Whether to enable or disable the given interface.
    """

    # Get Connection with this ID
    connection = get_connection(db, interface_id, raise_exc=True)

    # Update enabled status
    connection.enabled = status == 'enable'
    db.commit()

    # Get applicable InterfaceGroup
    group: InterfaceGroup = {
        'emby': emby_interfaces, 'jellyfin': jellyfin_interfaces,
        'plex': plex_interfaces, 'sonarr': sonarr_interfaces,
        'tmdb': tmdb_interfaces, 'tvdb': tvdb_interfaces,
    }[connection_type]

    # Refresh or disable interface within group
    if connection.enabled:
        group.refresh(interface_id, connection.interface_kwargs)
    else:
        group.disable(interface_id)

    return connection


@connection_router.get('/all')
def get_all_connection_details(
        db: Session = Depends(get_database),
    ) -> list[AnyConnection]:
    """Get details for all defined Connections (of all types)."""

    return db.query(Connection).all() # type: ignore


@connection_router.get('/emby/all')
def get_all_emby_connection_details(
        db: Session = Depends(get_database),
    ) -> list[EmbyConnection]:
    """Get details for all defined Emby Connections."""

    return [
        EmbyConnection.model_validate(connection)
        for connection in
        db.query(Connection).filter_by(interface_type='Emby').all()
    ]


@connection_router.get('/emby/{interface_id}')
def get_emby_connection_details_by_id(
        interface_id: int,
        db: Session = Depends(get_database),
    ) -> EmbyConnection:
    """
    Get the details for the Emby connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    return get_connection(db, interface_id, raise_exc=True)


@connection_router.get('/jellyfin/all')
def get_all_jellyfin_connection_details(
        db: Session = Depends(get_database),
    ) -> list[JellyfinConnection]:
    """Get details for all defined Jellyfin Connections."""

    return db.query(Connection)\
        .filter_by(interface_type='Jellyfin')\
        .all() # type: ignore


@connection_router.get('/jellyfin/{interface_id}')
def get_jellyfin_connection_details_by_id(
        interface_id: int,
        db: Session = Depends(get_database),
    ) -> JellyfinConnection:
    """
    Get the details for the Emby connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    return get_connection(db, interface_id, raise_exc=True)


@connection_router.get('/plex/all')
def get_all_plex_connection_details(
        db: Session = Depends(get_database),
    ) -> list[PlexConnection]:
    """Get details for all defined Plex Connections."""

    return db.query(Connection)\
        .filter_by(interface_type='Plex')\
        .all() # type: ignore


@connection_router.get('/plex/{interface_id}')
def get_plex_connection_details_by_id(
        interface_id: int,
        db: Session = Depends(get_database),
    ) -> PlexConnection:
    """
    Get the details for the Plex connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    return get_connection(db, interface_id, raise_exc=True)


@connection_router.get('/sonarr/all')
def get_all_sonarr_connection_details(
        db: Session = Depends(get_database),
    ) -> list[SonarrConnection]:
    """Get details for all defined Sonarr Connections."""

    return db.query(Connection)\
        .filter_by(interface_type='Sonarr')\
        .all() # type: ignore


@connection_router.get('/sonarr/{interface_id}')
def get_sonarr_connection_details_by_id(
        interface_id: int,
        db: Session = Depends(get_database),
    ) -> SonarrConnection:
    """
    Get the details for the Sonarr connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    return get_connection(db, interface_id, raise_exc=True)


@connection_router.get('/tmdb/all')
def get_all_tmdb_connection_details(
        db: Session = Depends(get_database),
    ) -> list[TMDbConnection]:
    """Get details for all defined TMDb Connections."""

    return db.query(Connection)\
        .filter_by(interface_type='TMDb')\
        .all() # type: ignore


@connection_router.get('/tmdb/{interface_id}')
def get_tmdb_connection_details_by_id(
        interface_id: int,
        db: Session = Depends(get_database),
    ) -> TMDbConnection:
    """
    Get the details for the TMDb connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    return get_connection(db, interface_id, raise_exc=True)


@connection_router.get('/tvdb/all')
def get_all_tvdb_connection_details(
        db: Session = Depends(get_database),
    ) -> list[TVDbConnection]:
    """
    Get details for all defined TVDb Connections.
    """

    return db.query(Connection)\
        .filter_by(interface_type='TVDb')\
        .all() # type: ignore


@connection_router.get('/tvdb/{interface_id}')
def get_tvdb_connection_details_by_id(
        interface_id: int,
        db: Session = Depends(get_database),
    ) -> TVDbConnection:
    """
    Get the details for the TVDb connection with the given ID.

    - interface_id: ID of the Interface whose connection details to get.
    """

    return get_connection(db, interface_id, raise_exc=True)


@connection_router.patch('/emby/{interface_id}')
def update_emby_connection(
        interface_id: int,
        update_object: UpdateEmby = Body(...),
        db: Session = Depends(get_database),
        emby_interfaces: (
            InterfaceGroup[int, EmbyInterface]
        ) = Depends(get_emby_interfaces),
    ) -> EmbyConnection:
    """
    Update the Connection details for the given Emby interface.

    - interface_id: ID of the Connection being modified.
    - update_object: Connection details to modify.
    """

    return update_connection(
        db, interface_id, emby_interfaces, update_object
    ) # type: ignore


@connection_router.patch('/jellyfin/{interface_id}')
def update_jellyfin_connection(
        interface_id: int,
        update_object: UpdateJellyfin = Body(...),
        db: Session = Depends(get_database),
        jellyfin_interfaces: InterfaceGroup[
            int, JellyfinInterface
        ] = Depends(get_jellyfin_interfaces),
    ) -> JellyfinConnection:
    """
    Update the Connection details for the given Jellyfin interface.

    - interface_id: ID of the Connection being modified.
    - update_object: Connection details to modify.
    """

    return update_connection(
        db, interface_id, jellyfin_interfaces, update_object,
    )


@connection_router.patch('/plex/{interface_id}')
def update_plex_connection(
        interface_id: int,
        update_object: UpdatePlex = Body(...),
        db: Session = Depends(get_database),
        plex_interfaces: (
            InterfaceGroup[int, PlexInterface]
        ) = Depends(get_plex_interfaces),
    ) -> PlexConnection:
    """
    Update the Connection details for the given Plex interface.

    - interface_id: ID of the Connection being modified.
    - update_object: Connection details to modify.
    """

    return update_connection(
        db, interface_id, plex_interfaces, update_object
    ) # type: ignore


@connection_router.patch('/sonarr/{interface_id}')
def update_sonarr_connection(
        interface_id: int,
        update_object: UpdateSonarr = Body(...),
        db: Session = Depends(get_database),
        sonarr_interfaces: (
            InterfaceGroup[int, SonarrInterface]
        ) = Depends(get_sonarr_interfaces),
    ) -> SonarrConnection:
    """
    Update the Connection details for the given Sonarr connection.

    - interface_id: ID of the Connection being modified.
    - update_object: Connection details to modify.
    """

    return update_connection(
        db, interface_id, sonarr_interfaces, update_object,
    ) # type: ignore


@connection_router.patch('/tmdb/{interface_id}')
def update_tmdb_connection(
        interface_id: int,
        update_object: UpdateTMDb = Body(...),
        db: Session = Depends(get_database),
        tmdb_interfaces: (
            InterfaceGroup[int, TMDbInterface]
        ) = Depends(get_tmdb_interfaces),
    ) -> TMDbConnection:
    """
    Update the Connection details for the given TMDb connection.

    - interface_id: ID of the TMDb Connection being modified.
    - update_object: Connection details to modify.
    """

    return update_connection(
        db, interface_id, tmdb_interfaces, update_object,
    ) # type: ignore


@connection_router.patch('/tvdb/{interface_id}')
def update_tvdb_connection(
        interface_id: int,
        update_object: UpdateTVDb = Body(...),
        db: Session = Depends(get_database),
        tvdb_interfaces: (
            InterfaceGroup[int, TVDbInterface]
        ) = Depends(get_tvdb_interfaces),
    ) -> TVDbConnection:
    """
    Update the Connection details for the given TVDb connection.

    - interface_id: ID of the TVDb Connection being modified.
    - update_object: Connection details to modify.
    """

    return update_connection(
        db, interface_id, tvdb_interfaces, update_object,
    ) # type: ignore


@connection_router.delete('/{interface_id}')
def delete_connection(
        interface_id: int,
        delete_title_cards: bool = Query(default=False),
        db: Session = Depends(get_database),
        emby_interfaces: (
            InterfaceGroup[int, EmbyInterface]
        ) = Depends(get_emby_interfaces),
        jellyfin_interfaces: (
            InterfaceGroup[int, JellyfinInterface]
        ) = Depends(get_jellyfin_interfaces),
        plex_interfaces: (
            InterfaceGroup[int, PlexInterface]
        ) = Depends(get_plex_interfaces),
        sonarr_interfaces: (
            InterfaceGroup[int, SonarrInterface]
        ) = Depends(get_sonarr_interfaces),
        tmdb_interfaces: (
            InterfaceGroup[int, TMDbInterface]
        ) = Depends(get_tmdb_interfaces),
        tvdb_interfaces: (
            InterfaceGroup[int, TVDbInterface]
        ) = Depends(get_tvdb_interfaces),
    ) -> None:
    """
    Delete the Connection with the given ID. This also disables and
    removes the Interface from the relevant InterfaceGroup, deletes any
    linked Syncs, removes this Connection's libraries from any Series,
    any Episode Data Sources from Series and Templates, removes any
    database IDs associated with the Connection (if it is an Emby,
    Jellyfin, or Sonarr Connection), and deletes the Connection from the
    global image source priority and episode data source settings.

    - interface_id: ID of the Connection to delete.
    - delete_title_cards: Whether to delete Title Cards associated with
    this Connection as well.
    """

    # Get Connection with this ID
    connection = get_connection(db, interface_id, raise_exc=True)

    # Remove Interface from group
    try:
        if connection.interface_type == 'Emby':
            emby_interfaces.disable(interface_id)
        elif connection.interface_type == 'Jellyfin':
            jellyfin_interfaces.disable(interface_id)
        elif connection.interface_type == 'Plex':
            plex_interfaces.disable(interface_id)
        elif connection.interface_type == 'Sonarr':
            sonarr_interfaces.disable(interface_id)
        elif connection.interface_type == 'TMDb':
            tmdb_interfaces.disable(interface_id)
        elif connection.interface_type == 'TVDb':
            tvdb_interfaces.disable(interface_id)
    except KeyError:
        pass

    # Remove from invalid Connection list
    settings.invalid_connections = [
        id_ for id_ in settings.invalid_connections if id_ != interface_id
    ]

    # Delete any linked Syncs
    for sync in db.query(Sync).filter_by(interface_id=interface_id).all():
        log.info(f'Deleting {sync}')
        db.delete(sync)

    # Remove from any linked Series libraries, data sources, or image sources
    for series in db.query(Series).all():
        if any(library['interface_id'] == interface_id
               for library in series.libraries):
            log.warning(f'Removing {connection} libraries from {series}')
            series.libraries = [
                library for library in series.libraries
                if library['interface_id'] != interface_id
            ]

        if series.data_source_id == interface_id:
            log.warning(f'Removing Episode Data Source from {series}')
            series.data_source_id = None

        if (series.image_source_priority and
            any(interface_id == id_ for id_ in series.image_source_priority)):
            log.warning(f'Removing Image Source from {series}')
            series.image_source_priority = [
                id_ for id_ in series.image_source_priority
                if id_ != interface_id
            ]

    # Remove linked data and image source from Templates
    for template in db.query(Template).filter_by(data_source_id=interface_id).all():
        log.warning(f'Removing Episode Data Source from {template}')
        template.data_source_id = None
    for template in db.query(Template).all():
        if (template.image_source_priority and
            any(interface_id == id_ for id_ in template.image_source_priority)):
            log.warning(f'Removing Image Source from {template}')
            template.image_source_priority = [
                id_ for id_ in template.image_source_priority
                if id_ != interface_id
            ]

    # Delete from global ISP if present
    settings.image_source_priority = [
        id_ for id_ in settings.image_source_priority
        if id_ != interface_id
    ]

    # Reset EDS if set
    if settings.episode_data_source == interface_id:
        new_eds = db.query(Connection)\
            .filter(Connection.id != interface_id)\
            .first()
        if new_eds:
            settings.episode_data_source = new_eds.id
            log.warning('Reset global Episode Data Source')
        else:
            log.critical('Cannot reassign global Episode Data Source')

    # Remove from Series and Episode database IDs
    for series in db.query(Series).all():
        if series.remove_interface_ids(interface_id):
            log.debug(f'Removed Series IDs from {series!r}')
    for episode in db.query(Episode).all():
        if episode.remove_interface_ids(interface_id):
            log.debug(f'Removed Episode IDs from {episode!r}')

    # Delete Title Cards if indicated
    if delete_title_cards:
        deleted = delete_cards(
            db,
            db.query(Card).filter_by(interface_id=interface_id),
            db.query(Loaded).filter_by(interface_id=interface_id),
        )
        log.info(f'Deleted {len(deleted)} Title Cards')
    else:
        loaded = db.query(Loaded).filter_by(interface_id=interface_id)
        log.info(f'Deleted {loaded.count()} Loaded records')
        loaded.delete()

    # Delete Connection
    db.delete(connection)
    log.info(f'Deleting {connection}')

    # Commit changes to global options and Database
    settings.commit()
    db.commit()


@connection_router.get('/sonarr/{interface_id}/libraries', tags=['Sonarr'])
def get_potential_sonarr_libraries(
        interface_id: int,
        sonarr_interfaces: (
            InterfaceGroup[int, SonarrInterface]
        ) = Depends(get_sonarr_interfaces),
    ) -> list[PotentialSonarrLibrary]:
    """Get the potential library names and paths from Sonarr."""

    if not (sonarr_interface := sonarr_interfaces[interface_id]):
        raise HTTPException(
            status_code=409,
            detail=f'No valid Sonarr Connection with ID {interface_id}',
        )

    # Attempt to interpret library names from root folders
    # This cannot be a direct PotentialSonarrLibrary object since these
    # are used in Jinja templates
    return [
        {
            'name': folder.name.replace('-', ' ').replace('_', ' '),
            'path': str(folder)
        }
        for folder in sonarr_interface.get_root_folders()
    ] # type: ignore


@connection_router.post('/tautulli/check', tags=['Tautulli'])
def check_tautulli_integration(
        tautulli_connection: NewTautulliConnection = Body(...),
        plex_interface_id: int = Query(...),
    ) -> TautulliIntegrationStatus:
    """
    Check whether Tautulli is integrated with TCM.

    - tautulli_connection: Details of the connection to Tautull, and the
    Notification Agent to search for integration of.
    """

    interface = TautulliInterface(
        tcm_url=tautulli_connection.tcm_url,
        tautulli_url=str(tautulli_connection.url),
        api_key=tautulli_connection.api_key.get_secret_value(),
        plex_interface_id=plex_interface_id,
        use_ssl=tautulli_connection.use_ssl,
        agent_name=tautulli_connection.agent_name,
    )

    status = interface.is_integrated()
    return TautulliIntegrationStatus(
        recently_added=status.recently_added,
        watched=status.watched,
    )


@connection_router.post('/tautulli/integrate', tags=['Tautulli'])
def add_tautulli_integration(
        tautulli_connection: NewTautulliConnection = Body(...),
        plex_interface_id: int = Query(...),
    ) -> None:
    """
    Integrate Tautulli with TitleCardMaker by creating a Notification
    Agent that triggers the /cards/key API route to quickly create
    title cards.

    - tautulli_connection: Details of the connection to Tautulli and the
    Notification Agent to search for/create.
    """

    TautulliInterface(
        tcm_url=tautulli_connection.tcm_url,
        tautulli_url=str(tautulli_connection.url),
        api_key=tautulli_connection.api_key.get_secret_value(),
        plex_interface_id=plex_interface_id,
        use_ssl=tautulli_connection.use_ssl,
        agent_name=tautulli_connection.agent_name,
        trigger_watched=tautulli_connection.trigger_watched,
        username=tautulli_connection.username,
    ).integrate()


@connection_router.get('/{interface_id}/libraries')
def get_interface_libraries(interface_id: int) -> list[str]:
    """
    Get the list of previously queried libraries for the given
    Connection.

    - interface_id: ID of the Connection whose libraries to return.
    """

    return settings.libraries.get(interface_id, ('', []))[1]


@connection_router.post('/{interface_id}/libraries')
def refresh_interface_libraries(
        interface_id: int,
        emby_interfaces: (
            InterfaceGroup[int, EmbyInterface]
        ) = Depends(get_emby_interfaces),
        jellyfin_interfaces: (
            InterfaceGroup[int, JellyfinInterface]
        ) = Depends(get_jellyfin_interfaces),
        plex_interfaces: (
            InterfaceGroup[int, PlexInterface]
        ) = Depends(get_plex_interfaces),
    ) -> list[str]:
    """
    Refresh the library list for the given Connection.

    - interface_id: ID of the Connection whose librares to refresh and
    return.
    """

    # Get associated Interface from relevant group
    interface, interface_type = None, None
    if interface_id in emby_interfaces:
        interface = emby_interfaces[interface_id]
        interface_type = 'Emby'
    elif interface_id in jellyfin_interfaces:
        interface = jellyfin_interfaces[interface_id]
        interface_type = 'Jellyfin'
    elif interface_id in plex_interfaces:
        interface = plex_interfaces[interface_id]
        interface_type = 'Plex'

    # Raise 404 if no valid Interface was found
    if interface is None or interface_type is None:
        raise HTTPException(
            status_code=404,
            detail='No valid media server Connection with the given ID'
        )

    # Query libraries, return result
    settings.libraries[interface_id] = (
        interface_type,
        interface.get_libraries()
    )

    return settings.libraries[interface_id][1]


@connection_router.delete('/{interface_id}/libraries')
def delete_interface_libraries(
        interface_id: int,
        backup: bool = Query(default=True),
        unlinked: bool = Query(default=False),
        library_name: str | None = Query(default=None),
        db: Session = Depends(get_database),
    ) -> int:
    """
    Delete any libraries associated with the given Connection which are
    either not a part of the most recently-queried library list or are
    the given name. This will potentially affect many Series. This
    returns the total number of modified Series.

    - interface_id: ID of the Connection whose libraries to delete.
    - backup: Whether to back up the database before deleting any
    libraries.
    - unlinked: Whether to delete unlinked libraries for the given
    Connection. Mutually exclusive with `library_name`.
    - library_name: Name of the library in the given Connection to
    delete . Mutually exclusive with `unlinked`.
    """

    # Perform backup if indicated
    if backup:
        backup_data(settings.config.CURRENT_VERSION)

    # If deleting unlinked then query any Series with at least one library
    keep_list: list[str] = []
    if unlinked:
        # Get list of all libraries to keep
        keep_list = settings.libraries.get(interface_id, ('', []))[1]
        series_list = db.query(Series)\
            .filter(func.json_array_length(Series.libraries) > 0)\
            .all()
    # If deleting a specific library then query any Series with those
    elif library_name:
        series_list = db.query(Series)\
            .filter(Series.libraries.contains(library_name))\
            .all()
    # Raise 422 if neither unlinked flag nor a library name was provided
    else:
        raise HTTPException(
            status_code=422,
            detail='Must provide unlinked flag or library name for deletion'
        )

    def keep_library(library: SeriesLibrary) -> bool:
        """Whether to keep the given library in the Series assignment"""

        return (
            library['interface_id'] != interface_id
            or (
                (unlinked and library['name'] in keep_list)
                or (not unlinked and library['name'] != library_name)
            )
        )

    # Update any Series with unlinked libraries
    changed = 0
    for series in series_list:
        _old = series.libraries
        series.libraries = [
            library
            for library in series.libraries
            if keep_library(library)
        ]

        # If the library list was changed, log and increment counter
        if len(series.libraries) != len(_old):
            changed += 1
            log.debug(
                f'Series[{series.id}].libraries = {_old} -> {series.libraries}'
            )

    # Commit changes if any Series were modified
    if changed > 0:
        db.commit()

    return changed
