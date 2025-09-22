# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import Annotated

from pydantic.types import StringConstraints


EmbyID = Annotated[
    str,
    StringConstraints(
        pattern=r'^(\d+[:-](.+)[:-][a-fA-F0-9]+,)*\d+[:-](.+)[:-][a-fA-F0-9]+$|^$'
    )
]
IMDbID = Annotated[str, StringConstraints(pattern=r'^tt\d{4,}$')] | None
JellyfinID = Annotated[
    str,
    StringConstraints(
        pattern=r'^(\d+[:-](.+)[:-][a-fA-F0-9]+,)*\d+[:-](.+)[:-][a-fA-F0-9]+$|^$'
    )
]
SonarrID = Annotated[
    str,
    StringConstraints(pattern=r'^(\d+[:-]\d+,)*\d+[:-]\d+$|^$')
]
TMDbID = int | None
TVDbID = int | None
TVRageID = int | None
