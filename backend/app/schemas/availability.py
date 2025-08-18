# pylint: disable=missing-class-docstring,missing-function-docstring,no-self-argument
from typing import TypedDict

from app.schemas.base import Base


class ReturnAvailableFontSchema(Base):
    id: int
    name: str
    sort_name: str

class ReturnAvailableSeriesSchema(Base):
    id: int
    name: str
    year: int
    directory: str | None = None

class ReturnAvailableTemplateDict(TypedDict):
    id: int
    name: str
    sort_name: str

class ReturnAvailableTemplateSchema(Base):
    id: int
    name: str
    sort_name: str

class ReturnTranslationLanguageSchema(Base):
    language_code: str
    language: str
