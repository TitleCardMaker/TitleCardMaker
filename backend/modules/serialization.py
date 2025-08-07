from datetime import datetime
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    TypeAlias,
    TypeVar,
    get_args,
    get_origin,
    get_type_hints,
)

from modules.Version import Version


_ExcludedText = 'Excluded from JSON serialization'

T = TypeVar('T')
if TYPE_CHECKING:
    # If type checking, tell the checker to treat SerializationExclusion
    # as a a transparent type alias to Annotated
    SerializationExclusion: TypeAlias = Annotated[T, _ExcludedText]
else:
    # In runtime, add the excluded text metadata to the type annotation
    class SerializationExclusion(Generic[T]):
        """
        A typing annotation "class" for marking a Key as being excluded from
        JSON serialization.

        Example:
        ```python
        class Settings:
            attr1: str = 'included'
            attr2: ExcludedKey[str] = 'excluded'
        ```

        This works by amending the object with an Annotated type including
        the `_ExcludedText` string.
        """
        def __class_getitem__(cls, key: str):
            return Annotated[key, _ExcludedText]


class SerializationMixin:
    """
    A mixin class for allowing a class to be serialized to a dictionary.
    """

    @staticmethod
    def convert(value: Any) -> Any:
        """
        Convert a value to a JSON-serializable type.

        This handles common types such as `pathlib.Path`, `set`, `Version`,
        and `datetime`.
        """

        if isinstance(value, Path):
            return str(value)
        if isinstance(value, set):
            return list(value)
        if isinstance(value, Version):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        return value


    def _serialize(self) -> dict[str, Any]:
        """
        Serialize this object into a dictionary; handling common types
        such as `pathlib.Path`, `set`, `Version`, and `datetime`.

        This does not serialize any attributes which are marked with the
        `SerializationExclusion` type annotation, or which start with an
        underscore.
        """

        def include(key: str) -> bool:
            """Whether to include the given key in the serialization."""

            # Exclude all private attributes
            if key.startswith('_'):
                return False

            # Check for excluded metadata
            annotation = get_type_hints(self, include_extras=True).get(key)
            if annotation and get_origin(annotation) is Annotated:
                _, *metadata = get_args(annotation)
                if metadata and _ExcludedText in metadata:
                    return False

            return True

        return {
            key: self.convert(value)
            for key, value in self.__dict__.items()
            if include(key)
        }
