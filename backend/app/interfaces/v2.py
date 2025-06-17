from typing import Union

from .emby import EmbyInterface
from .jellyfin import JellyfinInterface
from .plex import PlexInterface
from .magick import ImageMagickInterface
from .sonarr import SonarrInterface
from .tautulli import TautulliInterface
from .tmdb import TMDbInterface
from .tvdb import TVDbInterface


type AnyInterface = Union[
    EmbyInterface,
    JellyfinInterface,
    PlexInterface,
    SonarrInterface,
    TMDbInterface,
    TVDbInterface,
]

type EpisodeDataSourceInterface = Union[
    EmbyInterface,
    JellyfinInterface,
    PlexInterface,
    SonarrInterface,
    TMDbInterface,
]

type MediaServerInterface = Union[
    EmbyInterface,
    JellyfinInterface,
    PlexInterface,
]

__all__ = [
    'AnyInterface',
    'EmbyInterface',
    'EpisodeDataSourceInterface',
    'ImageMagickInterface',
    'JellyfinInterface',
    'MediaServerInterface',
    'PlexInterface',
    'SonarrInterface',
    'TautulliInterface',
    'TMDbInterface',
    'TVDbInterface',
]
