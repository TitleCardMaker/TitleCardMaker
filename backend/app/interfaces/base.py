from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Generic,
    Literal,
    TypeVar,
)

from PIL import Image

from app.info.base import InterfaceID
from app.info.episode import EpisodeInfo
from app.info.series import SeriesInfo
from app.logging.logger import Logger, log

if TYPE_CHECKING:
    from app.models.card import Card
    from app.models.episode import Episode


"""Type definitions"""
type InterfaceType = Literal[
    'Emby', 'Jellyfin', 'Plex', 'Sonarr', 'Tautulli', 'TMDb', 'TVDb'
]
SourceImage = str | bytes | None


class SearchResult:
    """
    Class that defines a SearchResult as returned by an
    EpisodeDataSource. This is essentially a `SeriesInfo` object, with
    additional attributes for a poster, overview, whether it's airing,
    and whether it's been added to TCM.
    """

    __slots__ = ('series_info', 'poster', 'ongoing', 'overview', 'added')


    def __init__(self,
            name: str,
            year: int | None = None,
            poster: str | None = None,
            overview: str | list[str] = ['No overview available'],
            ongoing: bool | None = None,
            *,
            emby_id: int | None = None,
            imdb_id: str | None = None,
            jellyfin_id: str | None = None,
            sonarr_id: str | None  =None,
            tmdb_id: int | None = None,
            tvdb_id: int | None = None,
            tvrage_id: int | None = None,
            added: bool = False,
        ) -> None:
        """
        Initialize this object. See `SeriesInfo.__init__()` for details.
        Other arguments are self-explanatory.
        """

        # Initialize SeriesInfo for the base Series attributes
        self.series_info = SeriesInfo(
            name=name, year=year, emby_id=emby_id, imdb_id=imdb_id,
            jellyfin_id=jellyfin_id, sonarr_id=sonarr_id, tmdb_id=tmdb_id,
            tvdb_id=tvdb_id, tvrage_id=tvrage_id,
        )

        # Store result-specific attributes
        self.added = added
        self.poster = poster
        self.ongoing = ongoing
        if isinstance(overview, str):
            self.overview = overview.splitlines()
        else:
            self.overview = overview


    def __repr__(self) -> str:
        return (
            f'<SearchResult {self.series_info!r}, added={self.added}, poster='
            f'{self.poster}, ongoing={self.ongoing}, overview={self.overview}>'
        )


    def __getattr__(self, attribute: str) -> Any:
        """
        Get an attribute from this object. These can be attributes
        defined in `SearchResult.__slots__`, or an attribute of the
        contained `SeriesInfo` object.
        """

        if attribute in self.__slots__:
            return self.__dict__[attribute]

        # Encode interface IDs into strings for serialization
        value = getattr(self.series_info, attribute)
        return str(value) if isinstance(value, InterfaceID) else value


class WatchedStatus:
    """
    This object defines a single watched status within a specific
    interface (Connection) and library. For example:

    >>> status = WatchedStatus(1, 'TV Shows', True)

    When associated with an Episode, this indicates that the Episode has
    been watched (True) in the 'TV Shows' library of the interface /
    Connection with ID 1.
    """


    __slots__ = ('interface_id', 'library_name', 'status')


    def __init__(self,
            interface_id: int,
            library_name: str | None = None,
            watched: bool | None = None,
        ) -> None:
        """
        Initialize this WatchedStatus for the given library details.

        Args:
            interface_id: ID of the interface associated with this
                status.
            library_name: Name of the library associated with this
                status.
            watched: The actual watched status.
        """

        self.interface_id = interface_id
        self.library_name = library_name
        self.status = watched


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return f'<WatchedStatus {self.interface_id}:{self.library_name}:{self.status}>'


    @property
    def db_key(self) -> str:
        """
        The key which this object should be stored at in the Episode
        database.
        """

        return f'{self.interface_id}:{self.library_name}'

    @property
    def has_status(self) -> bool:
        """Whether this watched status is defined (i.e. not `None`)."""

        return self.status is not None


    @property
    def as_db_entry(self) -> dict[str, bool]:
        """SQL database representation of this status."""

        if self.library_name is not None and self.status is not None:
            return {self.db_key: self.status}

        return {}


