from typing import Any

from app.schemas.base import (
    Base,
    BaseCardModel,
    BaseCardTypeAllText, # noqa: F401
    BaseCardTypeCustomFontAllText, # noqa: F401
    BaseCardTypeCustomFontNoText, # noqa: F401
    DictKey,
)
from modules.cards import *


class Extra(Base):
    name: str
    identifier: DictKey # type: ignore
    description: str
    tooltip: str | None = None
    card_type: str | None = None
    default: Any | None = None

LocalCardTypeModels: dict[str, type[Base | BaseCardModel]] = {
    'anime': AnimeTitleCard.get_validator_model(),
    'banner': BannerTitleCard.get_validator_model(),
    'calligraphy': CalligraphyTitleCard.get_validator_model(),
    'cascade': CascadeTitleCard.get_validator_model(),
    'comic book': ComicBookTitleCard.get_validator_model(),
    'cutout': CutoutTitleCard.get_validator_model(),
    'divider': DividerTitleCard.get_validator_model(),
    'fade': FadeTitleCard.get_validator_model(),
    'formula 1': FormulaOneTitleCard.get_validator_model(),
    'frame': FrameTitleCard.get_validator_model(),
    'graph': GraphTitleCard.get_validator_model(),
    'inset': InsetTitleCard.get_validator_model(),
    'landscape': LandscapeTitleCard.get_validator_model(),
    'logo': LogoTitleCard.get_validator_model(),
    'marvel': MarvelTitleCard.get_validator_model(),
    'music': MusicTitleCard.get_validator_model(),
    'negative space': NegativeSpaceTitleCard.get_validator_model(),
    'notification': NotificationTitleCard.get_validator_model(),
    'olivier': OlivierTitleCard.get_validator_model(),
    'overline': OverlineTitleCard.get_validator_model(),
    'poster': PosterTitleCard.get_validator_model(),
    'roman numeral': RomanNumeralTitleCard.get_validator_model(),
    'score': ScoreTitleCard.get_validator_model(),
    'shape': ShapeTitleCard.get_validator_model(),
    'skeleton crew': SkeletonCrew.get_validator_model(),
    'standard': StandardTitleCard.get_validator_model(),
    'star wars': StarWarsTitleCard.get_validator_model(),
    'striped': StripedTitleCard.get_validator_model(),
    'textless': TextlessTitleCard.get_validator_model(),
    'tinted glass': TintedGlassTitleCard.get_validator_model(),
    'tinted frame': TintedFrameTitleCard.get_validator_model(),
    'white border': WhiteBorderTitleCard.get_validator_model(),
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
