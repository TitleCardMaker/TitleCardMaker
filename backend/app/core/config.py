from pathlib import Path

from app.settings import settings
from modules.preferences import Preferences


if settings.IS_DOCKER:
    preferences_file = Path('/config/config.pickle')
else:
    preferences_file = (
        Path(__file__).parent.parent.parent
            / 'config'
            / 'config.pickle'
    )

PreferencesLocal = Preferences(preferences_file)

__all__ = [
    'settings',
    'PreferencesLocal'
]
