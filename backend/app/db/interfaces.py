from app.core.config import PreferencesLocal
from app.interfaces.EmbyInterface2 import EmbyInterface
from modules.ImageMagickInterface import ImageMagickInterface
from modules.InterfaceGroup import InterfaceGroup as IG
from modules.JellyfinInterface2 import JellyfinInterface
from modules.PlexInterface2 import PlexInterface
from modules.SonarrInterface2 import SonarrInterface
from modules.TMDbInterface2 import TMDbInterface
from modules.TVDbInterface import TVDbInterface


# Initialize all interfaces
ImageMagickInterfaceLocal = None
try:
    ImageMagickInterfaceLocal = ImageMagickInterface(
        use_magick_prefix=PreferencesLocal.use_magick_prefix,
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
    'PreferencesLocal',
]
