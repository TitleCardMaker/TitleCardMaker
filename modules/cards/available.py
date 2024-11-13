from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.BaseCardType import BaseCardType, CardTypeDescription

# Dictionary of card type identifiers to blur profiles
DEFAULT_BLUR_PROFILES: dict[str, str] = {}

# Dictionary of card type identifiers to card classes
CARD_CLASSES: dict[str, type['BaseCardType']] = {}

# List of API details for all local (builtin) cards
LocalCards: list['CardTypeDescription'] = []
