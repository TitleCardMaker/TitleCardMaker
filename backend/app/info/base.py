from abc import ABC, abstractmethod
from typing import Any, Callable, Literal, TypeVar, overload

from app.logging.logger import log


type ConnectionID = int | tuple[int, str]
DatabaseID = TypeVar('DatabaseID', str, int)
IDType = TypeVar('IDType', str, int)


class InterfaceID:
    """
    This class describes a "singular" ID for a given interface - i.e.
    all of "Sonarr" - but whose actual ID is varied by the interface
    number/ID itself. The idea being a singular Show/Episode may exist
    on multiple interfaces under multiple IDs, but all those IDs
    correspond to the same content.
    
    This can be viewed as a dictionary that maps interface IDs (keys) to
    actual IDs (values). For example:

    >>> iid = InterfaceID('0:123,1:234')
    >>> print(repr(iid))
    '<InterfaceID {'0': '123', '1': '234'}>'

    These IDs can then be set/got via the interface IDs:

    >>> print(iid.get_id(0))
    '123'
    >>> iid.set_id(999, 2)
    >>> print(iid.get_id(2))
    '999'

    IDs can also be compared with `<` and `>` for evaluating which
    contains more or less information. For example:

    >>> id0 = InterfaceID('0:123,1:234')
    >>> id1 = InterfaceID('0:123')
    >>> id0 > id1
    True
    >>> id0 > '0:123,1:999'
    False

    The intention is to be able to represent a collection of interface
    ID's with a single string that can be stored in a DB, while also
    providing ID-related functionality.
    """


    __slots__ = ('_id_map', )


    def __init__(self,
            id_: str | None = None,
            /,
        ) -> None:
        """
        Construct a new InterfaceID object from the given ID string. If
        the provided ID string has a library identifier, these are
        parsed as part of the ID key.

        >>> id = InterfaceID('0:123,1:234')
        >>> print(id)
        '<InterfaceID {'0': '123', '1': '234'}>'

        >>> id = InterfaceID('0:TV:123,0:Anime:987')
        >>> print(id)
        '<InterfaceID {'0:TV': '123', '0:Anime': '987'}>'

        Args:
            id_: ID string to parse for interface ID pairs.
            libraries: Whether these types of IDs allow per-library ID
                specification (in addition to per-interface).
        """

        # Mapping of key to ID. For library-accessed IDs, the key is
        # the interface ID and library name separated by a colon. For
        # non-library-accessed IDs, the key is the interface ID.
        # For example {'0': 'abc'} or {'0:TV': 'abc'}
        self._id_map: dict[str, str] = {}

        if not id_:
            return None

        # Populate the ID map
        for sub_id in id_.split(','): # ['0:123', '1:234']
            # ['0', '123'] or ['1', 'TV', '123']
            id_vals = sub_id.rsplit(':', maxsplit=1)
            self._id_map[id_vals[0]] = id_vals[1]

        return None


    def set_id(self,
        value: Any,
        /,
        interface_id: int,
        library_name: str | None = None,
    ) -> None:
        """
        Set the ID for the given interface to the given value.

        Args:
            value: Value to set the ID to.
            interface_id: ID of the interface whose ID is being set.
            library_name: Name of the library containing the ID being
                set.
        """

        if library_name:
            key = f'{interface_id}:{library_name}'
        else:
            key = str(interface_id)

        self._id_map[key] = str(value)


    def has_id(self,
            interface_id: int,
            library_name: str | None = None,
            /,
        ) -> bool:
        """
        Determine whether this object has an ID for the given interface
        ID and library name.

        Args:
            interface_id: ID of the interface whose ID to check.
            library_name: Name of the library containing the ID to check.

        Returns:
            True if the object has an ID for the given interface ID and
            library name. False otherwise.
        """

        if library_name:
            return f'{interface_id}:{library_name}' in self._id_map

        return str(interface_id) in self._id_map


    def get_id(self,
            interface_id: int,
            library_name: str | None = None,
            /,
        ) -> str | None:
        """
        Get the ID for the given connection ID and library name.

        Args:
            interface_id: ID of the interface whose ID to get.
            library_name: Name of the library containing the ID.

        Returns:
            ID of the given interface. None if there is no ID.
        """

        if library_name:
            return self._id_map.get(f'{interface_id}:{library_name}')

        return self._id_map.get(str(interface_id))


    def delete_id(self,
            connection_id: int,
            library_name: str | None = None,
            /,
        ) -> None:
        """
        Delete the ID for the given interface location.

        >>> id = InterfaceID('0:123,1:234')
        >>> id.delete_id(0)
        >>> print(id)
        '<InterfaceID {'1': '234'}>'

        >>> id = InterfaceID('0:TV:123,0:Anime:987', libraries=True)
        >>> id.delete_id(0, 'Anime')
        >>> print(id)
        '<InterfaceID {'0:TV': '123'}>'

        Args:
            connection_id: ID of the interface to reset.
            library_name: Name of the library containing the ID being
                deleted.
        """

        if library_name:
            key = f'{connection_id}:{library_name}'
        else:
            key = str(connection_id)

        try:
            del self._id_map[key]
        except KeyError:
            pass


    def equals(self, other: 'InterfaceID', /) -> bool:
        """
        Compare the equality of two InterfaceID objects.

        Args:
            other: InterfaceID to compare against.

        Returns:
            True if any IDs of the two IDs (of the same Interface ID)
            match. False otherwise.
        """

        return any(
            id_ == other._id_map.get(iid)
            for iid, id_ in self._id_map.items()
        )


    def gt(self, other: 'InterfaceID | str', /) -> bool:
        """
        Compare the inequality of two InterfaceID objects.

        >>> id0 = InterfaceID('0:123,1:234,2:345')
        >>> id1 = InterfaceID('0:123')
        >>> id0.gt(id1)
        True
        >>> id0.gt('0:123,1:234,2:999') # Has same ID keys, not more
        False

        Args:
            other: InterfaceID to compare against.

        Returns:
            True if this object contains more information than the other.
            False otherwise.
        """

        if isinstance(other, str):
            other = InterfaceID(other)

        return any(key not in other._id_map for key in self._id_map)


    def lt(self, other: 'InterfaceID | str', /) -> bool:
        """
        Compare the inequality of two InterfaceID objects.

        >>> id0 = InterfaceID('0:123,1:234,2:345')
        >>> id1 = InterfaceID('0:123')
        >>> id1.lt(id0)
        True
        >>> id0.lt('0:123,1:234,2:999') # Has same ID keys, not less
        False

        Args:
            other: InterfaceID to compare against.

        Returns:
            True if this object contains less information than the other.
            False otherwise.
        """

        if isinstance(other, str):
            other = InterfaceID(other)

        return any(key not in self._id_map for key in other._id_map)


    def __bool__(self) -> bool:
        """
        Get the boolean value of this ID.

        Returns:
            True if there is at least one mapped ID, False otherwise.
        """

        return len(self._id_map) > 0


    def __repr__(self) -> str:
        """Get an unambiguous representation of this object."""

        return f'<InterfaceID {self._id_map}>'


    def __str__(self) -> str:
        """
        Get a string representation of this object. This is a string
        that can be used to initialize an exact InterfaceID object.

        >>> id = InterfaceID('0:123,1:234')
        >>> print(str(id))
        '0:123,1:234'

        >>> id = InterfaceID('0:TV:123,0:Anime:987', libraries=True)
        >>> print(str(id))
        '0:TV:123,0:Anime:987'
        """

        return ','.join(f'{key}:{id_}' for key, id_ in self._id_map.items())


    def add_id(self, interface_id: 'str | InterfaceID', /) -> 'InterfaceID':
        """
        Add this object to the given object, returning the combination
        of their IDs. This object's IDs take priority in any interface
        ID conflicts.

        >>> id0 = InterfaceID('0:123,1:234')
        >>> id1 = InterfaceID('1:999,2:987')
        >>> str(id0 + id1) # id0's 1:234 takes priority of id1's 1:999
        '0:123,1:234,2:987'

        Args:
            interface_id: InterfaceID to add to this object. This can
                also be the string representation of an InterfaceID.

        Returns:
            A new InterfaceID object with the combined IDs of this
            object and the given object.
        """

        if isinstance(interface_id, str):
            interface_id = InterfaceID(interface_id)

        return_id = InterfaceID()
        return_id._id_map.update(interface_id._id_map)
        return_id._id_map.update(self._id_map)

        return return_id


    def delete_interface_id(self, connection_id: int, /) -> bool:
        """
        Delete all the IDs associated with the given connection ID.

        >>> id = InterfaceID('0:123,1:234,2:345')
        >>> id.delete_interface_id(1)
        True
        >>> str(id)
        '0:123,2:345'

        >>> id = InterfaceID('0:TV:123,0:Anime:987,1:TV:555')
        >>> id.delete_interface_id(0)
        True
        >>> str(id)
        '1:TV:555'

        Args:
            connection_id: ID of the Connection whose IDs are being
                deleted.

        Returns:
            Whether any IDs were deleted.
        """

        changed = False
        for key in self._id_map:
            if key == str(connection_id):
                del self._id_map[key]
                changed = True
            elif key.startswith(f'{connection_id}:'):
                del self._id_map[key]
                changed = True

        return changed


    def reset(self) -> None:
        """Reset this object."""

        self._id_map = {}


