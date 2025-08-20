from datetime import datetime, timedelta
from pathlib import Path
from re import IGNORECASE, compile as re_compile
from sys import exit as sys_exit
from typing import Annotated, Any, ClassVar, Literal

from fastapi import HTTPException

from app.core.config import config
from app.info.episode import EpisodeInfo, EpisodeInfoV1
from app.info.series import SeriesInfoV1, SeriesInfo
from app.interfaces.base import (
    EpisodeDataSource,
    EpisodeDataSourceV1,
    SearchResult,
    WatchedStatus,
)
from app.interfaces.base import Interface
from app.interfaces.base import SyncInterface
from app.interfaces.testing import testing_override
from app.interfaces.web import WebInterface
from app.logging.logger import Logger, log


type SeriesType = Literal['anime', 'daily', 'standard']


class TestingSonarrInterface:
    def get_root_folders(self) -> list[Path]:
        return [Path('/media/tv'), Path('/media/tv_4k'), Path('/media/anime')]

    def get_all_tags(self) -> list[dict[Literal['id', 'label'], Any]]:
        return [
            {'label': 'anime', 'id': 1},
            {'label': 'tv', 'id': 2},
            {'label': 'star wars', 'id': 3},
        ]

    def query_series(self,
            query: str,
            *,
            return_all: bool = False,
            log: Logger = log,
        ) -> list[SearchResult]:

        if query == 'Test Series':
            return [
                SearchResult(
                    name='Test Series 1',
                    year=2025,
                    poster='/public/styles/art.jpg',
                    overview=['...'],
                    ongoing=False,
                    tmdb_id=123,
                    tvdb_id=345,
                    imdb_id='tt1234',
                ),
                SearchResult(
                    name='Test Series 2',
                    year=2025,
                    poster='/public/styles/unique.jpg',
                    overview=['lorem ipsum delor sit amet'],
                    ongoing=True,
                    tmdb_id=987,
                    tvdb_id=654,
                    imdb_id='tt9876',
                ),
            ]

        return []

    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> None:
        return None

