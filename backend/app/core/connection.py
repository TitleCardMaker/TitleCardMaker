from typing import Union

from sqlalchemy.orm import Session

from app.db.query import get_connection
from app.dependencies import (
    AnyInterface,
    get_emby_interfaces,
    get_jellyfin_interfaces,
    get_plex_interfaces,
    get_sonarr_interfaces,
    get_tmdb_interfaces,
    get_tvdb_interfaces,
)
from app.core.auth import encrypt
from app.models.connection import Connection
from app.schemas.base import UNSPECIFIED
from app.schemas.connection import (
    NewEmbyConnection,
    NewJellyfinConnection,
    NewPlexConnection,
    NewSonarrConnection,
    NewTMDbConnection,
    NewTVDbConnection,
    UpdateEmby,
    UpdateJellyfin,
    UpdatePlex,
    UpdateSonarr,
    UpdateTMDb,
    UpdateTVDb,
)
from app.logging.logger import Logger, SECRETS, log
from app.interfaces.base import InterfaceGroup
from app.interfaces.v2 import (
    EmbyInterface,
    JellyfinInterface,
    PlexInterface,
)
from app.settings import settings


_MediaServerInterface = (EmbyInterface, JellyfinInterface, PlexInterface)
type _NewConnection = Union[
    NewEmbyConnection, NewJellyfinConnection, NewPlexConnection,
    NewSonarrConnection, NewTMDbConnection, NewTVDbConnection,
]
type _UpdateConnection = Union[
    UpdateEmby, UpdateJellyfin, UpdatePlex, UpdateSonarr, UpdateTMDb, UpdateTVDb
]


def initialize_connections(
        db: Session,
        *,
        log: Logger = log,
    ) -> None:
    """
    Initialize all Interfaces (and add them to their respective
    InterfaceGroup). This also adds their secrets to the set of secrets
    for logging.

    Args:
        db: Database with Connection definitions to query.
        log: Logger for all log messages.
    """

    # Initialize each type of Interface
    for interface_group, interface_type in (
        (get_emby_interfaces(), 'Emby'),
        (get_jellyfin_interfaces(), 'Jellyfin'),
        (get_plex_interfaces(), 'Plex'),
        (get_sonarr_interfaces(), 'Sonarr'),
        (get_tmdb_interfaces(), 'TMDb'),
        (get_tvdb_interfaces(), 'TVDb'),
    ):
        # Get all Connections of this interface type
        connections: list[Connection] = db.query(Connection)\
            .filter_by(interface_type=interface_type)\
            .all()

        # Set use_ toggle
        use_connection = any(connection.enabled for connection in connections)
        setattr(settings, f'use_{interface_type.lower()}', use_connection)

        # Initialize an Interface for each Connection (if enabled)
        for connection in connections:
            # Add to set of secrets
            connection.add_secrets(SECRETS)

            # Skip if disabled
            if not connection.enabled:
                log.debug(f'Not initializing {connection} (disabled)')
                continue

            try:
                interface_group.initialize_interface(
                    connection.id, connection.interface_kwargs, log=log,
                )
                interface = interface_group[connection.id]
                if isinstance(interface, _MediaServerInterface):
                    settings.libraries[connection.id] = (
                        interface_type,
                        interface.get_libraries()
                    )
                    log.trace(
                        f'Settings.libraries[{connection.id}] = '
                        f'{settings.libraries[connection.id]}'
                    )
            except Exception:
                settings.invalid_connections.append(connection.id)
                log.exception(f'Error initializing {connection}')

    # Log any invalid Connections
    if settings.invalid_connections:
        log.info(f'Disabled Connection(s) {settings.invalid_connections}')


def add_connection(
        db: Session,
        new_connection: _NewConnection,
        interface_group: InterfaceGroup,
        *,
        log: Logger = log,
    ) -> Connection:
    """
    Create a new Connecton and add it to the Database. If enabled, an
    Interface with the defined details is then initialized and added
    to the InterfaceGroup.

    Args:
        db: Database to add the new Connection to.
        new_connection: Details of the new Connection to add.
        interface_group: InterfaceGroup to add the initialized Interface
            to (if enabled).
        log: Logger for all log messages.

    Returns:
        Newly created Connection.
    """

    # Convert AnyUrl to string for database storage
    connection_data = new_connection.model_dump()
    if 'url' in connection_data and connection_data['url'] is not None:
        connection_data['url'] = str(connection_data['url'])

    # Add to database
    connection = Connection(**connection_data)
    connection.encrypt()
    db.add(connection)
    db.commit()

    # Add API key to set of secrets
    connection.add_secrets(SECRETS)
    log.info(f'Created {connection}')

    # Update global use_ attribute
    setattr(settings, f'use_{connection.interface_type.lower()}', True)

    # Update InterfaceGroup
    if connection.enabled:
        try:
            interface_group.initialize_interface(
                connection.id, connection.interface_kwargs, log=log
            )
        except Exception as exc:
            settings.invalid_connections.append(connection.id)
            raise exc

    # Assign global EDS if unset
    if settings.episode_data_source is None:
        settings.episode_data_source = connection.id
        log.info(f'Set global Episode Data Source to {connection}')
        settings.commit(log=log)
    # Assign global ISP if unset
    if (not settings.image_source_priority
        and connection.interface_type != 'Sonarr'):
        settings.image_source_priority = [connection.id]
        log.info(f'Set global Image Source Priority to [{connection}]')
        settings.commit(log=log)

    return connection


def update_connection(
        db: Session,
        interface_id: int,
        interface_group: InterfaceGroup[int, AnyInterface],
        update_object: _UpdateConnection,
        *,
        log: Logger = log,
    ) -> Connection:
    """
    Update the given Connection, refreshing the interface if any
    attributes were changed.

    Args:
        db: Database to query for the given Connection.
        interface_id: ID of the interface being updated.
        update_object: Update object with attributes to update.
        log: Logger for all log messages.

    Returns:
        Modified Connection with any updated attributes.

    Raises:
        HTTPException (404): There is no Connection with the given ID.
    """

    # Get existing Connection
    connection = get_connection(db, interface_id, raise_exc=True)

    # Update each attribute of the object
    changed = False
    for attr, value in update_object.dict(exclude_defaults=True).items():
        if value != UNSPECIFIED and getattr(connection, attr) != value:
            # Update Connection
            if attr in ('api_key', 'url'):
                # Convert AnyUrl to string before encryption
                if attr == 'url' and value is not None:
                    value = str(value)
                setattr(connection, attr, encrypt(value))
            else:
                setattr(connection, attr, value)
            changed = True

            # Update secrets, log change
            connection.add_secrets(SECRETS)
            log.debug(f'Connection[{interface_id}].{attr} = {value}')

    # If any values were changed, commit to database
    if changed:
        db.commit()
        if connection.enabled:
            # Attempt to re-initialize Interface with new details
            try:
                interface_group.refresh(
                    interface_id, connection.interface_kwargs, log=log
                )
                if interface_id in settings.invalid_connections:
                    settings.invalid_connections.remove(interface_id)
            except Exception as exc:
                if interface_id not in settings.invalid_connections:
                    settings.invalid_connections.append(interface_id)
                raise exc
        # Connection is disabled, remove from group
        else:
            interface_group.disable(interface_id)
            if interface_id in settings.invalid_connections:
                settings.invalid_connections.remove(interface_id)

    return connection
