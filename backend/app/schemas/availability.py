# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from app.schemas.base import Base


class ReturnAvailableFontSchema(Base):
    id: int
    name: str

class ReturnAvailableSeriesSchema(Base):
    id: int
    name: str
    year: int
    directory: str | None = None

class ReturnAvailableTemplateSchema(Base):
    id: int
    name: str

class ReturnTranslationLanguageSchema(Base):
    language_code: str
    language: str
