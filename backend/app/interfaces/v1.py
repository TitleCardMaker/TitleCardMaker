from .datafile import DataFileInterface
from .emby import EmbyInterfaceV1
from .magick import ImageMagickInterface
from .jellyfin import JellyfinInterfaceV1
from .plex import PlexInterfaceV1
from .sonarr import SonarrInterfaceV1
from .tautulli import TautulliInterfaceV1
from .tmdb import TMDbInterfaceV1
from .web import WebInterface


__all__ = [
    'DataFileInterface',
    'EmbyInterfaceV1',
    'ImageMagickInterface',
    'JellyfinInterfaceV1',
    'PlexInterfaceV1',
    'SonarrInterfaceV1',
    'TautulliInterfaceV1',
    'TMDbInterfaceV1',
    'WebInterface',
]