class EpisodeDataSource(ABC):
    """
    This class describes an abstract episode data source. Classes of
    this type define sources of Episode data.
    """

    SERIES_IDS: Annotated[
        ClassVar[tuple[str, ...]],
        "Series ID's that can be set by this data source"
    ]

    @abstractmethod
    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> None:
        """Set the series ID's for the given SeriesInfo object."""

        raise NotImplementedError


    @abstractmethod
    def set_episode_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """Set the episode ID's for the given EpisodeInfo objects."""

        raise NotImplementedError


    @abstractmethod
    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
        """Get all the EpisodeInfo objects associated with the given series."""

        raise NotImplementedError


    @abstractmethod
    def query_series(self,
            query: str,
            *,
            log: Logger = log,
        ) -> list[SearchResult]:
        """Query for a Series on this interface."""

        raise NotImplementedError


class Interface(ABC):
    """
    This class describes an abstract interface to some service. This
    class only defines the `__bool__` method and an `active` attribute.
    """

    INTERFACE_TYPE: ClassVar[str]

    def __init__(self) -> None:
        """Initialize this Interface with an inactive state."""

        self.active = False


    def __bool__(self) -> bool:
        """Whether this Interface is active."""

        return self.active


    def activate(self) -> None:
        """Set this Interface as active."""

        self.active = True


class MediaServer(ABC):
    """
    This class describes an abstract base class for all MediaServer
    classes. MediaServer objects are servers like Plex, Emby, and
    Jellyfin that can have title cards loaded into them, as well as
    source images retrieved from them.
    """

    REQUEST_TIMEOUT: Annotated[
        ClassVar[int],
        'Maximum time allowed for a single GET request (in seconds)'
    ] = 30

    DEFAULT_FILESIZE_LIMIT: Annotated[
        ClassVar[str | None],
        'Default filesize limit for all uploaded assets'
    ] = '10 MB'


    @abstractmethod
    def __init__(self, filesize_limit: int | None) -> None:
        """
        Initialize an instance of this object.
        
        Args:
            filesize_limit: Number of bytes to limit a single file to
                during upload.
        """

        self.filesize_limit = filesize_limit


    def compress_image(self,
            image: str | Path,
            *,
            log: Logger = log
        ) -> Path | None:
        """
        Compress the given image until below the filesize limit.

        Args:
            image: Path to the image to compress.
            log: Logger for all log messages.

        Returns:
            Path to the compressed image, or None if the image could not
            be compressed (or image DNE).
        """

        if not image or not (image := Path(image)).exists():
            return None

        # No compression necessary
        if (self.filesize_limit is None
            or image.stat().st_size <= self.filesize_limit):
            return image

        # Start with a quality of 95%, decrement by 5% each time
        quality = 100
        small_image = image

        # Compress the given image until below the filesize limit
        while quality > 0 and small_image.stat().st_size > self.filesize_limit:
            # Process image, exit if cannot be reduced
            quality -= 5
            # TODO Verify if need to resize with .resize((W, H))
            Image.open(small_image)\
                .save(small_image, optimize=True, quality=quality)

        # If still above the limit, warn and return
        if small_image.stat().st_size > self.filesize_limit:
            log.warning(
                f'Cannot reduce filesize of "{image.resolve()}" below limit'
            )
            return None

        # Compression successful, log and return intermediate image
        log.trace(f'Compressed "{image.resolve()}" at {quality}% quality')
        return small_image


    @abstractmethod
    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episodes: list['Episode'],
            *,
            log: Logger = log,
        ) -> bool:
        """Method to get the watched statuses of Episodes."""
        raise NotImplementedError


    @abstractmethod
    def load_title_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_and_cards: (
                list[tuple['Episode', 'Card']]
                | list[tuple['Episode', 'Card', str]]
            ),
            *,
            log: Logger = log,
        ) -> list[tuple['Episode', 'Card']]:
        """
        Abstract method to load title cards within this MediaServer.
        """
        raise NotImplementedError


    @abstractmethod
    def load_season_posters(self,
            library_name: str,
            series_info: SeriesInfo,
            posters: dict[int, str | Path],
            *,
            log: Logger = log,
        ) -> None:
        """
        Abstract method to load season posters within this MediaServer.
        """
        raise NotImplementedError


    @abstractmethod
    def load_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
            image: str | Path,
            *,
            log: Logger = log
        ) -> None:
        """
        Abstract method to load the given poster image within this
        MediaServer.
        """
        raise NotImplementedError


    @abstractmethod
    def load_series_background(self,
            library_name: str,
            series_info: SeriesInfo,
            image: str | Path,
            *,
            log: Logger = log
        ) -> None:
        """
        Abstract method to load the given background image within this
        MediaServer.
        """
        raise NotImplementedError


    @abstractmethod
    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            log: Logger = log,
        ) -> SourceImage:
        """
        Abstract method to get textless source images from this
        MediaServer.
        """
        raise NotImplementedError


    @abstractmethod
    def get_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> SourceImage:
        """
        Abstract method to get a Series poster from this MediaServer.
        """
        raise NotImplementedError


    @abstractmethod
    def get_libraries(self) -> list[str]:
        """
        Abstract method to get all libraries from this MediaServer.
        """
        raise NotImplementedError