class SonarrInterface(EpisodeDataSource, WebInterface, SyncInterface, Interface):
    """
    This class describes a Sonarr interface, which is a type of
    EpisodeDataSource, WebInterface, and SyncInterface object which
    connects to an instance of Sonarr.
    """

    INTERFACE_TYPE: ClassVar[str] = 'Sonarr'

    REQUEST_TIMEOUT: Annotated[
        ClassVar[int],
        'Use a longer request timeout for Sonarr to handle slow databases'
    ] = 600

    SERIES_IDS: Annotated[
        ClassVar[tuple[str, ...]],
        "Series ID's that can be set by Sonarr"
    ] = ('imdb_id', 'sonarr_id', 'tvdb_id', 'tvrage_id')

    VALID_SERIES_TYPES: Annotated[
        tuple[str, ...],
        'Series types that can be specified to filter a sync with'
    ] = ('anime', 'daily', 'standard')

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)
    __ALWAYS_IGNORE_REGEX = re_compile(r'^(tba|tbd)$', IGNORECASE)

    """Datetime format string for airDateUtc field in Sonarr API requests"""
    __AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


    def __init__(self,
            url: str,
            api_key: str,
            verify_ssl: bool = True,
            downloaded_only: bool = True,
            *,
            interface_id: int = 0,
            log: Logger = log,
            **_,
        ) -> None:
        """
        Construct a new instance of an interface to Sonarr.

        Args:
            url: The API url communicating with Sonarr.
            api_key: The API key for API requests.
            verify_ssl: Whether to verify SSL requests to Sonarr.
            downloaded_only: Whether to ignore Episode that are not
                downloaded when querying Sonarr for Episode data.
            interface_id: Interface ID of this interface.
            log: Logger for all log messages.

        Raises:
            HTTPException (401): The Sonarr system status cannot be
                pinged.
            HTTPException (422): An invalid URL is provided.
        """

        # Initialize parent WebInterface
        super().__init__('Sonarr', verify_ssl, cache=False, log=log)

        # Get correct URL
        url = url if url.endswith('/') else f'{url}/'
        if url.endswith('/api/v3/'):
            self.url = url
        elif (re_match := self._URL_REGEX.match(url)) is None:
            log.critical(f'Invalid Sonarr URL "{url}"')
            raise HTTPException(
                status_code=422,
                detail=f'Invalid Sonarr URL',
            )
        else:
            self.url = f'{re_match.group(1)}/api/v3/'

        # Base parameters for sending requests to Sonarr
        self.__standard_params = {'apikey': api_key}
        self.interface_id = interface_id
        self.downloaded_only = downloaded_only

        # Query system status to verify connection to Sonarr
        try:
            if not config.TESTING_MODE:
                status = self.get(
                    f'{self.url}system/status',
                    self.__standard_params,
                )
                if status.get('appName') != 'Sonarr':
                    raise HTTPException(
                        status_code=401,
                        detail='Invalid URL / API key',
                    )
        except Exception as e:
            log.critical(f'Cannot connect to Sonarr - returned error: "{e}"')
            raise e

        self.activate()


    @testing_override(TestingSonarrInterface.get_root_folders)
    def get_root_folders(self) -> list[Path]:
        """
        Get all the root folder paths from Sonarr.

        Returns:
            List of root folder paths in Sonarr.
        """

        return [
            Path(folder['path'])
            for folder in
            self.get(f'{self.url}rootfolder', self.__standard_params)
        ]


    def get_all_series(self,
            required_tags: list[str] = [],
            excluded_tags: list[str] = [],
            monitored_only: bool = False,
            downloaded_only: bool = False,
            required_series_type: SeriesType | None = None,
            excluded_series_type: SeriesType | None = None,
            required_root_folders: list[str] = [],
            *,
            log: Logger = log,
        ) -> list[tuple[SeriesInfo, str]]:
        """
        Get all the series within Sonarr, filtered by the given
        parameters.

         Args:
            required_tags: List of tags to filter return by. Only series
                that have all of the given tags are returned.
            excluded_tags: List of tags to filter return by. Series with
                any of the given tags are excluded from return.
            monitored_only: Whether to filter return to exclude series
                that are unmonitored within Sonarr.
            downloaded_only: Whether to filter return to exclude series
                that do not have any downloaded episodes.
            required_series_type: Type of series that must is required
                to be included.
            excluded_series_type: Type of series to exclude from the
                return.
            required_root_folders: List of root folders to filter the
                returned series by.
            log: Logger for all log messages.

        Returns:
            List of tuples. Tuple contains the SeriesInfo object for the
            series, and the Path to the series' media as reported by
            Sonarr.
        """

        # Construct GET arguments
        all_series = self.get(f'{self.url}series', self.__standard_params)

        # Get filtering tags if indicated
        required_tag_ids, excluded_tag_ids = [], []
        if len(required_tags) > 0 or len(excluded_tags) > 0:
            # Request all Sonarr tags, create mapping of label -> ID
            all_tags = {
                tag['label']: tag['id']
                for tag in self.get(f'{self.url}tag', self.__standard_params)
            }

            # Convert tag names to ID's
            required_tag_ids = [all_tags.get(tag, -1) for tag in required_tags]
            excluded_tag_ids = [all_tags.get(tag, -1) for tag in excluded_tags]

            # Log tags not identified with a matching ID
            for tag in (set(required_tags)|set(excluded_tags)) - set(all_tags):
                log.warning(f'Tag "{tag}" not found on Sonarr')

        # Go through each series in Sonarr
        series = []
        for show in all_series:
            # Apply filters
            if ((monitored_only and not show['monitored'])
                or (downloaded_only
                    and show.get('statistics', {}).get('sizeOnDisk', 0) == 0)
                or (excluded_tags
                    and any(tag in excluded_tag_ids for tag in show['tags']))
                or (required_tags
                    and not all(tag in show['tags'] for tag in required_tag_ids))
                or (required_series_type
                    and (show['seriesType'] != required_series_type))
                or (excluded_series_type
                    and (show['seriesType'] == excluded_series_type))
                or (required_root_folders
                    and not any(show['rootFolderPath'].startswith(folder)
                                for folder in required_root_folders))
                or (show['year'] == 0)):
                continue

            # Construct SeriesInfo object for this show
            series_info = SeriesInfo(
                show['title'],
                show['year'],
                imdb_id=show.get('imdbId'),
                sonarr_id=f'{self.interface_id}:{show.get("id")}',
                tvdb_id=show.get('tvdbId'),
                tvrage_id=show.get('tvRageId'),
            )

            # Add to returned list
            series.append((series_info, show['path']))

        return series


    @testing_override(TestingSonarrInterface.set_series_ids)
    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> None:
        """
        Set the TVDb ID for the given SeriesInfo object.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo to update.
            log: Logger for all log messages.
        """

        # If all possible ID's are defined, exit
        if series_info.has_ids(*self.SERIES_IDS, interface_id=self.interface_id):
            return None

        # Search for Series
        search_results: list[dict] = self.get( # type: ignore
            url=f'{self.url}series/lookup',
            params={'term': series_info.name} | self.__standard_params,
        )

        # No results, nothing to set
        if not search_results:
            return None

        # Find matching Series
        for series in search_results:
            try:
                reference_series_info = SeriesInfo(
                    series['title'],
                    series['year'],
                    imdb_id=series.get('imdbId'),
                    tvdb_id=series.get('tvdbId'),
                    tvrage_id=series.get('tvRageId'),
                )
            except TypeError:
                log.warning(f'Error evaluating {series}')
                continue

            # Add Sonarr ID if added to this server
            if (sonarr_id := series.get('id')) is not None:
                reference_series_info.set_sonarr_id(sonarr_id, self.interface_id)

            if series_info == reference_series_info:
                series_info.copy_ids(reference_series_info, log=log)
                break

        return None


    @testing_override(TestingSonarrInterface.query_series)
    def query_series(self,
            query: str,
            *,
            return_all: bool = False,
            log: Logger = log,
        ) -> list[SearchResult]:
        """
        Search Sonarr for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            return_all: Whether to return all Series, instead of those
                returned by the given query.
            log: Logger for all log messages.

        Returns:
            List of SearchResults for the given query. Results include
            Series not added to this Server. All returned poster URL's
            utilize the Sonarr proxy API endpoint to to (1) obfuscate
            this server's API, and so the local `SonarrAuth` cookie can
            be sent when querying for the poster.
        """

        # Perform query
        if return_all:
            search_results = self.get(
                f'{self.url}series', self.__standard_params
            )
        else:
            search_results = self.get(
                url=f'{self.url}series/lookup',
                params={'term': query} | self.__standard_params,
            )

        def get_poster_proxy(images: list[dict[str, str]]) -> str | None:
            """
            Get the proxy URL of for the poster indicated in the given
            set of images.

            Args:
                images: List of image types/URL's to parse for a poster.

            Returns:
                Proxied URL for the poster, if provided. None if there
                are no valid posters.
            """

            for image in images:
                if image['coverType'] == 'poster':
                    url = image['url'].rsplit('?', maxsplit=1)[0]
                    return (
                        f'/api/v2/proxy/sonarr?url={url}'
                        f'&interface_id={self.interface_id}'
                    )

            return None

        def get_sonarr_id(id_: int | None, /) -> str | None:
            return None if id_ is None else f'{self.interface_id}:{id_}'

        return [
            SearchResult(
                name=result['title'],
                year=result['year'],
                ongoing=not result['ended'],
                overview=result.get('overview', 'No overview available'),
                poster=get_poster_proxy(result.get('images', [])),
                imdb_id=result.get('imdbId', None),
                sonarr_id=get_sonarr_id(result.get('id', None)),
                tvdb_id=result.get('tvdbId', None),
                tvrage_id=result.get('tvRageId', None) or None,
            ) for result in search_results if result['year']
        ]


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
            library_name: Unused argument.
            series_info: SeriesInfo for the entry.
            log: Logger for all log messages.

        Returns:
            List of tuples of the EpisodeInfo objects and None (as the
            Episode watched status cannot be determined) for the given
            series.
        """

        # If no ID was returned, error and return an empty list
        if not series_info.has_id('sonarr_id', self.interface_id):
            self.set_series_ids(None, series_info, log=log)
            if not series_info.has_id('sonarr_id', self.interface_id):
                log.debug(f'Series "{series_info}" not found in Sonarr')
                return []

        # Construct GET arguments
        url = f'{self.url}episode/'
        params = {
            'seriesId': series_info.sonarr_id[self.interface_id]
        } | self.__standard_params

        # Query Sonarr to get JSON of all episodes for this series
        all_episodes: list[dict] = self.get(url, params)
        all_episode_info: list[tuple[EpisodeInfo, WatchedStatus]] = []

        # Go through each episode and get its season/episode number, and title
        has_bad_ids = False
        for episode in all_episodes:
            # Skip if not downloaded and ignoring non-downloaded Episodes
            if self.downloaded_only and not episode['hasFile']:
                continue

            # Skip permanent placeholder names if title matching is disabled
            if (not series_info.match_titles
                and self.__ALWAYS_IGNORE_REGEX.match(episode['title'])):
                log.trace(
                    f'Temporarily ignoring "{episode["title"]}" of '
                    f'{series_info} - placeholder title'
                )
                continue

            # Get airdate of this episode
            air_datetime = None
            if (ep_airdate := episode.get('airDateUtc')) is not None:
                # If episode hasn't aired, skip
                air_datetime=datetime.strptime(ep_airdate,self.__AIRDATE_FORMAT)
                if not episode['hasFile'] and air_datetime > datetime.now():
                    log.trace(
                        f'Ignoring "{episode["title"]}" of {series_info} - has '
                        f'not aired yet and is not downloaded'
                    )
                    continue

                # Skip temporary placeholder names if aired in the last 48 hours
                # and title matching is disabled
                if (not series_info.match_titles
                    and air_datetime + timedelta(days=2) > datetime.now()
                    and self.__TEMP_IGNORE_REGEX.match(episode['title'])):
                    log.trace(
                        f'Temporarily ignoring "{episode["title"]}" of '
                        f'{series_info} - placeholder title'
                    )
                    continue

            # If the episode's TVDb ID is 0, then set to None to avoid mismatch
            if episode.get('tvdbId') == 0:
                episode['tvdbId'] = None
                has_bad_ids = True

            # Create EpisodeInfo object for this entry
            all_episode_info.append((
                EpisodeInfo(
                    episode['title'],
                    episode['seasonNumber'],
                    episode['episodeNumber'],
                    episode.get('absoluteEpisodeNumber'),
                    tvdb_id=episode.get('tvdbId'),
                    airdate=air_datetime,
                ),
                WatchedStatus(self.interface_id),
            ))

        # If any episodes had TVDb ID's of 0, then warn user to refresh series
        if has_bad_ids:
            log.warning(
                f'Series "{series_info}" has no TVDb episode ID data - Refresh '
                f'& Scan in Sonarr'
            )

        return all_episode_info


    def set_episode_ids(self,
            library_name: Any,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo
        objects. This sets the TVDb ID for each episode.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo for the entry.
            episode_infos: List of EpisodeInfo objects to update.
            log: Logger for all log messages.
        """

        # Get all episodes for this series
        new_episode_infos = self.get_all_episodes(
            library_name, series_info, log=log
        )

        # Match to existing info
        for old_episode_info in episode_infos:
            for new_episode_info, _ in new_episode_infos:
                if old_episode_info == new_episode_info:
                    old_episode_info.copy_ids(new_episode_info, log=log)
                    break

        return None


    @testing_override(TestingSonarrInterface.get_all_tags)
    def get_all_tags(self) -> list[dict[Literal['id', 'label'], Any]]:
        """
        Get all tags present in Sonarr.

        Returns:
            List of tag dictionary objects.
        """

        return self.get(f'{self.url}tag', self.__standard_params)


    def get_series_path(self, series_id: int) -> str | None:
        """
        Get the path of the series with the given ID.

        Returns:
            Path of the series with the given ID, if found. None if the
            series is not found.
        """

        return self.get(
            f'{self.url}series/{series_id}', self.__standard_params
        ).get('path')


