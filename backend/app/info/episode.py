from datetime import datetime
from typing import TYPE_CHECKING, Any, TypedDict

from num2words import num2words
from plexapi.video import Episode as PlexEpisode
from sqlalchemy import ColumnElement, and_, false as sql_false, func, or_, not_
from titlecase import titlecase

from app.cards.title import Title
from app.info.base import DatabaseInfoContainer, InterfaceID
from app.logging.logger import Logger, log

if TYPE_CHECKING:
    from app.models.episode import Episode

# pylint: disable=missing-class-docstring
class UserData(TypedDict):
    Played: bool | None

class EmbyProviderIDs(TypedDict):
    Imdb: str | None
    Tmdb: int | None
    Tvdb: int | None
    TvRage: int | None

class EmbyEpisodeDict(TypedDict):
    Name: str
    ParentIndexNumber: int
    IndexNumber: int
    Id: int
    ProviderIds: EmbyProviderIDs
    PremiereDate: str
    UserData: UserData

class EpisodeDatabaseIDs(TypedDict):
    emby_id: str
    imdb_id: str | None
    jellyfin_id: str
    tmdb_id: int | None
    tvdb_id: int | None
    tvrage_id: int | None

class EpisodeCharacteristics(TypedDict, total=False):
    season_number: int
    episode_number: int
    absolute_number: int | None
    absolute_episode_number: int
    airdate: datetime | None

class EpisodeIndices(TypedDict):
    season_number: int
    episode_number: int
    absolute_number: int | None
# pylint: enable=missing-class-docstring


def imdb_str(id_: str | int | Any, /) -> str:
    """Convert an IMDb ID to a string."""

    if isinstance(id_, (int, str)):
        if (id := str(id_)).startswith('tt'):
            return id
        return f'tt{id}'
    raise ValueError(f'Invalid IMDb ID: {id_}')


