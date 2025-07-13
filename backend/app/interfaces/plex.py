from datetime import datetime, timedelta
from os import environ
from pathlib import Path
from re import IGNORECASE, compile as re_compile
from sys import exit as sys_exit
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
    NamedTuple,
    Union,
    cast
)

from fastapi import HTTPException
from PIL import Image
from plexapi.exceptions import PlexApiException
from plexapi.library import LibrarySection as PlexLibrary
from plexapi.video import Episode as PlexEpisode, Season as PlexSeason
from plexapi.server import PlexServer, NotFound, Unauthorized
from plexapi.video import Show as PlexShow
from requests.exceptions import (
    ConnectionError as PlexConnectionError,
    ReadTimeout,
)
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential
from tinydb import where
from tqdm import tqdm

from app.interfaces.base import (
    EpisodeDataSource,
    EpisodeDataSourceV1,
    Interface,
    MediaServer,
    MediaServerV1,
    SearchResult,
    SourceImage,
    SyncInterface,
    WatchedStatus,
)
from app.info.episode import EpisodeInfo, EpisodeInfoV1
from app.info.series import SeriesInfo, SeriesInfoV1
from app.interfaces.web import WebInterface
from app.settings import TQDM_KWARGS
from app.yaml.season_posters import SeasonPosterSet
from app.logging.logger import Logger, log
from modules.Episode import Episode
from modules.PersistentDatabase import PersistentDatabase
from modules.StyleSet import StyleSet

if TYPE_CHECKING:
    from app.models.card import Card
    from app.models.episode import Episode


class EpisodeDetails(NamedTuple): # pylint: disable=missing-class-docstring
    series_info: SeriesInfo
    episode_info: EpisodeInfo
    watched_status: WatchedStatus


def catch_and_log(
        message: str,
        *,
        default: Any = None,
    ) -> Callable:
    """
    Return a decorator that logs (with the given log function) the
    given message if the decorated function raises an uncaught
    PlexApiException.

    Args:
        message: Message to log upon uncaught exception.
        default: Value to return if decorated function raises
            an uncaught exception.

    Returns:
        Wrapped decorator that returns a wrapped callable.
    """

    def decorator(function: Callable) -> Callable:
        def inner(*args, **kwargs):
            # Get contextual logger if provided as argument to function
            if ('log' in kwargs
                and hasattr(kwargs['log'], 'exception')
                and callable(kwargs['log'].exception)):
                clog = kwargs['log']
            else:
                clog = log

            try:
                return function(*args, **kwargs)
            except PlexApiException:
                clog.exception(message)
                return default
            except (ReadTimeout, PlexConnectionError) as exc:
                clog.exception('Plex API has timed out, DB might be busy')
                raise exc
            except Exception as exc:
                clog.exception('Uncaught exception')
                raise exc
        return inner
    return decorator


