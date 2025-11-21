from datetime import datetime, timedelta
from typing import Iterator, TypeVar

from fastapi import HTTPException, Query
from huey import SqliteHuey
from requests import get
from sqlalchemy.orm import Session

from app.db.interfaces import (
    EmbyInterfaces,
    ImageMagickInterfaceLocal,
    JellyfinInterfaces,
    PlexInterfaces,
    SonarrInterfaces,
    TMDbInterfaces,
    TVDbInterfaces,
)
from app.db.database import BlueprintSessionMaker, SessionLocal
from app.interfaces.base import Interface, InterfaceGroup
from app.interfaces.v2 import (
    AnyInterface,
    EmbyInterface,
    ImageMagickInterface,
    JellyfinInterface,
    PlexInterface,
    SonarrInterface,
    TMDbInterface,
    TVDbInterface,
)
from app.logging.database import LogsSessionLocal
from app.logging.logger import log
from app.settings import settings


"""Where to download the Blueprint SQL Database from"""
BLUEPRINT_DATABASE_URL = (
    'https://github.com/CollinHeist/TCM-Blueprints-v2/raw/master/blueprints.db'
)

"""Where to read/write the Blueprint SQL database file"""
BLUEPRINT_DATABASE_FILE = settings.temporary_directory / '.blueprints.sqlite'


