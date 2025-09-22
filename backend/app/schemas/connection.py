# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
# pyright: reportInvalidTypeForm=false, reportAssignmentType=false, reportIncompatibleVariableOverride=false
from typing import Annotated, Literal, Union

from pydantic import AnyUrl, SecretStr, StringConstraints, validator

from app.schemas.base import Base, InterfaceType, UNSPECIFIED


# Names of acceptable server types
ServerName = Literal['Emby', 'Jellyfin', 'Plex', 'Sonarr']

# Match hexstrings of A-F and 0-9
Hexstring = Annotated[str, StringConstraints(pattern=r'^[a-fA-F0-9]+$')]

# Match dimensions of the form {width}x{height}
Dimensions = Annotated[
    str,
    StringConstraints(pattern=r'^\d+x\d+$')
]

# Acceptable units for filesize limits
FilesizeUnit = Literal['Bytes', 'Kilobytes', 'Megabytes']
FilesizeLimit = Annotated[
    str,
    StringConstraints(pattern=r'\d+\s+(Bytes|Kilobytes|Megabytes)')
]

# Accepted TMDb 2-letter language codes
TMDbLanguageCode = Literal[
    'ar', 'ar-AE', 'ar-SA', 'bg', 'ca', 'cn-CN', 'cs', 'da', 'de-AT', 'de-CH',
    'de-DE', 'el', 'en', 'es-ES', 'es-MX', 'fa', 'fi', 'fr-CA', 'fr-FR', 'he',
    'hi', 'hu', 'id', 'it-IT', 'it-CH', 'ja', 'ka', 'ko', 'lb', 'lt', 'lv',
    'my', 'nb-NO', 'nl-BE', 'nl-NL', 'nn-NO', 'ms-BN', 'ms-MY', 'ms-SG', 'no',
    'pl', 'pt-BR', 'pt-PT', 'ro', 'ru', 'sk', 'sr-RS', 'sv-FI', 'sv-SE', 'th',
    'tr', 'uk', 'uz-UZ', 'vi', 'zh', 'zh-CN', 'zh-HK', 'zh-SG',
]

# Order types for TVDb seasons
TVDbOrderType = Literal[
    'absolute', 'alternate', 'default', 'dvd', 'official', 'regional'
]

"""
Base classes
"""
class SonarrLibrary(Base):
    interface_id: int
    name: str
    path: str

class PotentialSonarrLibrary(SonarrLibrary):
    interface_id: int | None = None

class BaseServer(Base):
    id: int
    interface_type: InterfaceType
    enabled: bool
    name: str
    url: AnyUrl
    api_key: str
    use_ssl: bool = True

class BaseNewConnection(Base):
    enabled: bool = True
    name: str = 'Server'

class BaseNewServer(BaseNewConnection):
    url: AnyUrl
    api_key: Hexstring
    use_ssl: bool = True

class BaseNewMediaServer(BaseNewServer):
    filesize_limit: FilesizeLimit = '5 Megabytes'

class BaseUpdateServer(Base):
    name: str = UNSPECIFIED
    enabled: bool = UNSPECIFIED
    url: AnyUrl = UNSPECIFIED
    use_ssl: bool = UNSPECIFIED

class BaseUpdateMediaServer(BaseUpdateServer):
    filesize_limit: FilesizeLimit = UNSPECIFIED

"""
Creation classes
"""
class NewEmbyConnection(BaseNewMediaServer):
    name: str = 'Emby Server'
    interface_type: Literal['Emby'] = 'Emby'
    username: str | None = None

class NewJellyfinConnection(BaseNewMediaServer):
    name: str = 'Jellyfin Server'
    interface_type: Literal['Jellyfin'] = 'Jellyfin'
    username: str | None = None

class NewPlexConnection(BaseNewMediaServer):
    name: str = 'Plex Server'
    api_key: str
    interface_type: Literal['Plex'] = 'Plex'
    integrate_with_kometa: bool = False

class NewSonarrConnection(BaseNewServer):
    name: str = 'Sonarr Server'
    interface_type: Literal['Sonarr'] = 'Sonarr'
    downloaded_only: bool = True
    libraries: list[SonarrLibrary] = []

    @validator('libraries', pre=False)
    def validate_library_path_conflicts(
            cls,
            v: list[SonarrLibrary],
        ) -> list[SonarrLibrary]:

        for index, library in enumerate(v):
            for other_library in v[index+1:]:
                if (other_library.path.startswith(library.path)
                    and other_library.name != library.name):
                    separator = '/' if '/' in library.path else '\\'
                    raise ValueError((
                        f'Library path ({other_library.path}) contains '
                        f'other path ({library.path}) - this will cause '
                        f'Library assignment to fail. Add a trailing separator '
                        f'({separator}) to distinguish the two.'
                    ))

        return v

class NewTautulliConnection(BaseNewServer):
    api_key: SecretStr
    tcm_url: str
    agent_name: str = 'TitleCardMaker'
    trigger_watched: bool = True
    username: str | None = None