class PlexInterface(MediaServer, EpisodeDataSource, SyncInterface, Interface):
    """
    An interface to Plex. This allows loading assets, querying series
    and episode data, along with other attributes
    """

    INTERFACE_TYPE = 'Plex'

    """Series ID's that can be set by TMDb"""
    SERIES_IDS = ('imdb_id', 'tmdb_id', 'tvdb_id') # type: ignore

    """EXIF data to write to images if Kometa integration is enabled"""
    EXIF_TAG = {'key': 0x4242, 'data': 'titlecard'}

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)


    def __init__(self,
            url: str,
            api_key: str = 'NA',
            use_ssl: bool = True,
            integrate_with_kometa: bool = False,
            filesize_limit: int = 10485760,
            *,
            interface_id: int = 0,
            log: Logger = log,
        ) -> None:
        """
        Constructs a new instance of a Plex Interface.

        Args:
            url: URL of plex server.
            api_key: X-Plex Token for sending API requests to Plex.
            use_ssl: Whether to use SSL in all requests.
            integrate_with_kometa: Whether to integrate with Kometa in
                image uploads.
            filesize_limit: Number of bytes to limit a single file to
                during upload.
            interface_id: ID of this interface.
            log: Logger for all log messages.
        """

        super().__init__(filesize_limit)

        # Create Session for caching HTTP responses
        self._interface_id = interface_id
        self.__session = WebInterface('Plex', use_ssl, log=log).session

        # Create PlexServer object with these arguments
        try:
            self.__token = api_key
            self.__server = PlexServer(url, api_key, self.__session)
        except Unauthorized as exc:
            log.critical('Invalid Plex Token')
            raise HTTPException(
                status_code=401,
                detail='Invalid Plex Token',
            ) from exc
        except Exception as exc:
            log.exception('Cannot connect to Plex')
            raise HTTPException(
                status_code=400,
                detail=f'Cannot connect to Plex - {exc}',
            ) from exc

        # Store integration
        self.integrate_with_kometa = integrate_with_kometa
        self.activate()


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           reraise=True)
    def __get_library(self,
            library_name: str,
            *,
            log: Logger = log,
        ) -> PlexLibrary | None:
        """
        Get the Library object under the given name.

        Args:
            library_name: The name of the library to get.
            log: Logger for all log messages.

        Returns:
            The Library object if found, None otherwise.
        """

        try:
            return self.__server.library.section(library_name)
        except NotFound:
            log.error(f'Library "{library_name}" was not found in Plex')
            return None


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           reraise=True)
    def __get_series(self,
            library: PlexLibrary,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> PlexShow | None:
        """
        Get the Series object from within the given Library associated
        with the given SeriesInfo. This tries to match by TVDb ID,
        TMDb ID, name, and finally full name.

        Args:
            library: The Library object to search for within Plex.
            series_info: Series to get the episodes of.
            log: Logger for all log messages.

        Returns:
            The series associated with this SeriesInfo object.
        """

        # Try by IMDb ID
        if series_info.has_id('imdb_id'):
            try:
                return library.getGuid(f'imdb://{series_info.imdb_id}')
            except NotFound:
                pass

        # Try by TVDb ID
        if series_info.has_id('tvdb_id'):
            try:
                return library.getGuid(f'tvdb://{series_info.tvdb_id}')
            except NotFound:
                pass

        # Try by TMDb ID
        if series_info.has_id('tmdb_id'):
            try:
                return library.getGuid(f'tmdb://{series_info.tmdb_id}')
            except NotFound:
                pass

        # Try by name
        try:
            results: list[PlexShow] = library.search(
                title=series_info.name, year=series_info.year, libtype='show'
            )
            for series in results:
                if series_info.matches(series.title):
                    return series
        except NotFound:
            pass

        # Not found, return None
        log.warning(f'Series "{series_info}" was not found under '
                    f'library "{library.title}" in Plex')
        return None


    @catch_and_log('Error getting library paths', default={})
    def get_library_paths(self,
            filter_libraries: list[str] = []
        ) -> dict[str, list[str]]:
        """
        Get all libraries and their associated base directories.

        Args:
            filter_libraries: List of library names to filter the return
                by.

        Returns:
            Dictionary whose keys are the library names, and whose
            values are the list of paths to that library's base
            directories.
        """

        # Go through every library in this server
        all_libraries = {}
        for library in self.__server.library.sections():
            # Skip non-TV libraries
            if library.type != 'show':
                continue

            # If filtering, skip unspecified libraries
            if (len(filter_libraries) > 0
                and library.title not in filter_libraries):
                continue

            # Add library's paths to the dictionary under the library
            all_libraries[library.title] = library.locations

        return all_libraries


    @catch_and_log('Error getting all series', default=[])
    def get_all_series(self,
            required_libraries: list[str] = [],
            excluded_libraries: list[str] = [],
            required_tags: list[str] = [],
            excluded_tags: list[str] = [],
            *,
            log: Logger = log,
        ) -> list[tuple[SeriesInfo, str]]:
        """
        Get all series within Plex, as filtered by the given arguments.

        Args:
            required_libraries: Library names that a series must be
                present in to be returned.
            excluded_libraries: Library names that a series cannot be
                present in to be returned.
            required_tags: Tags that a series must have all of in order
                to be returned.
            excluded_tags: Tags that a series cannot have any of in
                order to be returned.
            log: Logger for all log messages.

        Returns:
            List of tuples of the filtered series info and their
            corresponding library names.
        """

        # Temporarily override request timeout to 240s (4 min)
        self.REQUEST_TIMEOUT = 240

        # Go through every library in this server
        all_series = []
        for library in self.__server.library.sections():
            # Skip non-TV libraries
            if library.type != 'show':
                continue

            # If filtering libraries, skip library if unspecified
            if ((required_libraries and library.title not in required_libraries)
                or (excluded_libraries and library.title in excluded_libraries)):
                continue

            # Get all Shows in this library
            for show in library.all():
                # Skip show if tags provided and does not match
                if required_tags or excluded_tags:
                    tags = [label.tag.lower() for label in show.labels]
                    if (required_tags
                        and not all(t.lower() in tags for t in required_tags)):
                        continue
                    if (excluded_tags
                        and any(t.lower() in tags for t in excluded_tags)):
                        continue

                # Skip show if it has no year
                if show.year is None:
                    log.warning(f'Series {show.title} has no year - skipping')
                    continue

                # Create SeriesInfo object for this show, add to return
                series_info = SeriesInfo.from_plex_show(show)
                all_series.append((series_info, library.title))

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


    @catch_and_log('Error getting all episodes', default=[])
    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
        """
        Gets all episode info for the given series. Only episodes that
        have  already aired are returned.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.
            log: Logger for all log messages.

        Returns:
            List of tuples of the EpisodeInfos and that episode's
            corresponding watched status for this series.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return []

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return []

        # Create list of all episodes in Plex
        all_episodes = []
        epq = series.episodes(container_size=500, params={'includeGuids': 1})
        for plex_episode in epq:
            # Skip if episode has no season or episode number
            plex_episode = cast(PlexEpisode, plex_episode)
            if (plex_episode.parentIndex is None
                or plex_episode.index is None):
                log.warning(
                    f'Episode {plex_episode} of {series_info} in '
                    f'"{library_name}" has no index - skipping'
                )
                continue

            # Skip temp titles if title matching and within 2 days of airing
            airdate = plex_episode.originallyAvailableAt
            if (not series_info.match_titles
                and airdate is not None
                and self.__TEMP_IGNORE_REGEX.match(plex_episode.title)
                and airdate + timedelta(days=2) > datetime.now()):
                log.debug(
                    f'Temporarily ignoring {plex_episode.seasonEpisode.upper()}'
                    f' of {series_info} - placeholder title'
                )
                continue

            # Create a new EpisodeInfo, add to list
            episode_info = EpisodeInfo.from_plex_episode(
                plex_episode,
                self._interface_id,
                library_name,
            )
            all_episodes.append((
                episode_info,
                WatchedStatus(
                    self._interface_id,
                    library_name,
                    plex_episode.isWatched,
                ),
            ))

        return all_episodes


    @catch_and_log('Error updating watched statuses', default=False)
    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episodes: list['Episode'],
            *,
            log: Logger = log,
        ) -> bool:
        """
        Modify the Episodes' watched attribute according to the watched
        status of the corresponding episodes within Plex.

        Args:
            library_name: The name of the library containing the Series.
            series_info: The Series to update.
            episodes: List of Episode objects to update.
            log: Logger for all log messages.

        Returns:
            Whether any Episode's watched statuses were modified.
        """

        # If no episodes, exit
        if not episodes:
            return False

        # If the given library cannot be found, exit
        if (library := self.__get_library(library_name, log=log)) is None:
            log.warning(f'Cannot find library "{library_name}" of {series_info}')
            return False

        # If the given series cannot be found in this library, exit
        if (series := self.__get_series(library, series_info, log=log)) is None:
            log.warning(f'Cannot find {series_info} in library "{library}"')
            return False

        # Get data for each Plex episode
        plex_episodes = [
            (
                EpisodeInfo.from_plex_episode(
                    episode,
                    self._interface_id,
                    library_name,
                ),
                WatchedStatus(
                    self._interface_id, library_name, episode.isWatched,
                )
            )
            for episode in cast(
                list[PlexEpisode],
                series.episodes(container_size=500, params={'includeGuids': 1})
            )
            if episode.parentIndex is not None and episode.index is not None
        ]

        # Update watched statuses of all Episodes
        changed = False
        for episode in episodes:
            episode_info = episode.as_episode_info
            for plex_episode, watched_status in plex_episodes:
                if episode_info == plex_episode:
                    changed |= episode.add_watched_status(
                        watched_status, log=log,
                    )
                    break

        return changed


    @catch_and_log("Error setting series ID's")
    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all possible series ID's for the given SeriesInfo object.

        Args:
            library_name: The name of the library containing the series.
            series_info: SeriesInfo to update.
            log: Logger for all log messages.
        """

        # If all possible ID's are defined
        if series_info.has_ids(*self.SERIES_IDS):
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return None

        # Set series ID's of all provided GUIDs
        for guid in series.guids:
            if 'imdb://' in guid.id:
                series_info.set_imdb_id(guid.id[len('imdb://'):])
            elif 'tmdb://' in guid.id:
                series_info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
            elif 'tvdb://' in guid.id:
                series_info.set_tvdb_id(int(guid.id[len('tvdb://'):]))

        return None


    @catch_and_log("Error setting episode ID's")
    def set_episode_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo objects. This
        sets the Sonarr and TVDb ID's for each episode. As a byproduct, this
        also updates the series ID's for the SeriesInfo object

        Args:
            library_name: Name of the library the series is under.
            series_info: SeriesInfo for the entry.
            infos: List of EpisodeInfo objects to update.
            log: Logger for all log messages.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return None

        # Filter EpisodeInfo's with all ID's
        filtered_episode_infos = {
            episode_info.key: episode_info
            for episode_info in episode_infos
            if not episode_info.has_ids(*self.SERIES_IDS)
        }

        # Go through all of this Series' Episodes
        epq = series.episodes(container_size=500, params={'includeGuids': 1})
        for plex_episode in epq:
            # Skip Plex episodes without indices
            plex_episode = cast(PlexEpisode, plex_episode)
            if (plex_episode.seasonNumber is None
                or plex_episode.episodeNumber is None):
                log.debug(f'Skipping {plex_episode} - no season/episode number')
                continue

            # Find matching EpisodeInfo, skip if not found
            episode_info = filtered_episode_infos.get(
                f's{plex_episode.seasonNumber}e{plex_episode.episodeNumber}'
            )
            if episode_info is None:
                continue

            # Set the ID's for this object
            for guid in plex_episode.guids:
                if 'imdb://' in guid.id:
                    episode_info.set_imdb_id(guid.id[len('imdb://'):])
                elif 'tmdb://' in guid.id:
                    episode_info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
                elif 'tvdb://' in guid.id:
                    episode_info.set_tvdb_id(int(guid.id[len('tvdb://'):]))

        return None


    @catch_and_log('Error querying for Series')
    def query_series(self,
            query: str,
            *,
            return_all: bool = False,
            log: Logger = log,
        ) -> list[SearchResult]:
        """
        Search Plex for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            return_all: Whether to return all Series, instead of those
                returned by the given query.
            log: Logger for all log messages.

        Returns:
            List of SearchResults for the given query. Results are from
            any library. All returned poster URL's utilize the Plex
            proxy API endpoint to obfuscate this Server's token.
        """

        if return_all:
            results = cast(
                list[PlexShow],
                [
                    show
                    for library in self.__server.library.sections()
                    for show in library.all()
                    if library.type == 'show' and show.year is not None
                ]
            )
        else:
            # Search Plex for this query
            results = cast(
                list[PlexShow],
                self.__server.search(query, mediatype='show', limit=50)
            )

        def parse_ids(show: PlexShow) -> dict:
            """
            Parse any database IDs from the given object.

            Args:
                show: Show object whose GUIDs are being parsed.

            Returns:
                Dictionary of DB ID's. Each ID is set, or None.
            """

            ids = {'imdb_id': None, 'tmdb_id': None, 'tvdb_id': None}
            for guid in show.guids:
                if 'imdb://' in guid.id:
                    ids['imdb_id'] = guid.id[len('imdb://'):]
                elif 'tmdb://' in guid.id:
                    ids['tmdb_id'] = int(guid.id[len('tmdb://'):])
                elif 'tvdb://' in guid.id:
                    ids['tvdb_id'] = int(guid.id[len('tvdb://'):])
            return ids

        # Return results, use proxy endpoint for poster URL
        return [
            SearchResult(
                name=result.title,
                year=result.year, # type: ignore
                poster=f'/api/v2/proxy/plex?url={result.thumb}&interface_id={self._interface_id}',
                overview=result.summary,
                **parse_ids(result),
            ) for result in results
        ]


    @catch_and_log('Error getting source image')
    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            proxy_url: bool = False,
            log: Logger = log,
        ) -> str | None:
        """
        Get the source image for the given episode within Plex.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the source image of.
            episode_info: The episode to get the source image of.
            proxy_url: Whether to proxy the returned URL.
            log: Logger for all log messages.

        Returns:
            URL to the thumbnail of the given Episode. None if the
            episode DNE or otherwise has no source image.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return None

        # Labels that will result in source skip
        bad_labels = ('Overlay', 'TCM') if self.integrate_with_kometa else ('TCM',)

        # Get Episode from within Plex
        try:
            plex_episode: PlexEpisode = series.episode( # type: ignore
                season=episode_info.season_number,
                episode=episode_info.episode_number
            )
        # Episode DNE in Plex, return
        except NotFound:
            return None

        # Verify this Episode does not have the Kometa overlay label
        if any(label.tag in bad_labels for label in plex_episode.labels):
            log.debug(
                f'{series_info} {episode_info} Cannot use Plex thumbnail, has '
                f'existing Overlay or Title Card'
            )
            return None

        # Check that the Episode's thumbnail is valid
        if not plex_episode.thumb:
            log.warning(
                f'{series_info} {episode_info} cannot use Plex image, this '
                'episode does not have a valid thumbnail'
            )
            return None

        # If proxying, use API redirect URL; token will be embedded by endpoint
        if proxy_url:
            return (
                f'/api/v2/proxy/plex?url={plex_episode.thumb}'
                f'&interface_id={self._interface_id}'
            )

        # pylint: disable=protected-access
        return (
            f'{self.__server._baseurl}/{plex_episode.thumb}'
            f'?X-Plex-Token={self.__token}'
        )


    @catch_and_log('Error getting Series poster')
    def get_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> SourceImage:
        """
        Get the poster for the given Series.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the poster of.
            log: Logger for all log messages.

        Returns:
            URL to the poster for the given series. None if the library,
            series, or thumbnail cannot be found.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return None

        return series.thumbUrl


    @catch_and_log('Error getting library names', default=[])
    def get_libraries(self) -> list[str]:
        """
        Get the names of all libraries within this server.

        Returns:
            List of library names.
        """

        return [
            library.title
            for library in self.__server.library.sections()
            if library.type == 'show'
        ]


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           before_sleep=lambda _:log.warning('Cannot upload image, retrying..'),
           reraise=True)
    def __retry_upload(self,
            entry: PlexShow | PlexSeason | PlexEpisode,
            image: str | Path,
            kind: Literal['art', 'poster'] = 'poster',
            *,
            log: Logger = log,
        ) -> None:
        """
        Upload the given image to the given entry, retrying if it fails.

        Args:
            entry: The plexapi object to upload the file to.
            image: URL or Path to the file to upload.
            kind: The kind of asset the given image is. This will
                affect what kind of upload functin to call.
            log: Logger for all log messages.
        """

        # Upload image as URL or file
        kwargs = {'url' if isinstance(image, str) else 'filepath': image}
        if kind == 'art':
            entry.uploadArt(**kwargs)
        else:
            entry.uploadPoster(**kwargs)


    def __add_exif_tag(self, image: Path, *, log: Logger = log) -> None:
        """
        Add an EXIF tag to the given image file. This adds "titlecard"
        at 0x4242, and overwrites the existing file.

        Args:
            image: Path to the Card file to modify.
            log: Logger for all log messages.
        """

        # Create Image object, read EXIF data
        card_image = Image.open(image)
        exif = card_image.getexif()

        # Add EXIF data
        exif[self.EXIF_TAG['key']] = self.EXIF_TAG['data']

        # Try and write explicitly; if an error OSError is raised then
        # that implies image has an alpha channel that is not supported
        # by file extension - convert and try again
        try:
            card_image.save(image.resolve(), exif=exif)
        except OSError:
            card_image.convert('RGB').save(image.resolve(), exif=exif)

        log.trace(f'Added EXIF data {self.EXIF_TAG} to {image}')


    @catch_and_log('Error uploading title cards', default=[])
    def load_title_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_and_cards: Union[
                list[tuple['Episode', 'Card']],
                list[tuple['Episode', 'Card', int]],
            ],
            *,
            log: Logger = log,
        ) -> list[tuple['Episode', 'Card']]:
        """
        Load the title cards for the given Series and Episodes.

        Args:
            library_name: Name of the library containing the series.
            series_info: SeriesInfo whose cards are being loaded.
            episode_and_cards: List of tuple of Episode and their
                corresponding Card objects to load. Each tuple may
                optionally include a UID to force load that Card into.
            log: Logger for all log messages.
        """

        # No episodes to load, exit
        if not episode_and_cards:
            log.trace(f'No episodes to load for {series_info}')
            return []

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name, log=log)):
            return []

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info, log=log)):
            return []

        # Find episodes which have a matching Card to load
        matched_episodes: list[tuple[PlexEpisode, 'Episode', 'Card']] = []
        matched_indices: set[int] = set()

        # An UID (RatingKey) was provided, match directly
        if len(episode_and_cards[0]) == 3:
            for index, (episode, card, uid) in enumerate(episode_and_cards): # type: ignore
                if (plex_ep := self.__server.fetchItem(int(uid))) is None:
                    log.warning(f'No Episode associated with Key {int(uid)}')
                    continue
                matched_episodes.append((plex_ep, episode, card))
                matched_indices.add(index)
        # No UID provided, find by iterating through all episodes of show
        else:
            # Generate EpisodeInfo of the given Episodes/Cards ahead of time
            # to avoid re-constructing the EpisodeInfo object for each episode
            infos = [
                (episode, episode.as_episode_info, card)
                for episode, card, *_ in episode_and_cards
            ]

            for plex_episode in cast(list[PlexEpisode], series.episodes(
                    container_size=100,
                    params={'includeGuids': 1},
                )):
                # Exit if all episodes have been matched
                if len(matched_episodes) == len(infos):
                    break

                for index, (episode, episode_info, card) in enumerate(infos):
                    if episode_info == plex_episode:
                        matched_episodes.append((plex_episode, episode, card))
                        matched_indices.add(index)
                        break

        # Log all unmatched Episodes
        for index, (episode, *_) in enumerate(episode_and_cards):
            if index not in matched_indices:
                log.warning(f'Unable to find associated Episode for {episode}')

        # No Episodes were found in Plex, exit
        if not matched_episodes:
            log.trace(f'Not loading any Cards for {series_info}')
            return []

        # Prepare batch edits on all these episodes
        library.batchMultiEdits([ep[0] for ep in matched_episodes])
        if self.integrate_with_kometa:
            library.removeLabel(['Overlay'])
            log.trace(
                f'Removed "Overlay" label from {len(matched_episodes)} episodes'
            )
        library.addLabel(['TCM'])

        # Upload card for all matched episodes
        loaded: list[tuple['Episode', 'Card']] = []
        for plex_episode, episode, card in matched_episodes:
            # Shrink image if necesssary, skipping if uncompressable
            if (image := self.compress_image(card.card_file, log=log)) is None:
                continue

            # Upload card
            try:
                # If integrating with Kometa, add EXIF data
                if self.integrate_with_kometa:
                    self.__add_exif_tag(image, log=log)

                # Upload card
                self.__retry_upload(plex_episode, image.resolve(), log=log)
                log.debug(
                    f'{series_info} {plex_episode.seasonEpisode} loaded Card '
                    f'"{image.name}" into "{library_name}"'
                )
            except Exception:
                log.exception(
                    f'Unable to upload {image.resolve()} to {series_info}'
                )
                continue
            else:
                loaded.append((episode, card))

        # Save batch edits
        library.saveMultiEdits()

        return loaded


    @catch_and_log('Error uploading season posters')
    def load_season_posters(self,
            library_name: str,
            series_info: SeriesInfo,
            posters: dict[int, str | Path],
            *,
            log: Logger = log,
        ) -> None:
        """
        Load the given season posters into Plex.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            posters: Dictionary of season numbers to poster URLs or
                files to upload.
            log: Logger for all log messages.
        """

        if (not posters
            or not (library := self.__get_library(library_name))
            or not (series := self.__get_series(library, series_info))):
            return None

        for season in series.seasons():
            season = cast(PlexSeason, season)
            # Skip if there is no poster for this season
            if not (poster := posters.get(season.index)):
                continue

            # Shrink image if necessary
            if (isinstance(poster, Path)
                and (poster := self.compress_image(poster)) is None):
                continue

            # Upload this poster
            try:
                # If integrating with Kometa, add EXIF data
                if isinstance(poster, Path) and self.integrate_with_kometa:
                    self.__add_exif_tag(poster)

                # Upload poster
                self.__retry_upload(season, poster, log=log)

                # If integrating with Kometa, remove label
                if self.integrate_with_kometa:
                    season.removeLabel(['Overlay'])
                    log.trace(f'Removed "Overlay" label from {season}')
                log.debug(
                    f'{series_info} loaded poster into season {season.index}'
                )
            except Exception:
                log.exception(
                    f'Failed to upload {poster} to season {season.index}'
                )
                continue

        return None


    @catch_and_log('Error loading the series poster')
    def load_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
            image: str | Path,
            *,
            log: Logger = log
        ) -> None:
        """
        Load the given series poster into Plex.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            image: URL or Path to the file to upload.
            log: Logger for all log messages.
        """

        if (not (library := self.__get_library(library_name))
            or not (series := self.__get_series(library, series_info))):
            return None

        # Shrink image if necessary
        if (isinstance(image, Path)
            and (image := self.compress_image(image)) is None):
            return None

        # Upload this poster
        try:
            # If integrating with Kometa, add EXIF data
            if isinstance(image, Path) and self.integrate_with_kometa:
                self.__add_exif_tag(image)

            # Upload poster
            self.__retry_upload(series, image, log=log)

            # If integrating with Kometa, remove label
            if self.integrate_with_kometa:
                series.removeLabel(['Overlay'])
                log.trace(f'Removed "Overlay" label from {series}')
            log.debug(f'{series_info} loaded poster')
        except Exception:
            log.exception(f'Failed to upload "{image}" to {series_info}')

        return None


    @catch_and_log('Error loading series background')
    def load_series_background(self,
            library_name: str,
            series_info: SeriesInfo,
            image: str | Path,
            *,
            log: Logger = log
        ) -> None:
        """
        Load the given series background image into Plex.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            image: URL or Path to the file to upload.
            log: Logger for all log messages.
        """

        if (not (library := self.__get_library(library_name))
            or not (series := self.__get_series(library, series_info))):
            return None

        # Shrink image if necessary
        if (isinstance(image, Path)
            and (image := self.compress_image(image)) is None):
            return None

        # Upload this poster
        try:
            # If integrating with Kometa, add EXIF data
            if isinstance(image, Path) and self.integrate_with_kometa:
                self.__add_exif_tag(image)

            # Upload poster
            self.__retry_upload(series, image, kind='art', log=log)

            # If integrating with Kometa, remove label
            if self.integrate_with_kometa:
                series.removeLabel(['Overlay'])
                log.trace(f'Removed "Overlay" label from {series}')
            log.debug(f'{series_info} loaded background')
        except Exception:
            log.exception(f'Failed to upload "{image}" to {series_info}')

        return None


    @catch_and_log('Error getting rating key details')
    def get_episode_details(self,
            rating_key: int,
            *,
            log: Logger = log,
        ) -> list[EpisodeDetails]:
        """
        Get all details for all episodes indicated by the given Plex
        rating key.

        Args:
            rating_key: Rating key used to fetch the item within Plex.
            log: Logger for all log messages.

        Returns:
            List of tuples of the SeriesInfo, EpisodeInfo, and the watch
            status corresponding to the given rating key. If the object
            associated with the rating key is a show or season, then all
            contained episodes are detailed. An empty list is returned
            if the item(s) associated with the given key cannot be
            found.
        """

        try:
            # Get the entry for this key
            if (entry := self.__server.fetchItem(rating_key)) is None:
                raise NotFound

            # Show, return all episodes in series
            if entry.type == 'show':
                entry = cast(PlexShow, entry) # type: ignore
                series_info = SeriesInfo.from_plex_show(entry)
                return [
                    EpisodeDetails(
                        series_info,
                        EpisodeInfo.from_plex_episode(
                            ep,
                            self._interface_id,
                            entry.librarySectionTitle,
                        ),
                        WatchedStatus(
                            self._interface_id,
                            entry.librarySectionTitle,
                            ep.isWatched,
                        )
                    )
                    for ep in cast(list[PlexEpisode], entry.episodes())
                ]

            # Season, return all episodes in season
            if entry.type == 'season':
                entry = cast(PlexSeason, entry) # type: ignore
                series = cast(
                    PlexShow,
                    self.__server.fetchItem(entry.parentRatingKey)
                )
                series_info = SeriesInfo.from_plex_show(series)
                return [
                    EpisodeDetails(
                        series_info,
                        EpisodeInfo.from_plex_episode(
                            ep,
                            self._interface_id,
                            entry.librarySectionTitle,
                        ),
                        WatchedStatus(
                            self._interface_id,
                            entry.librarySectionTitle,
                            ep.isWatched,
                        ),
                    )
                    for ep in cast(list[PlexEpisode], entry.episodes())
                ]

            # Episode, return just that
            if entry.type == 'episode':
                entry = cast(PlexEpisode, entry)
                series: PlexShow = self.__server.fetchItem( # type: ignore
                    entry.grandparentRatingKey
                )
                series_info = SeriesInfo.from_plex_show(series)
                return [
                    EpisodeDetails(
                        series_info,
                        EpisodeInfo.from_plex_episode(
                            entry,
                            self._interface_id,
                            entry.librarySectionTitle,
                        ),
                        WatchedStatus(
                            self._interface_id,
                            entry.librarySectionTitle,
                            entry.isWatched,
                        ),
                    )
                ]

            log.debug(f'Item with rating key {rating_key} has no episodes')
            return []
        except NotFound:
            log.warning(f'No item with rating key {rating_key} exists')
        except (ValueError, AssertionError):
            log.warning(f'Item with rating key {rating_key} has no year')
        except Exception:
            log.exception(f'Rating key {rating_key} has some error')

        # Error occurred, return empty list
        return []


    @catch_and_log('Error removing Series labels')
    def remove_series_labels(self,
            library_name: str,
            series_info: SeriesInfo,
            labels: list[str] = ['TCM', 'Overlay'],
            *,
            log: Logger = log,
        ) -> None:
        """
        Remove the given labels from all Episodes of the associated
        Series.

        Args:
            library_name: Name of the library containing the series.
            series_info: SeriesInfo whose Episodes' labels are being
                removed.
            labels: List of labels to remove.
            log: Logger for all log messages.
        """

        # Exit if no labels were provided or the library/series is not found
        if (not labels
            or not (library := self.__get_library(library_name, log=log))
            or not (series := self.__get_series(library, series_info, log=log))):
            return None

        # Get all Episodes for batch edits
        episodes = cast(list[PlexEpisode], series.episodes(container_size=500))
        library.batchMultiEdits(episodes)
        library.removeLabel(labels)

        # Finalize batch edits
        library.saveMultiEdits()

        return None


