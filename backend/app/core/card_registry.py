from typing import TYPE_CHECKING, Annotated

if TYPE_CHECKING:
    from modules.BaseCardType import BaseCardType, CardTypeDescription


DEFAULT_BLUR_PROFILES: Annotated[
    dict[str, str],
    'Dictionary of card type identifiers to blur profiles'
] = {}

CARD_CLASSES: Annotated[
    dict[str, type['BaseCardType']],
    'Dictionary of card type identifiers to card classes'
] = {}

LocalCards: Annotated[
    list['CardTypeDescription'],
    'List of API details for all local (builtin) cards'
] = []
