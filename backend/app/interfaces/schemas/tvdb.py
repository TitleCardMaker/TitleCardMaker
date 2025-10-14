from datetime import date, datetime
from tkinter import NO
from typing import Annotated, Literal
from pydantic import BaseModel, Field, PositiveInt


type StatusType = Literal['Continuing', 'Ended', 'Released']
type ResultType = Literal['company', 'list', 'movie', 'series', 'person']


"""
This is generated with the following code
{
    record_type: {
        art_type['name']: art_type['id']
        for art_type in [
            sub_type for sub_type in b if sub_type['recordType'] == record_type
        ]
    }
    for record_type in set(v['recordType'] for v in response)
}
"""
ArtworkTypes: Annotated[
    dict[str, dict[str, int]],
    'Mapping of record type to a mapping of artwork type names to IDs'
] = {
    'season': {
        'Banner': 6,
        'Poster': 7,
        'Background': 8,
        'Icon': 10,
    },
    'company': {'Icon': 19},
    'award': {'Icon': 26},
    'list': {'Poster': 27},
    'movie': {
        'Poster': 14,
        'Background': 15,
        'Banner': 16,
        'Icon': 18,
        'Cinemagraph': 21,
        'ClearArt': 24,
        'ClearLogo': 25,
    },
    'episode': {
        '16:9 Screencap': 11,
        '4:3 Screencap': 12
    },
    'actor': {'Photo': 13},
    'series': {
        'Banner': 1,
        'Poster': 2,
        'Background': 3,
        'Icon': 5,
        'Cinemagraph': 20,
        'ClearArt': 22,
        'ClearLogo': 23,
    },
}

class AuthenticationData(BaseModel):
    token: str

class Authentication(BaseModel):
    data: AuthenticationData | None = None
    status: Literal['success', 'failure']
    message: str | None = None

class PaginatedLinks(BaseModel):
    prev: str | None = None
    self: str
    next: str | None = None
    total_items: int
    page_size: int

class RemoteID(BaseModel):
    id: str
    # type: int
    sourceName: str

class SearchResult(BaseModel):
    # aliases: list[str] | None = None
    # companies: list[str] | None = None
    # companyType: str | None = None
    # country: Annotated[str, Field(min_length=3, max_length=3)] | None = None
    # director: str | None = None
    # first_air_time: date | None = None
    # genres: list[str] | None = None
    # id: str
    image_url: str
    name: str
    # is_official: bool | None = None
    # name_translated: str | None = None
    # network: str | None = None
    # objectID: str
    # officialList: str
    overview: str
    # overviews: dict[str, str]
    # overview_translated: list[str] | None = None
    # poster: str | None = None
    # posters: list[str] | None = None
    # primary_language: str | None = None
    remote_ids: list[RemoteID] = []
    status: StatusType | None = None
    # slug: str | None = None
    # studios: list[str] | None = None
    # title: str | None = None
    # thumbnail: str | None = None
    translations: dict[str, str] = {}
    # translationsWithLang: list[str] | None = None
    tvdb_id: int
    type: ResultType
    year: int | None = None

class SearchResultResponse(BaseModel):
    status: Literal['success', 'failure']
    message: str | None = None
    data: list[SearchResult] = []

class SeriesSearchResult(SearchResult):
    status: StatusType

class Alias(BaseModel):
    language: str
    name: str

class Status(BaseModel):
    id: int | None = None
    name: str | None = None
    recordType: str = ''
    keepUpdated: bool = False

class SeriesBaseRecord(BaseModel):
    # aliases: list[Alias] = []
    # averageRuntime: int | None = None
    # country: str | None = None
    # defaultSeasonType: int
    # episodes: list[EpisodeBaseRecord] = []
    # firstAired: date
    id: int
    # image: str
    # isOrderRandomized: bool
    # lastAired: date
    # lastUpdated: datetime
    # name: str
    # nameTranslations: list[str] = []
    # nextAired: date | Literal[''] = ''
    # originalCountry: str
    # originalLanguage: str
    # overviewTranslations: list[str] = []
    # score: int
    # slug: str
    # status: Status
    # year: int

class EpisodeBaseRecord(BaseModel):
    # absoluteNumber: int | None = None
    # aired: date
    # airsAfterSeason: int | None = None
    # airsBeforeEpisode: int | None = None
    # airsBeforeSeason: int | None = None
    # finaleType: str | None = None
    id: int
    # image: str | None = None
    # imageType: int | None = None
    # isMovie: Literal[0, 1] = 0
    # lastUpdated: datetime
    # linkedMovie: int | None = None
    # name: str | None = None
    # nameTranslations: list[str] | None = None
    # number: int | None = None
    # overview: str | None = None
    # overviewTranslations: list[str] | None = None
    # runtime: int | None = None
    # seasonNumber: int | None = None
    # seasons: list[SeasonBaseRecord] | None = None
    # seriesId: int
    # seasonName: str | None = None
    # year: int | None = None

class SearchByRemoteIdResult(BaseModel):
    series: SeriesBaseRecord | None = None
    # people: PeopleBaseRecord | None = None
    # movie: MovieBaseRecord | None = None
    episode: EpisodeBaseRecord | None = None
    # company: Company | None = None

class RemoteIDSearchResult(BaseModel):
    status: Literal['success', 'failure']
    message: str | None = None
    data: list[SearchByRemoteIdResult] | None = None