class PlexInterfaceV1(EpisodeDataSourceV1, MediaServerV1, SyncInterface):
    """This class describes an interface to Plex."""

    """Series ID's that can be set by TMDb"""
    SERIES_IDS = ('imdb_id', 'tmdb_id', 'tvdb_id')

    """Filepath to the database of each episode's loaded card characteristics"""
    LOADED_DB = 'loaded.json'

    """Filepath to the database of the loaded season poster characteristics"""
    LOADED_POSTERS_DB = 'loaded_posters.json'

    """How many failed episodes result in skipping a series"""
    SKIP_SERIES_THRESHOLD = 3

    """EXIF data to write to images if Kometa integration is enabled"""
    EXIF_TAG = {'key': 0x4242, 'data': 'titlecard'}

    """How many seconds to allow for a single transaction"""
    DEFAULT_TIMEOUT = 30 # seconds

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)


    def __init__(self,
            url: str,
            x_plex_token: str = 'NA',
            verify_ssl: bool = True,
            integrate_with_kometa: bool = False,
            filesize_limit: int = 10485760,
            timeout: int = DEFAULT_TIMEOUT,
        ) -> None:
        """
        Constructs a new instance of a Plex Interface.

        Args:
            url: URL of plex server.
            x_plex_token: X-Plex Token for sending API requests to Plex.
            verify_ssl: Whether to verify SSL requests when querying
                Plex.
            integrate_with_kometa: Whether to integrate with Kometa
                in image uploads.
            filesize_limit: Number of bytes to limit a single file to
                during upload.
            timeout: How many seconds to allow for a timeout.

        Raises:
            SystemExit: An Exception is raised while connecting to Plex.
        """

        super().__init__(filesize_limit)

        # Get global MediaInfoSet objects
        self.info_set = global_objects.info_set

        # Create Session for caching HTTP responses
        self.__session = WebInterface('Plex', verify_ssl).session

        # Create PlexServer object with these arguments
        try:
            self.__token = x_plex_token
            self.__server = PlexServer(
                url, x_plex_token, self.__session, timeout
            )
        except Unauthorized:
            log.critical(f'Invalid Plex Token "{x_plex_token}"')
            sys_exit(1)
        except Exception as exc:
            log.critical(f'Cannot connect to Plex - returned error: "{exc}"')
            sys_exit(1)

        # Adjust timeout for PlexServer object and environment variable
        environ['PLEXAPI_PLEXAPI_TIMEOUT'] = str(timeout)

        # Store integration
        self.integrate_with_kometa = integrate_with_kometa

        # Create/read loaded card database
        self.__posters = PersistentDatabase(self.LOADED_POSTERS_DB)

        # List of "not found" warned series
        self.__warned = set()


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           reraise=True)
    def __get_library(self, library_name: str) -> PlexLibrary | None:
        """
        Get the Library object under the given name.

        Args:
            library_name: The name of the library to get.

        Returns:
            The Library object if found, None otherwise.
        """

        try:
            return self.__server.library.section(library_name)
        except NotFound:
            log.error(f'Library "{library_name}" was not found in Plex')
            return None


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3)+wait_exponential(min=1, max=32),
           reraise=True)
    def __get_series(self,
            library: PlexLibrary,
            series_info: SeriesInfoV1) -> PlexShow | None:
        """
        Get the Series object from within the given Library associated
        with the given SeriesInfo. This tries to match by TVDb ID,
        TMDb ID, name, and finally name.

        Args:
            library: The Library object to search for within Plex.
            series_info: Series to get the episodes of.

        Returns:
            The Series associated with this SeriesInfo object.
        """

        # Try by IMDb ID
        if series_info.has_id('imdb_id'):
            try:
                return library.getGuid(f'imdb://{series_info.imdb_id}')
            except NotFound:
                pass

        # Try by TVDb ID
        if series_info.has_id('tvdb_id'):
            try:
                return library.getGuid(f'tvdb://{series_info.tvdb_id}')
            except NotFound:
                pass

        # Try by TMDb ID
        if series_info.has_id('tmdb_id'):
            try:
                return library.getGuid(f'tmdb://{series_info.tmdb_id}')
            except NotFound:
                pass

        # Try by name
        try:
            results = library.search(
                title=series_info.name, year=series_info.year, libtype='show'
            )
            for series in results:
                if series_info.matches(series.title):
                    return series
        except NotFound:
            pass

        # Try by full name
        try:
            results = library.search(
                title=series_info.full_name, year=series_info.year,
                libtype='show'
            )
            for series in results:
                if series_info.matches(series.title):
                    return series
        except NotFound:
            pass

        # Not found, return None
        key = f'{library.title}-{series_info.full_name}'
        if key not in self.__warned:
            log.warning(f'Series "{series_info}" was not found under '
                        f'library "{library.title}" in Plex')
            self.__warned.add(key)

        return None

    @catch_and_log('Error getting library paths', default={})
    def get_library_paths(self,
            filter_libraries: list[str] = [],
        ) -> dict[str, list[str]]:
        """
        Get all libraries and their associated base directories.

        Args:
            filer_libraries: List of library names to filter the return
                by.

        Returns:
            Dictionary whose keys are the library names, and whose
            values are the list of paths to that library's base
            directories.
        """

        # Go through every library in this server
        all_libraries = {}
        for library in self.__server.library.sections():
            # Skip non-TV libraries
            if library.type != 'show':
                continue

            # If filtering, skip unspecified libraries
            if (len(filter_libraries) > 0
                and library.title not in filter_libraries):
                continue

            # Add library's paths to the dictionary under the library
            all_libraries[library.title] = library.locations

        return all_libraries


    @catch_and_log('Error getting all series', default=[])
    def get_all_series(self,
            filter_libraries: list[str] = [],
            required_tags: list[str] = [],
        ) -> list[tuple[SeriesInfoV1, str, str]]:
        """
        Get all series within Plex, as filtered by the given libraries.

        Args:
            filter_libraries: Optional list of library names to filter
                returned by. If provided, only series that are within a
                given library are returned.
            required_tags: Optional list of tags to filter return by. If
                provided, only series with all the given tags are
                returned.

        Returns:
            List of tuples whose elements are the SeriesInfo of the
            series, the  path (string) it is located, and its
            corresponding library name.
        """

        # Temporarily override request timeout to 240s (4 min)
        self.REQUEST_TIMEOUT = 240

        # Go through every library in this server
        all_series = []
        for library in self.__server.library.sections():
            # Skip non-TV libraries
            if library.type != 'show':
                continue

            # If filtering libraries, skip library if unspecified
            if (len(filter_libraries) > 0
                and library.title not in filter_libraries):
                continue

            # Get all Shows in this library
            for show in library.all():
                # Skip show if tags provided and does not match
                if required_tags:
                    tags = [label.tag.lower() for label in show.labels]
                    if not all(tag.lower() in tags for tag in required_tags):
                        continue

                # Skip show if it has no year
                if show.year is None:
                    log.warning(f'Series {show.title} has no year - skipping')
                    continue

                # Skip show if it has no locations.. somehow..
                if len(show.locations) == 0:
                    log.warning(f'Series {show.title} has no files - skipping')
                    continue

                # Get all ID's for this series
                ids = {}
                for guid in show.guids:
                    for id_type in ('imdb', 'tmdb', 'tvdb'):
                        if (prefix := f'{id_type}://') in guid.id:
                            ids[f'{id_type}_id'] = guid.id[len(prefix):]
                            break

                # Create SeriesInfo object for this show, add to return
                series_info = SeriesInfoV1(show.title, show.year, **ids)
                all_series.append((series_info,show.locations[0],library.title))

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


    @catch_and_log('Error getting all episodes', default=[])
    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episode_infos: list[EpisodeInfoV1] | None = None,
        ) -> list[EpisodeInfoV1]:
        """
        Gets all episode info for the given series. Only episodes that
        have already aired are returned.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.
            episode_infos: Unused argument.

        Returns:
            List of EpisodeInfo objects for this series.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return []

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return []

        # Create list of all episodes in Plex
        all_episodes = []
        for plex_episode in series.episodes():
            # Skip if episode has no season or episode number
            if (plex_episode.parentIndex is None
                or plex_episode.index is None):
                log.warning(
                    f'Episode {plex_episode} of {series_info} in '
                    f'"{library_name}" has no index - skipping'
                )
                continue

            # Skip temporary titles
            airdate = plex_episode.originallyAvailableAt
            if (airdate is not None
                and self.__TEMP_IGNORE_REGEX.match(plex_episode.title)
                and airdate + timedelta(days=2) > datetime.now()):
                log.debug(
                    f'Temporarily ignoring {plex_episode.seasonEpisode.upper()}'
                    f' of {series_info} - placeholder title'
                )
                continue

            # Get all ID's for this episode
            ids = {}
            for guid in plex_episode.guids:
                if 'tvdb://' in guid.id:
                    ids['tvdb_id'] = guid.id[len('tvdb://'):]
                elif 'imdb://' in guid.id:
                    ids['imdb_id'] = guid.id[len('imdb://'):]
                elif 'tmdb://' in guid.id:
                    ids['tmdb_id'] = guid.id[len('tmdb://'):]

            # Create either a new EpisodeInfo or get from the MediaInfoSet
            episode_info = self.info_set.get_episode_info(
                series_info,
                plex_episode.title,
                plex_episode.parentIndex,
                plex_episode.index,
                **ids,
                airdate=airdate,
                title_match=True,
                queried_plex=True,
            )

            # Add to list
            if episode_info is not None:
                all_episodes.append(episode_info)

        return all_episodes


    def has_series(self, library_name: str, series_info: SeriesInfoV1) -> bool:
        """
        Determine whether the given series is present within Plex.

        Args:
            library_name: The name of the library potentially containing
                the series.
            series_info: The series to being evaluated.

        Returns:
            True if the series is present within Plex. False otherwise.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return False

        # If the given series cannot be found in this library, exit
        return self.__get_series(library, series_info) is not None


    @catch_and_log('Error updating watched statuses')
    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episode_map: dict[str, Episode],
            style_set: StyleSet,
        ) -> None:
        """
        Modify the Episode objects according to the watched status of
        the corresponding episodes within Plex, and the spoil status of
        the object. If a loaded card needs its spoiler status changed,
        the card is deleted and the loaded map is forced to reload that
        card.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episode_map: Dictionary of episode keys to Episode objects
                to modify
            style_set: StyleSet object to update the style of the
                Episodes with.
        """

        # If no episodes, exit
        if len(episode_map) == 0:
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Get loaded characteristics of the series
        loaded_series = self.loaded_db.search(
            self._get_condition(library_name, series_info)
        )

        # Go through each episode within Plex and update Episode spoiler status
        for plex_episode in series.episodes():
            # If this Plex episode doesn't have Episode object(?) skip
            ep_key = f'{plex_episode.parentIndex}-{plex_episode.index}'
            if not (episode := episode_map.get(ep_key)):
                continue

            # Set Episode watched/spoil statuses
            episode.update_statuses(plex_episode.isWatched, style_set)

            # Get characteristics of this Episode's loaded card
            details = self._get_loaded_episode(loaded_series, episode)
            loaded = details is not None
            spoiler_status = details['spoiler'] if loaded else None

            # Delete and reset card if current spoiler type doesn't match
            delete_and_reset = (
                episode.spoil_type != spoiler_status
                and bool(spoiler_status)
            )

            # Delete card, reset size in loaded map to force reload
            if delete_and_reset and loaded:
                episode.delete_card(reason='updating style')
                self.loaded_db.update(
                    {'filesize': 0},
                    self._get_condition(library_name, series_info, episode)
                )

        return None


    @catch_and_log("Error setting series ID's")
    def set_series_ids(self,library_name: str, series_info: SeriesInfoV1) -> None:
        """
        Set all possible series ID's for the given SeriesInfo object.

        Args:
            library_name: The name of the library containing the series.
            series_info: SeriesInfo object to update.
        """

        # If all possible ID's are defined
        if series_info.has_ids(*self.SERIES_IDS):
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Set series ID's of all provided GUIDs
        for guid in series.guids:
            # No MediaInfoSet, set directly
            if self.info_set is None:
                if 'imdb://' in guid.id:
                    series_info.set_imdb_id(guid.id[len('imdb://'):])
                elif 'tmdb://' in guid.id:
                    series_info.set_tmdb_id(guid.id[len('tmdb://'):])
                elif 'tvdb://' in guid.id:
                    series_info.set_tvdb_id(guid.id[len('tvdb://'):])
            # Set using global MediaInfoSet
            else:
                if 'imdb://' in guid.id:
                    self.info_set.set_imdb_id(
                        series_info, guid.id[len('imdb://'):]
                    )
                elif 'tmdb://' in guid.id:
                    self.info_set.set_tmdb_id(
                        series_info, guid.id[len('tmdb://'):]
                    )
                elif 'tvdb://' in guid.id:
                    self.info_set.set_tvdb_id(
                        series_info, guid.id[len('tvdb://'):]
                    )

        return None


    @catch_and_log("Error setting episode ID's")
    def set_episode_ids(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episode_infos: list[EpisodeInfoV1],
            *,
            inplace: bool = True,
        ) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo
        objects. This sets the Sonarr and TVDb ID's for each episode. As
        a byproduct, this also updates the series ID's for the
        SeriesInfo object

        Args:
            library_name: Name of the library the series is under.
            series_info: SeriesInfo for the entry.
            episode_infos: List of EpisodeInfo objects to update.
            inplace: Unused argument.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Go through each provided EpisodeInfo and update the ID's
        for info in episode_infos:
            # Skip if EpisodeInfo already has all the possible ID's
            if info.queried_plex or info.has_ids(*self.SERIES_IDS):
                continue

            # Get episode from Plex
            info.queried_plex = True
            try:
                plex_episode = series.episode(
                    season=info.season_number,
                    episode=info.episode_number,
                )
            except NotFound:
                continue

            # Set the ID's for this object
            for guid in plex_episode.guids:
                if 'imdb://' in guid.id:
                    info.set_imdb_id(guid.id[len('imdb://'):])
                elif 'tmdb://' in guid.id:
                    info.set_tmdb_id(int(guid.id[len('tmdb://'):]))
                elif 'tvdb://' in guid.id:
                    info.set_tvdb_id(int(guid.id[len('tvdb://'):]))

        return None


    @catch_and_log('Error getting source image')
    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episode_info: EpisodeInfoV1,
        ) -> SourceImage:
        """
        Get the source image for the given episode within Plex.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the source image of.
            episode_info: The episode to get the source image of.

        Returns:
            URL to the thumbnail of the given Episode. None if the
            episode DNE.
        """

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Get Episode from within Plex
        try:
            plex_episode = series.episode(
                season=episode_info.season_number,
                episode=episode_info.episode_number
            )

            return (f'{self.__server._baseurl}{plex_episode.thumb}' # pylint: disable=protected-access
                    f'?X-Plex-Token={self.__token}')
        except NotFound:
            # Episode DNE in Plex, return
            return None


    @catch_and_log('Error getting library names', default=[])
    def get_libraries(self) -> list[str]:
        """
        Get the names of all libraries within this server.

        Returns:
            List of library names.
        """

        return [
            library.title
            for library in self.__server.library.sections()
            if library.type == 'show'
        ]


    @retry(stop=stop_after_attempt(5),
           wait=wait_fixed(3) + wait_exponential(min=1, max=32),
           before_sleep=lambda _:log.warning('Cannot upload image, retrying..'),
           reraise=True)
    def __retry_upload(self,
            plex_object: PlexEpisode | PlexSeason,
            filepath: Path,
        ) -> None:
        """
        Upload the given poster to the given Episode, retrying if it
        fails.

        Args:
            plex_object: The plexapi object to upload the file to.
            filepath: Filepath to the poster to upload.
        """

        plex_object.uploadPoster(filepath=filepath)


    def __add_exif_tag(self, card: Path) -> None:
        """
        Add an EXIF tag to the given Card file. This adds "titlecard" at
        0x4242, and overwrites the existing file.

        Args:
            card: Path to the Card file to modify.
        """

        # Create Image object, read EXIF data
        card_image = Image.open(card)
        exif = card_image.getexif()

        # Add EXIF data, write modified file
        exif[self.EXIF_TAG['key']] = self.EXIF_TAG['data']
        card_image.save(card.resolve(), exif=exif)


    @catch_and_log('Error uploading title cards')
    def set_title_cards(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episode_map: dict[str, Episode],
        ) -> None:
        """
        Set the title cards for the given series. This only updates
        episodes that have title cards, and those episodes whose card
        filesizes are different than what has been set previously.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            episode_map: Dictionary of episode keys to Episode objects
                to update the cards of.
        """

        # Filter episodes without cards, or whose cards have not changed
        filtered_episodes = self._filter_loaded_cards(
            library_name, series_info, episode_map
        )

        # If no episodes remain, exit
        if len(filtered_episodes) == 0:
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Go through each episode within Plex, set title cards
        error_count, loaded_count = 0, 0
        for pl_episode in (pbar := tqdm(series.episodes(), **TQDM_KWARGS)):
            pl_episode: PlexEpisode = pl_episode
            # If error count is too high, skip this series
            if error_count >= self.SKIP_SERIES_THRESHOLD:
                log.error(
                    f'Failed to upload {error_count} episodes, skipping '
                    f'"{series_info}"'
                )
                break

            # Skip episodes that aren't in list of cards to update
            ep_key = f'{pl_episode.parentIndex}-{pl_episode.index}'
            if not (episode := filtered_episodes.get(ep_key)):
                continue

            # Update progress bar
            pbar.set_description(f'Updating {pl_episode.seasonEpisode.upper()}')

            # Shrink image if necessary, skip if cannot be compressed
            if (card := self.compress_image(episode.destination)) is None:
                continue

            # Upload card to Plex
            try:
                # If integrating with Kometa, add EXIF data
                if self.integrate_with_kometa:
                    self.__add_exif_tag(card)

                # Upload card
                self.__retry_upload(pl_episode, card.resolve())

                # If integrating with Kometa, remove label
                if self.integrate_with_kometa:
                    pl_episode.removeLabel(['Overlay'])
            except Exception:
                error_count += 1
                log.exception(f'Unable to upload {card.resolve()} to '
                              f'{series_info}')
                continue
            else:
                loaded_count += 1

            # Update/add loaded map with this entry
            self.loaded_db.upsert({
                'library': library_name,
                'series': series_info.full_name,
                'season': episode.episode_info.season_number,
                'episode': episode.episode_info.episode_number,
                'filesize': episode.destination.stat().st_size,
                'spoiler': episode.spoil_type,
            }, self._get_condition(library_name, series_info, episode))

        # Log load operations to user
        if loaded_count > 0:
            log.info(f'Loaded {loaded_count} cards for "{series_info}"')

        return None


    @catch_and_log('Error uploading season posters')
    def set_season_posters(self,
            library_name: str,
            series_info: SeriesInfoV1,
            season_poster_set: SeasonPosterSet,
        ) -> None:
        """
        Set the season posters from the given set within Plex.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            season_poster_set: SeasonPosterSet with season posters to
                set.
        """

        # If no posters to upload, skip
        if not season_poster_set.has_posters:
            return None

        # If the given library cannot be found, exit
        if not (library := self.__get_library(library_name)):
            return None

        # If the given series cannot be found in this library, exit
        if not (series := self.__get_series(library, series_info)):
            return None

        # Condition for this series
        loaded_count = 0
        for season in series.seasons():
            # Skip if no season poster for this seasons
            if (poster := season_poster_set.get_poster(season.index)) is None:
                continue

            # Get the loaded details for this season
            condition = (
                (where('library') == library_name)
                & (where('series') == series_info.full_name)
                & (where('season') == season.index)
            )
            details = self.__posters.get(condition)

            # Skip if this exact poster has been loaded
            if (details is not None
                and details['filesize'] == poster.stat().st_size):
                continue

            # Shrink image if necessary
            if (resized_poster := self.compress_image(poster)) is None:
                continue

            # Upload this poster
            try:
                # If integrating with Kometa, add EXIF data
                if self.integrate_with_kometa:
                    self.__add_exif_tag(resized_poster)

                # Upload poster
                self.__retry_upload(season, resized_poster)

                # If integrating with Kometa, remove label
                if self.integrate_with_kometa:
                    season.removeLabel(['Overlay'])
            except Exception:
                continue
            else:
                loaded_count += 1

            # Update loaded database
            self.__posters.upsert({
                'library': library_name,
                'series': series_info.full_name,
                'season': season.index,
                'filesize': poster.stat().st_size,
            }, condition)

        # Log load operations to user
        if loaded_count > 0:
            log.info(f'Loaded {loaded_count} season posters for "{series_info}"')

        return None


    @catch_and_log('Error getting episode details')
    def get_episode_details(self,
            rating_key: int,
        ) -> list[tuple[SeriesInfoV1, EpisodeInfoV1, str]]:
        """
        Get all details for all episodes indicated by the given Plex
        rating key.

        Args:
            rating_key: Rating key used to fetch the item within Plex.

        Returns:
            List of tuples of the SeriesInfo, EpisodeInfo, and the
            library name corresponding to the given rating key. If the
            object associated with the rating key is a show/season, then
            all contained episodes are detailed. An empty list is
            returned if the item(s) associated with the given key cannot
            be found.
        """

        try:
            # Get the episode for this key
            entry = self.__server.fetchItem(rating_key)

            # New show, return all episodes in series
            if entry.type == 'show':
                assert entry.year is not None
                series_info = self.info_set.get_series_info(
                    entry.title, entry.year
                )

                return [
                    (series_info,
                     EpisodeInfoV1(ep.title, ep.parentIndex, ep.index),
                     entry.librarySectionTitle)
                    for ep in entry.episodes()
                ]
            # New season, return all episodes in season
            if entry.type == 'season':
                # Get series associated with this season
                series = self.__server.fetchItem(entry.parentKey)
                if series.year is None:
                    raise ValueError

                series_info = self.info_set.get_series_info(
                    entry.parentTitle, entry.year
                )

                return [
                    (series_info,
                     EpisodeInfoV1(ep.title, entry.index, ep.index),
                     series.librarySectionTitle)
                    for ep in entry.episodes()
                ]
            # New episode, return just that
            if entry.TYPE == 'episode':
                series = self.__server.fetchItem(entry.grandparentKey)
                assert series.year is not None
                series_info = self.info_set.get_series_info(
                    entry.grandparentTitle, series.year
                )

                return [(
                    series_info,
                    EpisodeInfoV1(entry.title, entry.parentIndex, entry.index),
                    entry.librarySectionTitle,
                )]
            # Movie, warn and return empty list
            if entry.type == 'movie':
                log.warning(f'Item with rating key {rating_key} is a movie')
            return []
        except NotFound:
            log.error(f'No item with rating key {rating_key} exists')
        except ValueError:
            log.warning(f'Item with rating key {rating_key} has no year')
        except Exception:
            log.exception(f'Rating key {rating_key} has some error')

        # Error occurred, return empty list
        return []
