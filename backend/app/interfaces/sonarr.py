from datetime import datetime
from pathlib import Path
from re import IGNORECASE, compile as re_compile
from typing import Any, ClassVar

from app.interfaces.schemas.sonarr import (
    EpisodeResource,
    MediaCover,
    RootFolder,
    SeriesResource,
    SeriesType,
    SystemInfo,
    TagResource,
)
from fastapi import HTTPException

from app.core.config import config
from app.info.episode import EpisodeInfo
from app.info.series import SeriesInfo
from app.interfaces.base import EpisodeDataSource, SearchResult, WatchedStatus
from app.interfaces.base import Interface, SyncInterface
from app.interfaces.testing import testing_override
from app.interfaces.web import WebSession
from app.logging.logger import log
from app.settings import settings


class TestingSonarrInterface:
    def get_root_folders(self) -> list[Path]:
        return [Path('/media/tv'), Path('/media/tv_4k'), Path('/media/anime')]

    def get_all_tags(self) -> list[TagResource]:
        return [
            TagResource(label='anime', id=1),
            TagResource(label='tv', id=2),
            TagResource(label='star wars', id=3),
        ]

    def query_series(self,
            query: str,
            *,
            return_all: bool = False,
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
        ) -> None:
        return None


class SonarrInterface(EpisodeDataSource, SyncInterface, Interface):
    """
    This class describes a Sonarr interface, which is a type of
    EpisodeDataSource, WebInterface, and SyncInterface object which
    connects to an instance of Sonarr.

    API Documentation is available at: https://sonarr.tv/docs/api/#v3/
    """

    INTERFACE_TYPE: ClassVar[str] = 'Sonarr'

    """Episode titles that indicate a placeholder and are to be ignored"""
    __TEMP_IGNORE_REGEX = re_compile(r'^(tba|tbd|episode \d+)$', IGNORECASE)
    __ALWAYS_IGNORE_REGEX = re_compile(r'^(tba|tbd)$', IGNORECASE)


    def __init__(self,
            url: str,
            api_key: str,
            verify_ssl: bool = True,
            downloaded_only: bool = True,
            *,
            interface_id: int = 0,
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

        Raises:
            HTTPException (401): The Sonarr system status cannot be
                pinged.
        """

        # Standardize URL
        api_url = (
            url.removesuffix('/').removesuffix('/api').removesuffix('/api/v3')
            + '/api/v3/'
        )

        # Base parameters for sending requests to Sonarr
        self.interface_id = interface_id
        self.downloaded_only = downloaded_only
        self._session = WebSession(
            api_url,
            verify_ssl=verify_ssl,
            base_parameters={'apikey': api_key},
            timeout=config.SONARR_REQUEST_TIMEOUT,
        )

        self.__verify_connection()
        self.activate()


    def __verify_connection(self) -> None:
        """
        Verify that the connection to Sonarr is valid.

        Raises:
            HTTPException (401): The connection to Sonarr is invalid.
                The URL or API key is incorrect.
        """

        # Do not verify connection in testing mode
        if config.TESTING_MODE:
            return None

        info = self._session.get(
            '/system/status',
            response_model=SystemInfo,
        )

        if not info or not info.app_name == 'Sonarr':
            log.critical('Cannot connect to Sonarr')
            raise HTTPException(
                status_code=401,
                detail='Invalid Connection Details',
            )

        return None


    @testing_override(TestingSonarrInterface.get_root_folders)
    def get_root_folders(self) -> list[Path]:
        """
        Get all the root folder paths from Sonarr.

        Returns:
            List of root folder paths in Sonarr.
        """

        root_folders = self._session.get(
            '/rootfolder',
            response_model=list[RootFolder],
        )

        if not root_folders:
            log.exception('Error querying root folders from Sonarr')
            return []

        return [Path(folder.path) for folder in root_folders]



    def get_all_series(self,
            required_tags: list[str] = [],
            excluded_tags: list[str] = [],
            monitored_only: bool = False,
            downloaded_only: bool = False,
            required_series_type: SeriesType | None = None,
            excluded_series_type: SeriesType | None = None,
            required_root_folders: list[str] = [],
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

        Returns:
            List of tuples. Tuple contains the SeriesInfo object for the
            series, and the Path to the series' media as reported by
            Sonarr.
        """

        all_series = self._session.get(
            '/series',
            response_model=list[SeriesResource]
        )

        if not all_series:
            log.exception('Error querying series from Sonarr')
            return []

        # Get filter tags if indicated
        required_tag_ids, excluded_tag_ids = [], []
        if required_tags or excluded_tags:
            # Request all Sonarr tags, create mapping of label -> ID
            tag_details = self._session.get(
                '/tag',
                response_model=list[TagResource]
            )

            if tag_details:
                tags = {tag.label: tag.id for tag in tag_details}
                required_tag_ids = [tags.get(tag, -1) for tag in required_tags]
                excluded_tag_ids = [tags.get(tag, -1) for tag in excluded_tags]

                # Log tags not identified with a matching ID
                for tag in (set(required_tags) | set(excluded_tags)) - set(tags):
                    log.warning(f'Tag "{tag}" not found on Sonarr')
            else:
                log.exception('Error querying tags from Sonarr')


        def is_excluded(series: SeriesResource, /) -> bool:
            """Determine if the given series is to be excluded."""

            return bool(
                (monitored_only and not series.monitored)
                or (downloaded_only and series.statistics.size_on_disk < 100)
                or (required_series_type and series.type != required_series_type)
                or (excluded_series_type and series.type == excluded_series_type)
                or (
                    excluded_tag_ids
                    and any(tag in excluded_tag_ids for tag in series.tags)
                )
                or (
                    required_tags
                    and not all(tag in series.tags for tag in required_tag_ids)
                )
                or (
                    required_root_folders
                    and (
                        series.root_folder_path is None
                        or not any(
                            series.root_folder_path.startswith(folder)
                            for folder in required_root_folders
                        )
                    )
                )
            )


        return [
            (
                SeriesInfo.from_sonarr_resource(series, self.interface_id),
                series.path,
            )
            for series in all_series
            if (
                series.path is not None
                and series.title is not None
                and series.year
                and not is_excluded(series)
            )
        ]



    @testing_override(TestingSonarrInterface.set_series_ids)
    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> None:
        """
        Set the TVDb ID for the given SeriesInfo object.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo to update.
        """

        # If all possible ID's are defined, exit
        if series_info.has_ids(
            'imdb_id', 'sonarr_id', 'tvdb_id', 'tvrage_id',
            interface_id=self.interface_id
        ):
            return None

        # Search for Series by TVDb ID first
        results = None
        if series_info.tvdb_id:
            results = self._session.get(
                f'/series?tvdbId={series_info.tvdb_id}',
                response_model=list[SeriesResource],
            )

        # Nothing found, search by name
        if not results:
            results = self._session.get(
                '/series/lookup',
                parameters={'term': series_info.name},
                response_model=list[SeriesResource],
            )

        # Still not found, warn and exit
        if not results:
            log.warning(f'Series "{series_info}" not found in Sonarr')
            return None

        # Find matching Series
        for series in results:
            if not series.title or not series.year:
                log.trace(f'Series "{series}" has no title/year')
                continue

            this_series = SeriesInfo.from_sonarr_resource(
                series, self.interface_id
            )

            if this_series == series_info:
                series_info.copy_ids(this_series)
                break

        return None


    @testing_override(TestingSonarrInterface.query_series)
    def query_series(self,
            query: str,
            *,
            return_all: bool = False,
        ) -> list[SearchResult]:
        """
        Search Sonarr for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            return_all: Whether to return all Series, instead of those
                returned by the given query.

        Returns:
            List of SearchResults for the given query. Results include
            Series not added to this Server. All returned poster URL's
            utilize the Sonarr proxy API endpoint to to (1) obfuscate
            this server's API, and so the local `SonarrAuth` cookie can
            be sent when querying for the poster.
        """

        # Perform query
        if return_all:
            search_results = self._session.get(
                '/series',
                response_model=list[SeriesResource]
            )
        else:
            search_results = self._session.get(
                '/series/lookup',
                parameters={'term': query},
                response_model=list[SeriesResource],
            )

        if not search_results:
            return []

        def get_poster_proxy(images: list[MediaCover]) -> str | None:
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
                if image.cover_type == 'poster':
                    url = image.url.rsplit('?', maxsplit=1)[0]
                    return (
                        f'/api/v2/proxy/sonarr?url={url}'
                        f'&interface_id={self.interface_id}'
                    )

            return None

        return [
            SearchResult.from_sonarr_resource(
                result,
                self.interface_id,
                poster=get_poster_proxy(result.images),
            )
            for result in search_results
            if result.title and result.year
        ]


    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
        """
        Gets all episode info for the given series. Only episodes that
        have  already aired are returned.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo for the entry.

        Returns:
            List of tuples of the EpisodeInfo objects and None (as the
            Episode watched status cannot be determined) for the given
            series.
        """

        # If no ID was returned, error and return an empty list
        if not series_info.sonarr_id.has_id(self.interface_id):
            self.set_series_ids('', series_info)
            if not series_info.sonarr_id.has_id(self.interface_id):
                log.debug(f'Series "{series_info}" not found in Sonarr')
                return []

        # Query episode data for this series
        all_episodes = self._session.get(
            '/episode',
            parameters={
                'seriesId': series_info.sonarr_id.get_id(self.interface_id),
            },
            response_model=list[EpisodeResource],
        )

        if not all_episodes:
            log.error(f'Error querying episodes for {series_info} from Sonarr')
            return []

        # Go through each episode and get its season/episode number, and title
        infos: list[tuple[EpisodeInfo, WatchedStatus]] = []
        for episode in all_episodes:
            # Skip if not downloaded and ignoring non-downloaded Episodes
            if self.downloaded_only and not episode.has_file:
                continue

            # Skip permanent placeholder/empty titles
            if (not episode.title
                or (
                    not series_info.match_titles
                    and self.__ALWAYS_IGNORE_REGEX.match(episode.title)
                )
            ):
                log.trace((
                    f'Temporarily ignoring "{episode.title or ''}" of '
                    f'{series_info} - placeholder title'
                ))
                continue

            # Skip unaired episodes which have a temporary title
            if (episode.airdate is not None
                and not episode.has_file and (
                    (
                        # Timezone-naive airdate
                        episode.airdate.tzinfo is None
                        and episode.airdate > datetime.now()
                    ) or (
                        # Timezone-aware airdate
                        episode.airdate.tzinfo is not None
                        and episode.airdate > settings.config.now()
                    )
                )
                and self.__TEMP_IGNORE_REGEX.match(episode.title or '')):
                log.trace((
                    f'Temporarily ignoring "{episode.title}" of '
                    f'{series_info} - placeholder title'
                ))
                continue

            infos.append(
                (
                    EpisodeInfo.from_sonarr_resource(episode),
                    WatchedStatus(self.interface_id),
                )
            )

        return infos


    def set_episode_ids(self,
            library_name: Any,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
        ) -> None:
        """
        Set all the episode ID's for the given list of EpisodeInfo
        objects. This sets the TVDb ID for each episode.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo for the entry.
            episode_infos: List of EpisodeInfo objects to update.
        """

        # Get all episodes for this series
        new_episode_infos = self.get_all_episodes(library_name, series_info)

        # Match to existing info
        for old_episode_info in episode_infos:
            for new_episode_info, _ in new_episode_infos:
                if old_episode_info == new_episode_info:
                    old_episode_info.copy_ids(new_episode_info)
                    break

        return None


    @testing_override(TestingSonarrInterface.get_all_tags)
    def get_all_tags(self) -> list[TagResource]:
        """
        Get all tags present in Sonarr.

        Returns:
            List of tag dictionary objects.
        """

        return self._session.get('/tag', response_model=list[TagResource]) or []


    def get_series_path(self, series_id: int) -> str | None:
        """
        Get the path of the series with the given ID.

        Returns:
            Path of the series with the given ID, if found. None if the
            series is not found.
        """

        series = self._session.get(
            f'/series/{series_id}',
            response_model=SeriesResource,
        )

        return None if not series else series.path
