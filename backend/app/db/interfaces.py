from app.interfaces.base import InterfaceGroup as IG
from app.interfaces.emby import EmbyInterface
from app.interfaces.magick import ImageMagickInterface
from app.interfaces.jellyfin import JellyfinInterface
from app.interfaces.plex import PlexInterface
from app.interfaces.sonarr import SonarrInterface
from app.interfaces.tmdb import TMDbInterface
from app.interfaces.tvdb import TVDbInterface
from app.settings import settings


# Initialize all interfaces
ImageMagickInterfaceLocal = None
try:
    ImageMagickInterfaceLocal = ImageMagickInterface(
        use_magick_prefix=settings.use_magick_prefix,
    )
except Exception:
    pass

EmbyInterfaces: IG[int, EmbyInterface] = IG(EmbyInterface)
JellyfinInterfaces: IG[int, JellyfinInterface] = IG(JellyfinInterface)
PlexInterfaces: IG[int, PlexInterface] = IG(PlexInterface)
SonarrInterfaces: IG[int, SonarrInterface] = IG(SonarrInterface)
TMDbInterfaces: IG[int, TMDbInterface] = IG(TMDbInterface)
TVDbInterfaces: IG[int, TVDbInterface] = IG(TVDbInterface)


__all__ = [
    'EmbyInterfaces',
    'ImageMagickInterfaceLocal',
    'JellyfinInterfaces',
    'PlexInterfaces',
    'SonarrInterfaces',
    'TMDbInterfaces',
    'TVDbInterfaces',
]