class SonarrInterfaceV1(EpisodeDataSourceV1, WebInterface, SyncInterface):
    """
    This class describes a Sonarr interface, which is a type of
    WebInterface and SyncInterface object.
    """

    """Use a longer request timeout for Sonarr to handle slow databases"""
    REQUEST_TIMEOUT = 600

    """Series ID's that can be set by Sonarr"""
    SERIES_IDS = ('imdb_id', 'sonarr_id', 'tvdb_id', 'tvrage_id')

    """Series types that can be specified to filter a sync with"""
    VALID_SERIES_TYPES = ('anime', 'daily', 'standard')

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)
    __ALWAYS_IGNORE_REGEX = re_compile(r'^(tba|tbd)$', IGNORECASE)

    """Datetime format string for airDateUtc field in Sonarr API requests"""
    __AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


    def __init__(self,
            url: str,
            api_key: str,
            verify_ssl: bool = True,
            downloaded_only: bool = True,
            server_id: int = 0,
        ) -> None:
        """
        Construct a new instance of an interface to Sonarr.

        Args:
            url: The API url communicating with Sonarr.
            api_key: The API key for API requests.
            verify_ssl: Whether to verify SSL requests to Sonarr.
            downloaded_only: Whether to ignore Episode that are not
                downloaded when querying Sonarr for Episode data.
            server_id: Server ID of this server.

        Raises:
            SystemExit: Invalid Sonarr URL/API key provided.
        """

        # Initialize parent WebInterface
        super().__init__('Sonarr', verify_ssl)

        # Get global MediaInfoSet object
        self.info_set = global_objects.info_set

        # Get correct URL
        url = url if url.endswith('/') else f'{url}/'
        if url.endswith('/api/v3/'):
            self.url = url
        elif (re_match := self._URL_REGEX.match(url)) is None:
            log.critical(f'Invalid Sonarr URL "{url}"')
            sys_exit(1)
        else:
            self.url = f'{re_match.group(1)}/api/v3/'

        # Base parameters for sending requests to Sonarr
        self.__api_key = api_key
        self.__standard_params = {'apikey': api_key}
        self.server_id = server_id
        self.downloaded_only = downloaded_only

        # Query system status to verify connection to Sonarr
        try:
            status =self.get(f'{self.url}system/status',self.__standard_params)
            if status.get('appName') != 'Sonarr':
                log.critical(f'Cannot get Sonarr status - invalid URL/API key')
                sys_exit(1)
        except Exception as e:
            log.critical(f'Cannot connect to Sonarr - returned error: "{e}"')
            sys_exit(1)

        # Parse all Sonarr series
        self.__series_data = {}
        self.__map_all_series_data()


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        return (
            f'<SonarrInterface {self.server_id=}, {self.url=}, '
            f'{self.__api_key=}>'
        )


    def __map_all_series_data(self) -> None:
        """
        Map all Sonarr series to their Sonarr and TVDb ID's. This
        updates this object's __series_data attribute with keys of the
        full name for each series (as well as the full name version of
        each alternate title) to a SonarrSeriesInfo dataclass.
        """

        # Construct GET arguments
        url = f'{self.url}series'
        params = self.__standard_params
        all_series = self.get(url, params)

        # Go through each series in Sonarr
        for series in all_series:
            # Skip unaired series with a year of 0
            if series['year'] == 0:
                continue

            # Unpopulated TVRage ID's are left as 0
            tvrage_id = None
            if series.get('tvRageId'):
                tvrage_id = series.get('tvRageId')

            # Data to store for this series, eventually for updating
            # a SeriesInfo object with
            data = {
                'imdb_id': series.get('imdbId'),
                'sonarr_id': f'{self.server_id}-{series["id"]}',
                'tvdb_id': series.get('tvdbId'),
                'tvrage_id': tvrage_id,
            }

            # Create keys to store this data under
            # Always store series under full name and sonarr ID
            if series['title'].endswith(f'({series["year"]})'):
                effective_title = series['title']
            else:
                effective_title = f'{series["title"]} ({series["year"]})'
            keys = [effective_title, f'sonarr:{self.server_id}-{series["id"]}']

            # Also store under any provided database ID's
            if series.get('imdbId'):
                keys.append(f'imdb:{series["imdbId"]}')
            if series.get('tvdbId'):
                keys.append(f'tvdb:{series["tvdbId"]}')
            if tvrage_id:
                keys.append(f'tvrage:{tvrage_id}')

            # Also store series under any available alternative titles
            for alt_title in series['alternateTitles']:
                keys.append(f'{alt_title["title"]} ({series["year"]})')

            # Update all identified keys inside series data dict
            self.__series_data.update(dict.fromkeys(keys, data))


    def has_series(self, series_info: SeriesInfoV1) -> bool:
        """
        Query whether this Sonarr server has the given series.

        Args:
            series_info: Series being evaluated.

        Returns:
            True if the series is present on this server. False
            otherwise.
        """

        # Check for series under any possible keys
        if self.__series_data.get(series_info.full_name):
            return True
        if (series_info.has_id('imdb_id')
            and self.__series_data.get(f'imdb:{series_info.imdb_id}')):
            return True
        if (series_info.has_id('sonarr_id')
            and self.__series_data.get(f'sonarr:{series_info.sonarr_id}')):
            return True
        if (series_info.has_id('tvdb_id')
            and self.__series_data.get(f'tvdb:{series_info.tvdb_id}')):
            return True
        if (series_info.has_id('tvrage_id')
            and self.__series_data.get(f'tvrage_id:{series_info.tvrage_id}')):
            return True

        return False


    def get_all_series(self,
            required_tags: list[str] = [],
            excluded_tags: list[str] = [],
            monitored_only: bool = False,
            downloaded_only: bool = False,
            series_type: str | None = None,
        ) -> list[tuple[SeriesInfoV1, str]]:
        """
        Get all the series within Sonarr, filtered by the given
        parameters.

         Args:
            required_tags: List of tags to filter return by. If
                provided, only series that have all of the given tags
                are returned.
            excluded_tags: List of tags to filter return by. If
                provided, series with any of the given tags are excluded
                from return.
            monitored_only: Whether to filter return to exclude series
                that are unmonitored within Sonarr.
            downloaded_only: Whether to filter return to exclude series
                that do not have any downloaded episodes.
            series_type: Optional series type to filter series by.

        Returns:
            List of tuples. Tuple contains the SeriesInfo object for the
            series, and the Path to the series' media as reported by
            Sonarr.
        """

        # Construct GET arguments
        all_series = self.get(f'{self.url}series', self.__standard_params)

        # Get filtering tags if indicated
        required_tag_ids, excluded_tag_ids = [], []
        if len(required_tags) > 0 or len(excluded_tags) > 0:
            # Request all Sonarr tags, create mapping of label -> ID
            all_tags = {
                tag['label']: tag['id']
                for tag in self.get(f'{self.url}tag', self.__standard_params)
            }

            # Convert tag names to ID's
            required_tag_ids = [all_tags.get(tag, -1) for tag in required_tags]
            excluded_tag_ids = [all_tags.get(tag, -1) for tag in excluded_tags]

            # Log tags not identified with a matching ID
            for tag in (set(required_tags)|set(excluded_tags)) - set(all_tags):
                log.warning(f'Tag "{tag}" not found on Sonarr')

        # Go through each series in Sonarr
        series = []
        for show in all_series:
            # Skip if monitored only and show isn't monitored
            if monitored_only and not show['monitored']:
                continue

            # Skip if downloaded only and filesize is 0
            if (downloaded_only
                and show.get('statistics', {}).get('sizeOnDisk') == 0):
                continue

            # Skip show if tag is in exclude list
            if (len(excluded_tags) > 0
                and any(tag in excluded_tag_ids for tag in show['tags'])):
                continue

            # Skip show if tag isn't in filter (and filter is enabled)
            if (len(required_tags) > 0
                and not all(tag in show['tags'] for tag in required_tag_ids)):
                continue

            # Skip if series type indicated and does not match
            if series_type is not None and show['seriesType'] != series_type:
                continue

            # Skip show if it has a year of 0
            if show['year'] == 0:
                continue

            # Get TVRage ID (0 if not filled out)
            tvrage_id = None
            if show.get('tvRageId'):
                tvrage_id = show.get('tvRageId')

            # Construct SeriesInfo object for this show, do not use MediaInfoSet
            series_info = SeriesInfoV1(
                show['title'],
                show['year'],
                imdb_id=show.get('imdbId'),
                sonarr_id=f'{self.server_id}-{show.get("id")}',
                tvdb_id=show.get('tvdbId'),
                tvrage_id=tvrage_id,
            )

            # Add to returned list
            series.append((series_info, show['path']))

        return series


    def set_series_ids(self, library_name: Any, series_info: SeriesInfoV1) -> None:
        """
        Set the TVDb ID for the given SeriesInfo object.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo to update.
        """

        # If all possible ID's are defined, exit
        if series_info.has_ids(*self.SERIES_IDS):
            return None

        # Look for this series under any of the possible stored keys
        if (data := self.__series_data.get(series_info.full_name)):
            pass
        elif (series_info.has_id('imdb_id') and
            (data := self.__series_data.get(f'imdb:{series_info.imdb_id}'))):
            pass
        elif (series_info.has_id('sonarr_id') and
            (data := self.__series_data.get(f'sonarr:{series_info.sonarr_id}'))):
            pass
        elif (series_info.has_id('tvdb_id') and
            (data := self.__series_data.get(f'tvdb:{series_info.tvdb_id}'))):
            pass
        elif (series_info.has_id('tvrage_id') and
            (data := self.__series_data.get(f'tvrage_id:{series_info.tvrage_id}'))):
            pass
        else:
            log.warning(f'Series "{series_info}" not found in Sonarr')
            return None

        series_info.set_imdb_id(data['imdb_id'])
        series_info.set_sonarr_id(data['sonarr_id'])
        series_info.set_tvdb_id(data['tvdb_id'])
        series_info.set_tvrage_id(data['tvrage_id'])
        return None


    def get_all_episodes(self,
            library_name: Any,
            series_info: SeriesInfoV1,
            episode_infos: list[EpisodeInfoV1] | None = None
        ) -> list[EpisodeInfoV1]:
        """
        Gets all episode info for the given series. Only episodes that
        have already aired are returned.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo for the entry.
            episode_infos: Optional EpisodeInfos to update.

        Returns:
            List of EpisodeInfo objects for the given series.
        """

        # If no ID was returned, error and return an empty list
        if series_info.sonarr_id is None:
            log.warning(f'Series "{series_info}" not found in Sonarr')
            return []

        # Construct GET arguments
        url = f'{self.url}episode/'
        params = {
            'apikey': self.__api_key,
            'seriesId': int(series_info.sonarr_id.split('-')[1])
        }

        # Query Sonarr to get JSON of all episodes for this series
        all_episodes = self.get(url, params)
        all_episode_info = []

        # Go through each episode and get its season/episode number, and title
        has_bad_ids = False
        for episode in all_episodes:
            # Skip if not downloaded and ignoring non-downloaded Episodes
            if self.downloaded_only and not episode['hasFile']:
                continue

            # Get airdate of this episode
            air_datetime = None
            if (ep_airdate := episode.get('airDateUtc')) is not None:
                # If episode hasn't aired, skip
                air_datetime=datetime.strptime(ep_airdate,self.__AIRDATE_FORMAT)
                if not episode['hasFile'] and air_datetime > datetime.now():
                    continue

                # Skip temporary placeholder names if aired in the last 48 hours
                if (self.__TEMP_IGNORE_REGEX.match(episode['title'])
                    and air_datetime + timedelta(days=2) > datetime.now()):
                    log.debug(
                        f'Temporarily ignoring "{episode["title"]}" of '
                        f'{series_info} - placeholder title'
                    )
                    continue

            # Skip permanent placeholder names
            if self.__ALWAYS_IGNORE_REGEX.match(episode['title']):
                continue

            # If the episode's TVDb ID is 0, then set to None to avoid mismatch
            if episode.get('tvdbId') == 0:
                episode['tvdbId'] = None
                has_bad_ids = True

            # Create new EpisodeInfo via global MediaInfoSet object
            if episode_infos is None:
                episode_info = self.info_set.get_episode_info(
                    series_info,
                    episode['title'],
                    episode['seasonNumber'],
                    episode['episodeNumber'],
                    episode.get('absoluteEpisodeNumber'),
                    tvdb_id=episode.get('tvdbId'),
                    title_match=True,
                    queried_sonarr=True,
                    airdate=air_datetime,
                )

                # Add to episode list
                if episode_info is not None:
                    all_episode_info.append(episode_info)
            else:
                tmp_ei = (episode['seasonNumber'], episode['episodeNumber'])
                for episode_info in episode_infos:
                    # Index match, update ID's
                    if episode_info == tmp_ei:
                        episode_info.set_tvdb_id(episode.get('tvdbId'))
                        all_episode_info.append(episode_info)
                        break

        # If any episodes had TVDb ID's of 0, then warn user to refresh series
        if has_bad_ids:
            log.warning(
                f'Series "{series_info}" has no TVDb episode ID data - Refresh '
                f'& Scan in Sonarr'
            )

        return all_episode_info


    def set_episode_ids(self,
            library_name: Any, # pylint: disable=unused-argument
            series_info: SeriesInfoV1,
            episode_infos: list[EpisodeInfoV1],
            *,
            inplace: bool = False
        ) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo
        objects. This sets the TVDb ID for each episode.

        Args:
            series_info: SeriesInfo for the entry.
            infos: List of EpisodeInfo objects to update. Not used.
        """

        self.get_all_episodes(
            library_name,
            series_info,
            episode_infos=episode_infos if inplace else None
        )


    def get_all_tags(self) -> list[dict]:
        """
        Get all tags present in Sonarr.

        Returns:
            List of tag dictionary objects with the keys "id" and
            "label" for each tag.
        """

        return self.get(f'{self.url}tag', self.__standard_params)


    def list_all_series_id(self) -> None:
        """List all the series ID's of all shows used by Sonarr. """

        # Construct GET arguments
        url = f'{self.url}series'
        params = self.__standard_params
        all_series = self.get(url, params)

        # Go through each series in Sonarr
        for show in all_series:
            # Print the main and alternate titles
            main_title = show['title']
            alt_titles = [_['title'] for _ in show['alternateTitles']]

            padding = len(f'{show["id"]} : ')
            titles = f'\n{" " * padding}'.join([main_title] + alt_titles)
            print(f'{show["id"]} : {titles}')