type IdName = Literal[
    'emby_id', 'emby',
    'jellyfin_id', 'jellyfin',
    'sonarr_id', 'sonarr',
    'imdb_id', 'imdb',
    'tmdb_id', 'tmdb',
    'tvdb_id', 'tvdb',
    'tvrage_id', 'tvrage',
]

class DatabaseInfoContainer(ABC):
    """
    This class describes an abstract base class for all Info objects
    containing database ID's. This provides common methods for checking
    whether an object has a specific ID, as well as updating an ID
    within an objct.
    """

    __slots__ = ()


    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError('All DatabaseInfoContainers must define this')


    def __eq__(self, other: 'DatabaseInfoContainer | object') -> bool:
        """
        Compare the equality of two like objects. This compares all
        `_id` attributes of the objects.

        Args:
            other: Reference object to compare equality of.

        Returns:
            True if any of the `_id` attributes of these objects are
            equal (and not None). False otherwise.
        """

        # Verify class comparison
        if not isinstance(other, self.__class__):
            return False

        for attr in self.__slots__:
            if not attr.endswith('_id'):
                continue

            if (attr_val := getattr(self, attr)) is None:
                continue

            if isinstance(attr_val, InterfaceID):
                if attr_val.equals(getattr(other, attr)):
                    return True
            else:
                if attr_val == getattr(other, attr):
                    return True

        return False


    def _update_attribute(self,
            attribute: str,
            value: Any,
            type_: Callable | None = None,
            *,
            interface_id: int | None = None,
            library_name: str | None = None,
        ) -> None:
        """
        Set the given attribute to the given value with the given type.

        Args:
            attribute: Attribute being set.
            value: Value to set the attribute to.
            type_: Optional callable to call on `value` before
                assignment. Resulting value is thus `type_(value)`.
            interface_id: ID of the interface for this ID. Required if
                the specified attribute corresponds to an `InterfaceID`
                object.
            library_name: Name of the library associated with this
                interface. Required if the specified attribute
                corresonsd to a media-server `InterfaceID` object.
        """

        # Value not provided, don't update
        if not value:
            return None

        # Updating an InterfaceID
        if isinstance(getattr(self, attribute), InterfaceID):
            # Update via library name if not already defined
            if library_name:
                if getattr(self, attribute)[interface_id, library_name] is None:
                    getattr(self, attribute)[interface_id, library_name] = value
            # Update directly if not already defined
            elif getattr(self, attribute)[interface_id] is None:
                getattr(self, attribute)[interface_id] = value
        # Non-interface ID that is not defined, update
        elif getattr(self, attribute) is None:
            if type_ is None:
                setattr(self, attribute, value)
            else:
                try:
                    setattr(self, attribute, type_(value))
                except ValueError:
                    log.exception((
                        f'Invalid ID {attribute} of {value} - cannot be '
                        f'converted to type {type_}'
                    ))

        return None


    @overload
    def has_id(self,
            id_: Literal['sonarr', 'sonarr_id'],
            /,
            interface_id: int,
            library_name: None = None
        ) -> bool:
        ...

    @overload
    def has_id(self,
            id_: Literal['emby', 'emby_id', 'jellyfin', 'jellyfin_id'],
            /,
            interface_id: int,
            library_name: str,
        ) -> bool:
        ...

    @overload
    def has_id(self,
            id_: Literal[
                'imdb', 'imdb_id',
                'tmdb', 'tmdb_id',
                'tvdb', 'tvdb_id',
                'tvrage', 'tvrage_id',
            ],
            /,
            interface_id: None = None,
            library_name: None = None,
        ) -> bool:
        ...

    def has_id(self,
            id_: IdName,
            /,
            interface_id: int | None = None,
            library_name: str | None = None,
        ) -> bool:
        """
        Determine whether this object has defined the given ID.

        Args:
            id_: ID being checked.
            interface_id: ID of the interface whose ID is being checked.
            library_name: Name of the library containing the ID being
                checked.

        Returns:
            True if the given ID is defined (i.e. not None) for this
            object. False otherwise.

        Raises:
            ValueError if the indicated ID type is an InterfaceID object
            which requires an interface_id and/or library name, but one
            is not provided.
        """

        id_name = id_.removesuffix('_id') + '_id'

        if isinstance((val := getattr(self, id_name)), InterfaceID):
            if interface_id is None:
                raise ValueError('InterfaceID objects require an interface_id')

            return val.get_id(interface_id, library_name) is not None

        return val is not None


    @overload
    def has_ids(self,
            *ids: IdName,
            interface_id: int,
            library_name: str,
        ) -> bool:
        ...

    @overload
    def has_ids(self,
            *ids: IdName,
            interface_id: int,
            library_name: None = None,
        ) -> bool:
        ...

    @overload
    def has_ids(self,
            *ids: IdName,
            interface_id: None = None,
            library_name: None = None,
        ) -> bool:
        ...

    def has_ids(self,
            *ids: IdName,
            interface_id: int | None = None,
            library_name: str | None = None,
        ) -> bool:
        """
        Determine whether this object has defined all the given ID's.

        Args:
            ids: Any ID's being checked for.
            interface_id: ID of the interface whose IDs are being
                checked.
            library_name: Name of the library containing the ID being
                checked.

        Returns:
            True if all the given ID's are defined (i.e. not None) for
            this object. False otherwise.
        """

        return all(
            self.has_id(
                id_,
                interface_id=interface_id,
                library_name=library_name
            )
            for id_ in ids
        )


    def copy_ids(self, other: 'DatabaseInfoContainer') -> None:
        """
        Copy the database ID's from another DatabaseInfoContainer into
        this object. Only updating the more precise ID's (e.g. this
        object's ID must be None and the other ID must be non-None).

        Args:
            other: Container whose ID's are being copied over.
        """

        # Go through all attributes of this object
        for attr in self.__slots__:
            # Skip non-ID attributes
            if not attr.endswith('_id'):
                continue

            # If this is an InterfaceID, combine
            if isinstance((attr_val := getattr(self, attr)), InterfaceID):
                if attr_val.lt(getattr(other, attr)):
                    log.trace((
                        f'Merging {attr} <-- {getattr(self, attr)!r} + '
                        f'{getattr(other, attr)!r}'
                    ))
                    setattr(
                        self,
                        attr,
                        attr_val.add_id(getattr(other, attr))
                    )
            # Regular ID, copy if this info is missing
            elif not getattr(self, attr) and getattr(other, attr):
                setattr(self, attr, getattr(other, attr))

        return None


    def reset_id(self, id_: str) -> None:
        """
        Reset the ID definition of the given type.

        Args:
            id_: ID name being reset.
        """

        id_ = id_ if id_.endswith('_id') else f'{id_}_id'
        if isinstance(getattr(self, id_), InterfaceID):
            getattr(self, id_).reset()
        else:
            setattr(self, id_, None)