def get_database() -> Iterator[Session]:
    """Yield a Session to the standard database."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_log_database() -> Iterator[Session]:
    """Yield a Session to the logging database."""

    db = LogsSessionLocal()
    try:
        yield db
    finally:
        db.close()


def download_blueprint_database() -> None:
    """
    Download the Blueprint SQL database from the GitHub repository and
    then write its contents locally.

    Raises:
        HTTPException (404): There is no blueprint database file at the
            attempted URL (`BLUEPRINT_DATABASE_URL`).
        HTTPException: There is some error downloading the blueprint
            database file.
    """

    # If no file was found, raise
    log.trace(f'Downloading Blueprint database from "{BLUEPRINT_DATABASE_URL}"')
    if (response := get(BLUEPRINT_DATABASE_URL, timeout=30)).status_code == 404:
        log.error(
            f'No blueprint database file found at "{BLUEPRINT_DATABASE_URL}"'
        )
        raise HTTPException(
            status_code=404,
            detail='No Blueprint database file found',
        )

    # Non-404 error, raise
    if not response.ok:
        raise HTTPException(
            status_code=response.status_code,
            detail='Error downloading Blueprint database',
        )

    # Write database to file
    BLUEPRINT_DATABASE_FILE.parent.mkdir(exist_ok=True, parents=True)
    BLUEPRINT_DATABASE_FILE.write_bytes(response.content)


_db_expiration = datetime.now()
def get_blueprint_database(
        allow_refresh: bool = Query(default=True),
        force_refresh: bool = Query(default=False),
    ) -> Iterator[Session]:
    """
    Dependency to get a Session to the Blueprint SQLite database.

    Args:
        allow_refresh: Whether to allow a refresh of the database if it
            has expired.
        force_refresh: Whether to force a refresh of the database.

    Yields:
        A Session to the database which is closed afterwards.
    """

    # If refreshing db, database DNE, or file has expired, re-download
    global _db_expiration # pylint: disable=global-statement
    if (force_refresh
        or not BLUEPRINT_DATABASE_FILE.exists()
        or (allow_refresh and _db_expiration <= datetime.now())
    ):
        download_blueprint_database()
        log.debug('Downloaded Blueprint database')
        _db_expiration = datetime.now() + timedelta(hours=2)

    db = BlueprintSessionMaker()
    try:
        yield db
    finally:
        db.close()


def get_scheduler() -> SqliteHuey:
    """
    Dependency to get the global task Scheduler.

    Returns:
        Huey instance responsible for all task scheduling.
    """

    from app.core.schedule import huey
    return huey


_InterfaceType = TypeVar('_InterfaceType', bound=Interface)
def _require_interface(
        interface_group: InterfaceGroup[int, _InterfaceType],
        interface_id: int | None,
        name: str,
    ) -> _InterfaceType:
    """
    Dependency to get the interface with the given ID from the given
    `InterfaceGroup`.

    Args:
        interface_group: InterfaceGroup containing all interfaces of
            this connection.
        interface_id: ID of the interface to return.
        name: Name of the connection this interface corresponds to.

    Returns:
        `Interface` object with the given ID.

    Raises:
        HTTPException (400): The interface is defined but not enabled
            or valid.
        HTTPException (404): There is no interface with the given ID, or
            no ID was provided.
    """

    # No ID provided, raise 404
    if interface_id is None:
        raise HTTPException(
            status_code=404,
            detail=f'No {name} Connection defined'
        )

    # Interface not defined in the group, raise 404
    if interface_id not in interface_group:
        raise HTTPException(
            status_code=404,
            detail=f'No {name} Connection with ID {interface_id}'
        )

    # Interface enabled but not active, raise 400
    if not (iid := interface_group[interface_id]):
        raise HTTPException(
            status_code=400,
            detail=f'Error connecting to {name}[{interface_id}]'
        )

    return iid


# pylint: disable=global-statement
def get_emby_interfaces() -> InterfaceGroup[int, EmbyInterface]:
    """
    Dependency to get all interfaces to Emby.

    Returns:
        Global `InterfaceGroup` of `EmbyInterface` objects.
    """

    return EmbyInterfaces


def require_emby_interface(interface_id: int = Query(...)) -> EmbyInterface:
    """
    Dependency to get the `EmbyInterface` with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `EmbyInterface` with the given ID as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
    """

    return _require_interface(EmbyInterfaces, interface_id, 'Emby')


def refresh_imagemagick_interface() -> None:
    """
    Refresh the global interface to ImageMagick. This reinitializes and
    overrides the object.
    """

    global ImageMagickInterfaceLocal
    ImageMagickInterfaceLocal = ImageMagickInterface(
        use_magick_prefix=settings.use_magick_prefix,
    )


def get_imagemagick_interface() -> ImageMagickInterface:
    """
    Dependency to get the global interface to ImageMagick.

    Returns:
        Global ImageMagickInterface.
    """

    return ImageMagickInterfaceLocal


def get_jellyfin_interfaces() -> InterfaceGroup[int, JellyfinInterface]:
    """
    Dependency to get all interfaces to Jellyfin.

    Returns:
        Global `InterfaceGroup` of `JellyfinInterface` objects.
    """

    return JellyfinInterfaces


def require_jellyfin_interface(interface_id: int = Query(...)) -> JellyfinInterface:
    """
    Dependency to get the `JellyfinInterface` with the given ID. This
    adds `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `JellyfinInterface` with the given ID as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
    """

    return _require_interface(JellyfinInterfaces, interface_id, 'Jellyfn')


def get_plex_interfaces() -> InterfaceGroup[int, PlexInterface]:
    """
    Dependency to get all interfaces to Plex.

    Returns:
        Global `InterfaceGroup` of `PlexInterface` objects.
    """

    return PlexInterfaces


def require_plex_interface(interface_id: int = Query(...)) -> PlexInterface:
    """
    Dependency to get the `PlexInterface` with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `PlexInterface` with the given ID as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
    """

    return _require_interface(PlexInterfaces, interface_id, 'Plex')


def get_sonarr_interfaces() -> InterfaceGroup[int, SonarrInterface]:
    """
    Dependency to get all interfaces to Sonarr.

    Returns:
        Global `InterfaceGroup` of `SonarrInterface` objects.
    """

    return SonarrInterfaces


def require_sonarr_interface(interface_id: int = Query(...)) -> SonarrInterface:
    """
    Dependency to get the `SonarrInterface` with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `SonarrInterface` with the given ID as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
    """

    return _require_interface(SonarrInterfaces, interface_id, 'sonarr')


def get_tmdb_interfaces() -> InterfaceGroup[int, TMDbInterface]:
    """
    Dependency to get all interfaces to TMDb.

    Returns:
        Global `InterfaceGroup` of `TMDbInterface` objects.
    """

    return TMDbInterfaces


def get_first_tmdb_interface(
        interface_id: int | None = Query(default=None),
    ) -> TMDbInterface | None:
    """
    Dependency to get the `TMDbInterface` with the given ID. This adds
    `interface_id` as a Query parameter. If the parameter is omitted,
    then the first-defined TMDbInterface is used.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `TMDbInterface` with the given ID (or the first one if
        `interface_id` is None) as defined in the global
        `InterfaceGroup`. None otherwise.
    """

    # If no ID was provided, get the first available TVDb interface
    if interface_id is None:
        for _, interface in TMDbInterfaces:
            return interface

    try:
        return _require_interface(TMDbInterfaces, interface_id, 'tmdb')
    except HTTPException:
        return None


def require_tmdb_interface(
        interface_id: int | None = Query(default=None)
    ) -> TMDbInterface:
    """
    Dependency to get the `TMDbInterface` with the given ID. This adds
    `interface_id` as a Query parameter. If the parameter is omitted,
    then the first TMDbInterface is used.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        `TMDbInterface` with the given ID (or the first one if
        `interface_id` is None) as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
    """

    # If no ID was provided, get the first available TMDb interface
    if interface_id is None:
        for _, interface in TMDbInterfaces:
            return interface

    return _require_interface(TMDbInterfaces, interface_id, 'tmdb')


def get_tvdb_interfaces() -> InterfaceGroup[int, TVDbInterface]:
    """
    Dependency to get all interfaces to TVDb.

    Returns:
        Global `InterfaceGroup` of `TVDbInterface` objects.
    """

    return TVDbInterfaces


def get_first_tvdb_interface(
        tvdb_interface_id: int | None = Query(default=None)
    ) -> TVDbInterface | None:
    """
    Dependency to get the `TVDbInterface` with the given ID. This adds
    `tvdb_interface_id` as a Query parameter. If the parameter is
    omitted, then the first TVDbInterface is used.

    Args:
        tvdb_interface_id: ID of the interface to get.

    Returns:
        `TVDbInterface` with the given ID (or the first one if
        `tvdb_interface_id` is None) as defined in the global
        `InterfaceGroup`. None otherwise.
    """

    # If no ID was provided, get the first available TVDb interface
    if tvdb_interface_id is None:
        for _, interface in TVDbInterfaces:
            return interface

    try:
        return _require_interface(TVDbInterfaces, tvdb_interface_id, 'tvdb')
    except HTTPException:
        return None


def require_tvdb_interface(
        tvdb_interface_id: int | None = Query(default=None)
    ) -> TVDbInterface:
    """
    Dependency to get the `TVDbInterface` with the given ID. This adds
    `tvdb_interface_id` as a Query parameter. If the parameter is
    omitted, then the first TVDbInterface is used.

    Args:
        tvdb_interface_id: ID of the interface to get.

    Returns:
        `TVDbInterface` with the given ID (or the first one if
        `tvdb_interface_id` is None) as defined in the global
        `InterfaceGroup`.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
    """

    # If no ID was provided, get the first available TVDb interface
    if tvdb_interface_id is None:
        for _, interface in TVDbInterfaces:
            return interface

    return _require_interface(TVDbInterfaces, tvdb_interface_id, 'tvdb')


def require_interface(interface_id: int = Query(...)) -> AnyInterface:
    """
    Dependency to get the interface with the given ID. This adds
    `interface_id` as a Query parameter.

    Args:
        interface_id: ID of the interface to get.

    Returns:
        Interface with the given ID as defined in the global
        `InterfaceGroup` for the corresponding type.

    Raises:
        HTTPException (400): The interface cannot be communicated with.
        HTTPException (404): There is no interface with the given ID.
    """

    groups = (
        (EmbyInterfaces, 'Emby'),
        (JellyfinInterfaces, 'Jellyfin'),
        (PlexInterfaces, 'Plex'),
        (SonarrInterfaces, 'Sonarr'),
        (TMDbInterfaces, 'TMDb'),
        (TVDbInterfaces, 'TVDb')
    )

    for interface_group, name in groups:
        try:
            return _require_interface(interface_group, interface_id, name) # type: ignore
        except HTTPException as exc:
            if exc.status_code != 404:
                raise exc

    raise HTTPException(
        status_code=404,
        detail=f'No Connection with ID {interface_id}'
    )


__all__ = [
    'Session',
    'EmbyInterface',
    'ImageMagickInterface',
    'InterfaceGroup',
    'JellyfinInterface',
    'PlexInterface',
    'SonarrInterface',
    'TMDbInterface',
    'TVDbInterface',
    'get_database',
    'get_blueprint_database',
    'get_emby_interfaces',
    'require_emby_interface',
    'refresh_imagemagick_interface',
    'get_imagemagick_interface',
    'get_first_tvdb_interface',
    'get_jellyfin_interfaces',
    'get_plex_interfaces',
    'get_sonarr_interfaces',
    'get_tmdb_interfaces',
    'get_tvdb_interfaces',
    'require_jellyfin_interface',
    'require_plex_interface',
    'require_sonarr_interface',
    'require_tmdb_interface',
    'require_tvdb_interface',
    'require_interface',
]
