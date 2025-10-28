from typing import Any

from app.schemas.base import (
    Base,
    BaseCardModel,
    BaseCardTypeAllText, # noqa: F401
    BaseCardTypeCustomFontAllText, # noqa: F401
    BaseCardTypeCustomFontNoText, # noqa: F401
    DictKey,
)
from app.cards.types import *


class Extra(Base):
    name: str
    identifier: DictKey
    description: str
    tooltip: str | None = None
    card_type: str | None = None
    default: Any | None = None

LocalCardTypeModels: dict[str, type[BaseCardModel]] = {
    'anime': Anime.get_validator_model(),
    'anime fade': AnimeFade.get_validator_model(),
    'banner': Banner.get_validator_model(),
    'calligraphy': Calligraphy.get_validator_model(),
    'cascade': Cascade.get_validator_model(),
    'comic book': ComicBook.get_validator_model(),
    'cutout': Cutout.get_validator_model(),
    'dictionary': Dictionary.get_validator_model(),
    'divider': Divider.get_validator_model(),
    'fade': Fade.get_validator_model(),
    'formula 1': FormulaOne.get_validator_model(),
    'frame': Frame.get_validator_model(),
    'graph': Graph.get_validator_model(),
    'inset': Inset.get_validator_model(),
    'landscape': Landscape.get_validator_model(),
    'logo': Logo.get_validator_model(),
    'marvel': Marvel.get_validator_model(),
    'music': Music.get_validator_model(),
    'negative space': NegativeSpace.get_validator_model(),
    'notification': Notification.get_validator_model(),
    'olivier': Olivier.get_validator_model(),
    'overline': Overline.get_validator_model(),
    'poster': Poster.get_validator_model(),
    'roman numeral': RomanNumeral.get_validator_model(),
    'score': Score.get_validator_model(),
    'shape': Shape.get_validator_model(),
    'skeleton crew': SkeletonCrew.get_validator_model(),
    'standard': Standard.get_validator_model(),
    'star wars': StarWars.get_validator_model(),
    'striped': Striped.get_validator_model(),
    'textless': Textless.get_validator_model(),
    'tinted glass': TintedGlass.get_validator_model(),
    'tinted frame': TintedFrame.get_validator_model(),
    'white border': WhiteBorder.get_validator_model(),
}

# Add duplicate models under alternate card identifiers so that the
# validator model is not recreated twice
LocalCardTypeModels['4x3'] = LocalCardTypeModels['fade']
LocalCardTypeModels['blurred border'] = LocalCardTypeModels['tinted frame']
LocalCardTypeModels['phendrena'] = LocalCardTypeModels['cutout']
LocalCardTypeModels['photo'] = LocalCardTypeModels['frame']
LocalCardTypeModels['generic'] = LocalCardTypeModels['standard']
LocalCardTypeModels['polymath'] = LocalCardTypeModels['standard']
LocalCardTypeModels['gundam'] = LocalCardTypeModels['poster']
LocalCardTypeModels['ishalioh'] = LocalCardTypeModels['olivier']
LocalCardTypeModels['reality tv'] = LocalCardTypeModels['logo']
LocalCardTypeModels['spotify'] = LocalCardTypeModels['music']
LocalCardTypeModels['musikmann'] = LocalCardTypeModels['white border']
LocalCardTypeModels['negative'] = LocalCardTypeModels['negative space']
LocalCardTypeModels['polygon'] = LocalCardTypeModels['striped']
LocalCardTypeModels['roman'] = LocalCardTypeModels['roman numeral']
LocalCardTypeModels['sherlock'] = LocalCardTypeModels['tinted glass']