class SeriesBaseRecord(BaseModel):
    aliases: list[Alias] = []
    country: str | None = None
    defaultSeasonType: int
    episodes: list[EpisodeBaseRecord] | None = None
    firstAired: date | Literal[''] = ''
    id: int
    image: str | None = None
    isOrderRandomized: bool = False
    lastAired: date | Literal[''] = ''
    lastUpdated: datetime
    name: str
    nameTranslations: list[str] | None = None
    nextAired: date | Literal[''] = ''
    originalCountry: str | None = None
    originalLanguage: str | None = None
    overviewTranslations: list[str] | None = None
    score: int
    slug: str
    status: Status
    year: int

class EpisodeBaseRecord(BaseModel):
    # absoluteNumber: int | None = None
    aired: date | Literal[''] = ''
    # airsAfterSeason: int | None = None
    # airsBeforeEpisode: int | None = None
    # airsBeforeSeason: int | None = None
    # finaleType: str | None = None
    id: int
    # image: str | None = None
    # imageType: int | None = None
    isMovie: Literal[0, 1] = 0
    # lastUpdated: datetime
    # linkedMovie: int | None = None
    name: str
    # nameTranslations: list[str] | None = None
    number: int
    # overview: str
    # overviewTranslations: list[str] | None = None
    # runtime: int
    seasonNumber: int
    # seasons: SeasonBaseRecord | None = None
    # seriesId: int
    # seasonName: str | None = None
    # year: int | None = None

class SeriesEpisodeData(BaseModel):
    series: SeriesBaseRecord
    episodes: list[EpisodeBaseRecord]

class SeriesEpisodeResponse(BaseModel):
    status: Literal['success', 'failure']
    data: SeriesEpisodeData
    links: PaginatedLinks

class ArtworkExtendedRecord(BaseModel):
    # episodeId: int | None = None
    height: Annotated[int, PositiveInt] = 0
    # id: int
    image: str
    # includesText: bool
    # language: str
    # movieId: int | None = None
    # networkId: int | None = None
    # peopleId: int | None = None
    # score: int
    # seasonId: int
    # seriesId: int | None = None
    # seriesPeopleId: int | None = None
    # status: ArtworkStatus
    # tagOptions: TagOption | None = None
    # thumbnail: str
    # thumbnailHeight: Annotated[int, PositiveInt]
    # thumbnailWidth: Annotated[int, PositiveInt]
    type: Annotated[int, Field(ge=1, le=27)]
    # updatedAt: int
    width: Annotated[int, PositiveInt]

class SeriesExtendedRecord(BaseModel):
    # abbreviation: str | None = None
    # airsDays: SeriesAirsDays
    # airsTime: str | None = None
    # aliases: list[Alias] = []
    artworks: list[ArtworkExtendedRecord] = []
    # averageRuntime: int | None = None
    # characters: list[Character] | None = None
    # contentRatings: list[ContentRating] | None = None
    # country: str | None = None
    # defaultSeasonType: int
    # episodes: list[EpisodeBaseRecord] | None = None
    # firstAired: date | Literal[''] = ''
    # lists: ...
    # genres: GenreBaseRecord | None = None
    # id: int
    # image: str | None = None
    # isOrderRandomized: bool = False
    # lastAired: date | Literal[''] = ''
    # lastUpdated: datetime
    # name: str
    # nameTranslations: list[str] | None = None
    # companies: list[Company] | None = None
    # nextAired: date | Literal[''] = ''
    # originalCountry: str | None = None
    # originalLanguage: str | None = None
    # originalNetwork: Company | None = None
    # overview: str
    # latestNetwork: Company | None = None
    # overviewTranslations: list[str] | None = None
    remoteIds: list[RemoteID] | None = None
    # score: int
    # seasons: list[SeasonBaseRecord] | None = None
    # seasonTypes: list[SeasonType] | None = None
    # slug: str
    # status: Status | None = None
    # tags: list[TagOption] | None = None
    # trailers: list[Trailer] | None = None
    # translations: list[TranslationExtended] | None = None
    # year: int

class SeriesArtworkResponse(BaseModel):
    status: Literal['success', 'failure']
    data: SeriesExtendedRecord
    message: str | None = None

class EpisodeExtendedRecord(BaseModel):
    # aired: date | Literal[''] = ''
    # airsAfterSeason: int | None = None
    # airsBeforeEpisode: int | None = None
    # airsBeforeSeason: int | None = None
    # awards: list[AwardBaseRecord] = []
    # characters: list[Character] = []
    # companies: list[Company] = []
    # contentRatings: list[ContentRating] = []
    # finaleType: Literal['season', 'midseason', 'series'] | None = None
    # id: int
    image: str | None = None
    # imageType: int | None = None
    # isMovie: Literal[0, 1] = 0
    # lastUpdated: datetime
    # linkedMovie: int | None = None
    # name: str
    # nameTranslations: list[str] | None = None
    # networks: list[Company] | None = None
    # nominations: list[AwardNomineeBaseRecord] | None = None
    # number: int
    # overview: str
    # overviewTranslations: list[str] | None = None
    # productionCode: str | None = None
    remoteIds: list[RemoteID] | None = None
    # runtime: int
    # seasonNumber: int
    # seasons: list[SeasonBaseRecord] | None = None
    # seriesId: int | None = None
    # studios: list[Company] | None = None
    # tagOptions: list[TagOption] | None = None
    # trailers: list[Trailer] | None = None
    # translations: TranslationExtended | None = None
    # year: int

class EpisodeExtendedResponse(BaseModel):
    status: Literal['success', 'failure']
    data: EpisodeExtendedRecord
    message: str | None = None

class Translation(BaseModel):
    name: str
    overview: str | None = None
    language: str
    isPrimary: bool = False

class EpisodeTranslationResponse(BaseModel):
    status: Literal['success', 'failure']
    data: Translation
    message: str | None = None