class NewTMDbConnection(Base):
    name: str = 'TMDb'
    interface_type: Literal['TMDb'] = 'TMDb'
    enabled: bool = True
    api_key: Hexstring
    minimum_dimensions: Dimensions = '0x0'
    skip_localized: bool = True
    language_priority: list[TMDbLanguageCode] = ['en']

    @validator('language_priority', pre=True)
    def comma_separate_language_codes(cls, v):
        if isinstance(v, list):
            return v
        if v == '':
            return ['en']
        return [str(s).lower().strip() for s in v.split(',') if str(s).strip()]

class NewTVDbConnection(Base):
    name: str = 'TVDb'
    interface_type: Literal['TVDb'] = 'TVDb'
    enabled: bool = True
    api_key: str
    episode_ordering: TVDbOrderType = 'default'
    include_movies: bool = False
    minimum_dimensions: Dimensions = '0x0'
    language_priority: list[str] = ['eng']

"""
Update classes
"""
class UpdateEmby(BaseUpdateMediaServer):
    api_key: Hexstring = UNSPECIFIED
    username: str | None = UNSPECIFIED

class UpdateJellyfin(BaseUpdateMediaServer):
    api_key: Hexstring = UNSPECIFIED
    username: str | None = UNSPECIFIED

class UpdatePlex(BaseUpdateMediaServer):
    api_key: str = UNSPECIFIED
    integrate_with_kometa: bool = UNSPECIFIED

class UpdateSonarr(BaseUpdateServer):
    api_key: Hexstring = UNSPECIFIED
    use_ssl: bool = UNSPECIFIED
    downloaded_only: bool = UNSPECIFIED
    libraries: list[SonarrLibrary] = UNSPECIFIED

    @validator('libraries', pre=False)
    def remove_empty_strings(
            cls,
            v: list[SonarrLibrary],
        ) -> list[SonarrLibrary]:
        return [library for library in v if library.name and library.path]

    @validator('libraries', pre=False)
    def validate_library_path_conflicts(
            cls,
            v: list[SonarrLibrary],
        ) -> list[SonarrLibrary]:

        for index, library in enumerate(v):
            for other_library in v[index+1:]:
                if other_library.path.startswith(library.path):
                    separator = '/' if '/' in library.path else '\\'
                    raise ValueError((
                        f'Library path ({other_library.path}) contains '
                        f'other path ({library.path}) - this will cause '
                        f'Library assignment to fail. Add a trailing separator '
                        f'({separator}) to distinguish the two.'
                    ))

        return v

class UpdateTMDb(Base):
    enabled: bool = UNSPECIFIED
    api_key: Hexstring = UNSPECIFIED
    minimum_dimensions: Dimensions = UNSPECIFIED
    skip_localized: bool = UNSPECIFIED
    language_priority: list[TMDbLanguageCode] = UNSPECIFIED

    @validator('language_priority', pre=True)
    def comma_separate_language_codes(cls, v):
        return list(map(lambda s: str(s).strip(), v.split(',')))

class UpdateTVDb(Base):
    enabled: bool = UNSPECIFIED
    api_key: str = UNSPECIFIED
    episode_ordering: TVDbOrderType = UNSPECIFIED
    include_movies: bool = UNSPECIFIED
    minimum_dimensions: Dimensions = UNSPECIFIED
    language_priority: list[str] = UNSPECIFIED

    @validator('language_priority', pre=True)
    def comma_separate_language_codes(cls, v):
        return list(map(lambda s: str(s).strip(), v.split(',')))

"""
Return classes
"""
class EmbyConnection(BaseServer):
    url: str
    username: str | None
    filesize_limit: FilesizeLimit

class JellyfinConnection(BaseServer):
    url: str
    username: str | None
    filesize_limit: FilesizeLimit

class PlexConnection(BaseServer):
    url: str
    integrate_with_kometa: bool
    filesize_limit: FilesizeLimit

class SonarrConnection(BaseServer):
    url: str
    downloaded_only: bool
    libraries: list[SonarrLibrary]

class TMDbConnection(Base):
    id: int
    interface_type: Literal['TMDb'] = 'TMDb'
    enabled: bool
    name: str
    api_key: str
    minimum_dimensions: str
    skip_localized: bool
    language_priority: list[TMDbLanguageCode]

class TVDbConnection(Base):
    id: int
    interface_type: Literal['TVDb'] = 'TVDb'
    enabled: bool
    name: str
    api_key: str
    episode_ordering: TVDbOrderType
    include_movies: bool
    minimum_dimensions: str
    language_priority: list[str]

class TautulliIntegrationStatus(Base):
    recently_added: bool
    watched: bool

AnyConnection = Union[
    EmbyConnection,
    JellyfinConnection,
    PlexConnection,
    SonarrConnection,
    TMDbConnection,
    TVDbConnection,
]