class EpisodeInfo(DatabaseInfoContainer):
    """
    This class describes static information about an Episode, such as
    the season, episode, and absolute number, as well as the various IDs
    associated with it.
    """

    __slots__ = (
        'absolute_number',
        'airdate',
        'episode_number',
        'emby_id',
        'imdb_id',
        'jellyfin_id',
        'plex_id',
        'season_number',
        'tmdb_id',
        'tvdb_id',
        'tvrage_id',
        'title',
    )


    def __init__(self,
            title: str | Title,
            season_number: int,
            episode_number: int,
            absolute_number: int | None = None,
            *,
            emby_id: str | None = None,
            imdb_id: str | None = None,
            jellyfin_id: str | None = None,
            plex_id: str | None = None,
            tmdb_id: int | None = None,
            tvdb_id: int | None = None,
            tvrage_id: int | None = None,
            airdate: datetime | None = None,
        ) -> None:
        """
        Initialize this object with the given title, indices, database
        ID's, airdate.
        """

        self.title = title.full_title if isinstance(title, Title) else title
        self.season_number = int(season_number)
        self.episode_number = int(episode_number)
        self.absolute_number = None if absolute_number is None else int(absolute_number)
        self.airdate = airdate

        self.emby_id = InterfaceID(emby_id, type_=int, libraries=True)
        self.imdb_id: str | None = None
        self.jellyfin_id = InterfaceID(jellyfin_id, type_=str, libraries=True)
        self.plex_id = InterfaceID(plex_id, type_=int, libraries=True)
        self.tmdb_id: int | None = None
        self.tvdb_id: int | None = None
        self.tvrage_id: int | None = None

        self.set_imdb_id(imdb_id)
        self.set_tmdb_id(tmdb_id)
        self.set_tvdb_id(tvdb_id)
        self.set_tvrage_id(tvrage_id)


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        attributes = ', '.join(f'{attr}={getattr(self, attr)!r}'
            for attr in self.__slots__
            if not attr.startswith('__')
        )

        return f'<EpisodeInfo {attributes}>'


    def __str__(self) -> str:
        """Returns a string representation of the object."""

        return f'S{self.season_number:02}E{self.episode_number:02}'


    def __eq__(self, other: 'EpisodeInfo | PlexEpisode | object') -> bool:
        """
        Returns whether the given episode info object corresponds to the
        same entry. This comparison prioritizes ID matches, and gives
        lower priority to index and title matching.

        Args:
            other: Other info container to compare.

        Returns:
            True if any database IDs match or there is an exact index
            and title match. False otherwise.

        Raises:
            TypeError if `other` is not an `EpisodeInfo` or
            `plexapi.video.Episode` object.
        """

        # If a PlexEpisode, compare indirectly
        if isinstance(other, PlexEpisode):
            # Attempt database ID match
            id_matches = 0
            for guid in other.guids:
                if self.imdb_id and 'imdb://' in guid.id: # type: ignore
                    if self.imdb_id == guid.id.removeprefix('imdb://'):
                        id_matches += 1
                    else:
                        id_matches -= 1
                if self.tmdb_id and 'tmdb://' in guid.id: # type: ignore
                    if self.tmdb_id == int(guid.id.removeprefix('tmdb://')):
                        id_matches += 1
                    else:
                        id_matches -= 1
                if self.tvdb_id and 'tvdb://' in guid.id: # type: ignore
                    if self.tvdb_id == int(guid.id.removeprefix('tvdb://')):
                        id_matches += 1
                    else:
                        id_matches -= 1

            # Require at least one net positive ID match
            if id_matches > 0:
                return True

            # Attempt title and index match
            return (
                self.season_number == other.parentIndex
                and self.episode_number == other.index
                and self.full_title.matches(other.title)
            )

        # Verify the comparison is another EpisodeInfo object
        if not isinstance(other, EpisodeInfo):
            return False

        # Count how many IDs match and contradict
        id_matches, id_mismatches = 0, 0
        for this_id, other_id in [
            (self.emby_id, other.emby_id),
            (self.imdb_id, other.imdb_id),
            (self.jellyfin_id, other.jellyfin_id),
            (self.tmdb_id, other.tmdb_id),
            (self.tvdb_id, other.tvdb_id),
            (self.tvrage_id, other.tvrage_id),
        ]:
            if this_id is not None and this_id == other_id:
                id_matches += 1
            elif (this_id is not None and other_id is not None
                and this_id != other_id):
                id_mismatches += 1

        # More than one ID match is equality, more than one mismatch is
        # an inequality
        if id_matches > 1:
            return True
        if id_mismatches > 1:
            return False

        # Require title match for index equality
        return (
            # Season number match
            self.season_number == other.season_number
            and (
                # Episode number match
                self.episode_number == other.episode_number
                or (
                    # Both have absolute numbers that match
                    (
                        self.absolute_number is not None
                        and self.absolute_number == other.absolute_number
                    )
                    # One has absolute number that matches the others episode
                    or (
                        self.absolute_number == other.episode_number
                        or self.episode_number == other.absolute_number
                    )
                )
            )
            # And title match
            and self.full_title.matches(other.full_title)
        )


    @property
    def full_title(self) -> Title:
        """This Episode's title (as a Title object)."""

        return Title(self.title)


    @classmethod
    def from_emby_info(
            cls,
            info: EmbyEpisodeDict,
            interface_id: int,
            library_name: str,
        ) -> 'EpisodeInfo':
        """
        Create an EpisodeInfo object from the given emby episode data.

        Args:
            info: Dictionary of episode info.
            interface_id: ID of the Emby interface whose data is being
                parsed.
            library_name: Name of the library associated with this
                Series.

        Returns:
            EpisodeInfo object defining the given data.
        """

        # Parse airdate
        airdate = None
        try:
            airdate = datetime.strptime(
                info['PremiereDate'], '%Y-%m-%dT%H:%M:%S.%f000000Z'
            )
        except KeyError:
            log.debug('Cannot parse episode airdate')
        except Exception:
            log.exception('Cannot parse airdate')
            log.debug(f'Episode data: {info}')

        # TMDb movies might have an ID formatted as {id}-{name} or ../{name}/{id}
        if (tmdb_id := info['ProviderIds'].get('Tmdb')) is not None:
            if '-' in (tmdb_id_str := str(tmdb_id)):
                try:
                    tmdb_id = int(tmdb_id_str.split('-', maxsplit=1)[0])
                except ValueError:
                    pass
            elif '/' in tmdb_id_str:
                try:
                    tmdb_id = int(tmdb_id_str.rsplit('/', maxsplit=1)[-1])
                except ValueError:
                    pass

        return cls(
            info['Name'],
            info['ParentIndexNumber'],
            info['IndexNumber'],
            emby_id=f'{interface_id}:{library_name}:{info["Id"]}',
            imdb_id=info['ProviderIds'].get('Imdb'),
            tmdb_id=tmdb_id,
            tvdb_id=info['ProviderIds'].get('Tvdb'),
            tvrage_id=info['ProviderIds'].get('TvRage'),
            airdate=airdate,
        )


    @classmethod
    def from_jellyfin_info(
            cls,
            info: EmbyEpisodeDict,
            interface_id: int,
            library_name: str,
            *,
            log: Logger = log,
        ) -> 'EpisodeInfo':
        """
        Create an EpisodeInfo object from the given Jellyfin episode
        data.

        Args:
            info: Dictionary of episode info.
            interface_id: ID of the Jellyfin interface whose data is
                being parsed.
            library_name: Name of the library associated with this
                Series.
            log: Logger for all log messages.

        Returns:
            EpisodeInfo object defining the given data.
        """

        # Parse airdate
        airdate = None
        if 'PremiereDate' in info:
            try:
                airdate = datetime.strptime(
                    info['PremiereDate'], '%Y-%m-%dT%H:%M:%S.%f000000Z'
                )
            except Exception as e:
                log.debug(f'Cannot parse airdate {e} - {info=}')

        return cls(
            info['Name'],
            info['ParentIndexNumber'],
            info['IndexNumber'],
            imdb_id=info.get('ProviderIds', {}).get('Imdb'),
            jellyfin_id=f'{interface_id}:{library_name}:{info["Id"]}',
            tmdb_id=info.get('ProviderIds', {}).get('Tmdb'),
            tvdb_id=info.get('ProviderIds', {}).get('Tvdb'),
            tvrage_id=info.get('ProviderIds', {}).get('TvRage'),
            airdate=airdate,
        )


    @classmethod
    def from_plex_episode(cls,
            plex_episode: PlexEpisode,
            interface_id: int,
            library_name: str,
        ) -> 'EpisodeInfo':
        """
        Create an EpisodeInfo object from a `plexapi.video.Episode`
        object.

        Args:
            plex_episode: Episode to create an object from. Any
                available GUID's are utilized.
            interface_id: ID of the PlexInterface whose data is being
                parsed.
            library_name: Name of the library associated with this
                Series.

        Returns:
            EpisodeInfo object encapsulating the given Episode.
        """

        episode_info = cls(
            title=plex_episode.title,
            season_number=int(plex_episode.parentIndex),
            episode_number=int(plex_episode.index),
            plex_id=f'{interface_id}:{library_name}:{plex_episode.ratingKey}',
            airdate=plex_episode.originallyAvailableAt,
        )

        # Add any GUIDs as database ID's
        for guid in plex_episode.guids:
            if 'imdb://' in guid.id:
                episode_info.set_imdb_id(guid.id[len('imdb://'):])
            elif 'tmdb://' in guid.id:
                episode_info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
            elif 'tvdb://' in guid.id:
                episode_info.set_tvdb_id(int(guid.id[len('tvdb://'):]))

        return episode_info


    @property
    def key(self) -> str:
        """Key for this episode - i.e. s1e1"""

        return f's{self.season_number}e{self.episode_number}'


    @property
    def index_str(self) -> str:
        """Index string for this episode - i.e. S01E01"""

        return f'S{self.season_number:02}E{self.episode_number:02}'


    @property
    def has_all_ids(self) -> bool:
        """Whether this object has all ID's defined"""

        return all(self.ids.values())


    @property
    def ids(self) -> EpisodeDatabaseIDs:
        """This object's ID's (as a dictionary)"""

        return {
            'emby_id': str(self.emby_id),
            'imdb_id': self.imdb_id,
            'jellyfin_id': str(self.jellyfin_id),
            'tmdb_id': self.tmdb_id,
            'tvdb_id': self.tvdb_id,
            'tvrage_id': self.tvrage_id,
        }


    @property
    def characteristics(self) -> EpisodeCharacteristics:
        """
        Get the characteristics of this object for formatting.

        Returns:
            Dictionary of characteristics that define this object. Keys
            are the indices of the episode in numeric, cardinal, and
            ordinal form.
        """

        if self.absolute_number is None:
            effective_absolute = self.episode_number
        else:
            effective_absolute = self.absolute_number

        return {
            'season_number': self.season_number,
            'episode_number': self.episode_number,
            'absolute_number': self.absolute_number,
            'absolute_episode_number': effective_absolute,
            'airdate': self.airdate,
        }


    @property
    def indices(self) -> EpisodeIndices:
        """This object's season/episode indices (as a dictionary)"""

        return {
            'season_number': self.season_number,
            'episode_number': self.episode_number,
            'absolute_number': self.absolute_number,
        }


    def set_emby_id(self,
            emby_id: int | None,
            interface_id: int,
            library_name: str,
        ) -> None:
        """Set the Emby ID of this object. See `_update_attribute()`."""

        self._update_attribute(
            'emby_id', emby_id,
            interface_id=interface_id, library_name=library_name,
        )


    def set_imdb_id(self, imdb_id: str | None) -> None:
        """Set the IMDb ID of this object. See `_update_attribute()`."""

        self._update_attribute('imdb_id', imdb_id, imdb_str)


    def set_jellyfin_id(self,
            jellyfin_id: str | None,
            interface_id: int,
            library_name: str,
        ) -> None:
        """Set the Jellyfin ID of this object. See `_update_attribute()`."""

        self._update_attribute(
            'jellyfin_id', jellyfin_id,
            interface_id=interface_id, library_name=library_name,
        )


    def set_tmdb_id(self, tmdb_id: int | None) -> None:
        """Set the TMDb ID of this object. See `_update_attribute()`."""

        self._update_attribute('tmdb_id', tmdb_id, int)


    def set_tvdb_id(self, tvdb_id: int | None) -> None:
        """Set the TVDb ID of this object. See `_update_attribute()`."""

        self._update_attribute('tvdb_id', tvdb_id, int)


    def set_tvrage_id(self, tvrage_id: int | None) -> None:
        """Set the TVRage ID of this object. See `_update_attribute()`."""

        self._update_attribute('tvrage_id', tvrage_id, int)


    def set_airdate(self, airdate: datetime) -> None:
        """Set the airdate of this object. See `_update_attribute()`."""

        self._update_attribute('airdate', airdate)


    def filter_conditions(self,
            EpisodeModel: type['Episode'],
        ) -> ColumnElement[bool]:
        """
        Get the SQLAlchemy Query condition for this object.

        Args:
            EpisodeModel: Episode model to utilize for Query conditions.

        Returns:
            Query condition for this object. This is a complex condition
            for at least two non-null ID matches OR an index match (e.g.
            season+episode number) and either an airdate, title, or
            single-ID match.
        """

        # Conditions to filter by database ID
        id_conditions: list[ColumnElement[bool]] = []
        if self.emby_id:
            id_conditions.append(func.regex_match(
                fr'(?:^|\D){self.emby_id}(?!\d)', EpisodeModel.emby_id,
            ))
        if self.imdb_id is not None:
            id_conditions.append(EpisodeModel.imdb_id==self.imdb_id)
        if self.jellyfin_id:
            id_conditions.append(func.regex_match(
                fr'(?:^|\D){self.jellyfin_id}(?!\d)', EpisodeModel.jellyfin_id,
            ))
        if self.tmdb_id is not None:
            id_conditions.append(EpisodeModel.tmdb_id==self.tmdb_id)
        if self.tvdb_id is not None:
            id_conditions.append(EpisodeModel.tvdb_id==self.tvdb_id)
        if self.tvrage_id is not None:
            id_conditions.append(EpisodeModel.tvrage_id==self.tvrage_id)

        # If >1 ID condition is present, require any two ID match to
        # prevent failed matches caused by single ID collision
        expressions: list[ColumnElement[bool]] = []
        if len(id_conditions) >= 2:
            for i, condition in enumerate(id_conditions):
                for j in range(i + 1, len(id_conditions)):
                    expressions.append(and_(condition, id_conditions[j]))

        # Airdate expression
        airdate_expression: list[ColumnElement[bool]] = []
        if self.airdate:
            airdate_expression = [and_(
                not_(EpisodeModel.airdate.is_(None)),
                func.date(EpisodeModel.airdate)==self.airdate.date()
            )]

        return or_(
            # At least two ID matches; add false() in case no expressions
            or_(sql_false(), *expressions),
            # Index match and (title match OR ID match OR airdate match)
            and_(
                EpisodeModel.season_number==self.season_number,
                EpisodeModel.episode_number==self.episode_number,
                or_(
                    # Title match
                    EpisodeModel.title==self.title,
                    # ID Match
                    *id_conditions,
                    # Airdate match
                    *airdate_expression,
                ),
            ),
        )


