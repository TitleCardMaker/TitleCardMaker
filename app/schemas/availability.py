# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from app.schemas.base import Base


class AvailableFont(Base):
    id: int
    name: str

class AvailableSeries(Base):
    id: int
    name: str
    year: int
    directory: str | None = None

class AvailableTemplate(Base):
    id: int
    name: str

class TranslationLanguage(Base):
    language_code: str
    language: str
