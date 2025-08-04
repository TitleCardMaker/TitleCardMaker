
class InvalidCardSettings(Exception):
    pass

class InvalidFormatString(InvalidCardSettings):
    pass

class MissingSourceImage(InvalidCardSettings):
    pass

class UnknownCardType(InvalidCardSettings):
    pass