class WordSet(dict):
    """
    Dictionary subclass that contains keys for translated word-versions
    of numbers.
    """


    def add_numeral(self,
            label: str,
            number: int | None,
            lang: str | None = None
        ) -> None:
        """
        Add the cardinal and ordinal versions of the given number under
        the given label. For example:

        >>> word_set = WordSet()
        >>> word_set.add_numeral('season_number', 4)
        >>> print(word_set)
        {'season_number_cardinal': 'four',
         'season_number_ordinal': 'fourth'}
        >>> word_set.add_numeral('abs_number', 2, 'es')
        {'season_number_cardinal': 'four',
         'season_number_ordinal': 'fourth',
         'abs_number_cardinal_es': 'dos',
         'abs_number_ordinal_es': 'segundo'}

        Args:
            label: Label key to add the converted number under.
            number: Number to wordify and add into this object.
            lang: Optional language to wordify the object into. Appended
                to any added keys.
        """

        # If value is None, do nothing
        if number is None:
            return None

        # If a specific language was indicated, use in conversion
        if lang is not None and lang != 'en':
            # Catch exceptions caused by an unsupported language
            try:
                cardinal = num2words(number, to='cardinal', lang=lang)
                self.update({
                    f'{label}_cardinal_{lang}': cardinal,
                    f'{label}_cardinal_{lang}_title': titlecase(cardinal),
                })
            except NotImplementedError:
                pass
            try:
                ordinal = num2words(number, to='ordinal', lang=lang)
                self.update({
                    f'{label}_ordinal_{lang}': ordinal,
                    f'{label}_ordinal_{lang}_title': titlecase(ordinal),
                })
            except NotImplementedError:
                pass
        # No language indicated, convert using base language
        else:
            cardinal = num2words(number, to='cardinal')
            ordinal = num2words(number, to='ordinal')
            self.update({
                f'{label}_cardinal': cardinal,
                f'{label}_cardinal_title': f'{titlecase(cardinal)}',
                f'{label}_ordinal': ordinal,
                f'{label}_ordinal_title': titlecase(ordinal),
            })

        return None


    def has_number(self, label: str, lang: str | None = None) -> bool:
        """
        Whether this object has defined translations for the given label
        and language combination.

        Args:
            label: Label key of the converted numbers.
            lang: Language of the converted numbers.

        Returns:
            True if the cardinal and ordinal translations are defined
            for this label and language; False otherwise.
        """

        if lang is not None and lang != 'en':
            return (
                f'{label}_cardinal_{lang}' in self
                and f'{label}_ordinal_{lang}' in self
            )

        return f'{label}_cardinal' in self and f'{label}_ordinal' in self