class SyncInterface(ABC):
    """
    This class describes an abstract SyncInterface. This is some
    Interface which can be synced (e.g. series can be grabbed) from.
    """


    def get_library_paths(self,
            filter_libraries: list[str] = [], # pylint: disable=unused-argument
        ) -> dict[str, list[str]]:
        """
        Get all libraries and their associated base directories.

        Args:
            filter_libraries: List of library names to filter the return
                by.

        Returns:
            Dictionary whose keys are the library names, and whose
            values are the list of paths to that library's base
            directories.
        """

        return {}


    @abstractmethod
    def get_all_series(self) -> Any:
        """Abstract method to get all series within this Interface."""

        raise NotImplementedError('All SyncInterfaces must implement this')


_InterfaceID = TypeVar('_InterfaceID', bound=int)
_Interface = TypeVar('_Interface', bound=Interface)

class InterfaceGroup(
    Generic[_InterfaceID, _Interface],
    Mapping[_InterfaceID, _Interface],
):
    """
    Class that defines a group of like-classed Interfaces. This class
    creates a mapping of interface IDs to Interface instances, and also
    provides convenience methods for adding and modifying interfaces.

    >>> ig = InterfaceGroup.from_argument_list(
        MyInterface,
        [{'interface_id': 0, 'url': '...', 'api_key': '...'},
         {'interface_id': 2, 'url': '...', 'api_key': '...'}],
    ) # This is practically equivalent to:
    >>> ig = {
        0: MyInterface(url='...', api_key='...'),
        2: MyInterface(url='...', api_key='...'),
    }
    """


    __slots__ = ('cls', 'interfaces', '_uninitialized')


    def __init__(self, cls: type[_Interface]) -> None:
        """
        Initialize this object as a group containing interfaces of
        the given class.

        Args:
            cls: Class to initialize and construct whenever interfaces
                are added.
        """

        self.cls = cls
        self.interfaces: dict[_InterfaceID, _Interface] = {}
        self._uninitialized: dict[_InterfaceID, dict[str, Any]] = {}


    def __repr__(self) -> str:
        """Get an unambigious string representation of this object."""

        return f'<InterfaceGroup[{self.cls.__name__}]{self.interfaces}>'


    def __bool__(self) -> bool:
        """
        Get the truthy-ness of this group of interfaces.

        Returns:
            True if all mapped interfaces are also truthy (activated).
            False otherwise.
        """

        return any(bool(interface) for interface in self.interfaces.values())


    def __len__(self) -> int:
        """
        The number of interfaces defined in this group.
        """

        return len(self.interfaces)


    def __getitem__(self, interface_id: _InterfaceID) -> _Interface | None:
        """
        Get the Interface with the given ID. If the Interface with the
        given ID is defined but not initialized / active, then an
        attempt is made to re-initialize and return it.

        Args:
            interface_id: ID of the Interface to get.

        Returns:
            Interface with the given ID. None if there is no Interface
            with the given ID.
        """

        if interface_id in self.interfaces:
            return self.interfaces[interface_id]

        if interface_id in self._uninitialized:
            try:
                return self.initialize_interface(
                    interface_id, self._uninitialized[interface_id]
                )
            except Exception:
                pass

        return None


    def __setitem__(self,
            interface_id: _InterfaceID,
            interface: _Interface,
        ) -> None:
        """
        Store the given Interface at the given ID.

        Args:
            interface_id: ID to store the given Interface at.
            interface: Interface being stored.
        """

        self.interfaces[interface_id] = interface


    def __contains__(self, interface_id: object | _InterfaceID) -> bool:
        """
        Whether the given interface ID has an associated Interface.
        """

        return (
            interface_id in self.interfaces
            or interface_id in self._uninitialized
        )


    def __iter__(self) -> Iterator[tuple[_InterfaceID, _Interface]]:
        """
        Iterate through this object. Practically identical to calling
        `dict.items()`.

        Returns:
            Tuple of the interface ID and Interface object.
        """

        for interface_id, interface in self.interfaces.items():
            yield interface_id, interface


    @property
    def first_interface_id(self) -> _InterfaceID | None:
        """The first interface ID with a defined, active Interface."""

        for interface_id, interface in self.interfaces.items():
            if interface:
                return interface_id

        return None


    @classmethod
    def from_argument_list(
            cls: type['InterfaceGroup[int, _Interface]'],
            interface_cls: type[_Interface],
            interface_kwargs: Iterable[dict[str, Any]],
            *,
            log: Logger = log,
        ) -> 'InterfaceGroup[int, _Interface]':
        """
        Construct a new `InterfaceGroup` object of the given
        `interface_cls`, each initialized with the given arguments.

        >>> # Construct two MyInterface objects with the given URL's
        >>> ig = InterfaceGroup.from_argument_list(
            MyInterface,
            [{'interface_id': 0, 'url': '...'},
             {'interface_id': 1, 'url': '...'}],
        )

        Args:
            interface_cls: Interface class the created `InterfaceGroup`
                will map and initialize.
            interface_kwargs: Iterable of kwargs for initializing each
                Interface object with.
            log: Logger for all log messages.

        Returns:
            Initialized `InterfaceGroup` object containing initalized
            `interface_cls` objects.
        """

        interface_group = cls(interface_cls)
        for kwargs in interface_kwargs:
            interface_id = kwargs['interface_id']
            interface_group.interfaces[interface_id] = interface_cls(
                **kwargs, log=log,
            )

        return interface_group


    def initialize_interface(self,
            interface_id: _InterfaceID,
            interface_kwargs: dict[str, Any],
            *,
            log: Logger = log,
        ) -> _Interface:
        """
        Construct and initialize the Interface with the given ID.

        Args:
            interface_id: ID of the Interface to initialize.
            interface_kwargs: Kwargs to pass to the Interface
                initialization.
            log: Logger for all log messages.

        Returns:
            Initialized Interface.
        """

        log.debug(f'Initializing {self.cls.__name__}[{interface_id}]..')
        try:
            self.interfaces[interface_id] = self.cls(
                **interface_kwargs, log=log
            )
            self._uninitialized.pop(interface_id, None)
        except Exception as exc:
            self._uninitialized[interface_id] = interface_kwargs
            raise exc
        log.debug(f'Finished initializing {self.cls.__name__}[{interface_id}]')

        return self.interfaces[interface_id]


    def refresh(self,
            interface_id: _InterfaceID,
            interface_kwargs: dict[str, Any],
            *,
            log: Logger = log,
        ) -> _Interface:
        """
        Refresh the given interface.

        Args:
            interface_id: ID of the interface being refreshed.
            interface_kwargs: Keyword arguments to initialize the
                Interface with.
            log: Logger for all log messages.

        Returns:
            Interface initialized with the given arguments.
        """

        self.interfaces[interface_id] = self.cls(**interface_kwargs, log=log)

        return self.interfaces[interface_id]


    def disable(self, interface_id: _InterfaceID, /) -> None:
        """
        Disable (and delete) the Interface with the given ID.

        Args:
            interface_id: ID of the Interface to disable.
        """

        if interface_id in self.interfaces:
            del self.interfaces[interface_id]
