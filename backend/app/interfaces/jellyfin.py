from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Literal,
    Union,
    overload,
)

from fastapi import HTTPException

from app.core.config import config
from app.info.episode import EpisodeInfo
from app.info.series import SeriesInfo
from app.interfaces.base import (
    EpisodeDataSource,
    Interface,
    MediaServer,
    SearchResult,
    SourceImage,
    SyncInterface,
    WatchedStatus,
)
from app.interfaces.schemas.jellyfin import (
    ItemDetails,
    ItemQuery,
    LibraryQuery,
    SystemInfo,
    UserQueryItem
)
from app.interfaces.testing import testing_override
from app.interfaces.web import WebInterface, WebSession
from app.logging.logger import log

if TYPE_CHECKING:
    from app.models.card import Card
    from app.models.episode import Episode


class TestingJellyfinInterface:
    def _get_user_id(self, username: str | None) -> str:
        return '123'

    def _map_libraries(self) -> dict[str, str]:
        return { 'TV': 'abc', 'TV 4K': 'def', 'Anime': 'abcdef' }

    def get_usernames(self) -> list[str]:
        return ['Admin', 'User']


class JellyfinInterface(MediaServer, EpisodeDataSource, SyncInterface, Interface):
    """
    This class describes an interface to a Jellyfin media server. This
    is a type of EpisodeDataSource (e.g. interface by which Episode data
    can be retrieved), as well as a MediaServer (e.g. a server in which
    cards can be loaded into).
    """

    INTERFACE_TYPE = 'Jellyfin'

    SERIES_IDS: Annotated[
        ClassVar[tuple[str, ...]],
        "Series ID's that can be set by Jellyfin"
    ] = ('imdb_id', 'jellyfin_id', 'tmdb_id', 'tvdb_id')

    """Datetime format string for airdates reported by Jellyfin"""
    AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f000000Z'


    def __init__(self,
            url: str,
            api_key: str,
            username: str | None = None,
            use_ssl: bool = True,
            filesize_limit: int | None = None,
            *,
            interface_id: int = 0,
        ) -> None:
        """
        Construct a new instance of an interface to a Jellyfin server.

        Args:
            url: The API url communicating with Jellyfin.
            api_key: The API key for API requests.
            username: Username of the Jellyfin account to get watch
                statuses of.
            use_ssl: Whether to use SSL in all requests.
            filesize_limit: Number of bytes to limit a single file to
                during upload.
            interface_id: ID of this interface.
        """

        # Intiialize parent classes
        super().__init__(filesize_limit)

        # Store attributes of this Interface
        self._interface_id = interface_id
        self.session = WebInterface('Jellyfin', use_ssl)
        self.url = url.removesuffix('/')
        self.__params = {'api_key': api_key}
        self.libraries = {}
        self.user_id = ''

        self._session = WebSession(
            url,
            verify_ssl=use_ssl,
            base_parameters={'api_key': api_key},
            timeout=config.JELLYFIN_REQUEST_TIMEOUT,
        )

        # Authenticate with server
        try:
            if not config.TESTING_MODE:
                system_info = self._session.get(
                    '/System/Info',
                    response_model=SystemInfo,
                )

                if not system_info:
                    raise ConnectionError('Unable to authenticate with server')
        except Exception as exc:
            log.critical('Cannot connect to Jellyfin - returned error')
            log.exception('Bad Jellyfin connection')
            raise HTTPException(
                status_code=400,
                detail=f'Cannot connect to Jellyfin - {exc}',
            ) from exc

        self.user_id = self._get_user_id(username)
        self.libraries = self._map_libraries()

        self.activate()


    @testing_override(TestingJellyfinInterface._get_user_id)
    def _get_user_id(self, username: str | None) -> str:
        """
        Get the User ID associated with the given username.

        Args:
            username: Username to query for.

        Returns:
            User ID hexstring associated with the given username.
        """

        # Query for list of all users on this server
        users = self._session.get(
            '/Users',
            response_model=list[UserQueryItem],
        )

        if not users:
            log.critical('Cannot identify any users on this server')
            raise HTTPException(
                status_code=400,
                detail='Cannot identify any users on this server',
            )

        for user in users:
            if not username:
                return user.id
            if user.name == username:
                return user.id

        log.error(f'User "{username}" not found in Jellyfin ({users})')
        raise HTTPException(
            status_code=400,
            detail=f'User "{username}" not found in Jellyfin ({users})',
        )


    @testing_override(TestingJellyfinInterface._map_libraries)
    def _map_libraries(self) -> dict[str, str]:
        """
        Map the libraries on this interface's server.

        Returns:
            Dictionary whose keys are the names of the libraries, and
            whose values are that library's ID.
        """

        libraries = self._session.get(
            '/Items',
            parameters={
                'recursive': True,
                'includeItemTypes': 'CollectionFolder',
            },
            response_model=LibraryQuery,
        )

        if not libraries:
            return {}

        return {library.name: library.id for library in libraries.items}


    @overload
    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            raw_obj: Literal[False] = False,
        ) -> str | None:
        ...

    @overload
    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            raw_obj: Literal[True],
        ) -> SeriesInfo | None:
        ...

    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            raw_obj: bool = False,
        ) -> str | SeriesInfo | None:
        """
        Get the Jellyfin ID (or entire SeriesInfo) for the given series.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series being evaluated.
            raw_obj: Whether to return the raw object rather than just
                the dictionary.

        Returns:
            None if the series is not found. The Jellyfin ID of the
            series if `raw_obj` is False, otherwise the SeriesInfo of
            the found series.
        """


        if (not raw_obj
            and (id_ := series_info.jellyfin_id.get_id(
                self._interface_id, library_name
            )) is not None
        ):
            # Query for this item
            details = self._session.get(
                f'/Items/{id_}?userId={self.user_id}',
                response_model=ItemDetails,
            )

            # Item found, ID is still valid
            if details and details.id == id_:
                return details.id

            # No item found, ID must be invalid - reset and re-query
            log.trace((
                f'Emby ID ({id_}) has been dynamically re-assigned. Querying '
                f'for new one..'
            ))
            series_info.emby_id.delete_id(self._interface_id, library_name)

        # Get ID of this library
        if (library_id := self.libraries.get(library_name)) is None:
            log.error(f'Library "{library_name}" not found in Jellyfin')
            return None

        # Base params for all queries
        parameters: dict[str, Any] = {
            'recursive': True,
            'includeItemTypes': 'Series',
            # isSeries search filter DOES NOT work
            'searchTerm': series_info.name,
            'fields': 'ProviderIds',
            'enableImages': False,
            'parentId': library_id,
        }

        def _query_series(year: int) -> str | SeriesInfo | None:
            """Look up the series in the specified year"""

            all_results = self._session.get(
                '/Items',
                parameters=parameters | ({'years': str(year)} if year else {}),
                response_model=ItemQuery,
            )

            # If no responses, return
            if not all_results or all_results.total_record_count == 0:
                return None

            # Parse all results into SeriesInfo objects
            results = [
                (
                    result,
                    SeriesInfo.from_jellyfin_info(
                        result, self._interface_id, library_name
                    ),
                )
                for result in all_results.items
                if result.premiere_date
            ]

            # Attempt to "smart" match by ID first
            for result, result_series in results:
                if series_info == result_series:
                    return result_series if raw_obj else result.id
            # Attempt to match by name alone
            for result, result_series in results:
                if series_info.matches(result.name):
                    return result_series if raw_obj else result.id

            # No match
            return None

        # Look for series in this year, then surrounding years, then no year
        for year in (
            series_info.year, series_info.year-1, series_info.year+1, None
        ):
            if (jellyfin_id := _query_series(year)) is not None:
                return jellyfin_id

        log.warning(f'Series not found in Jellyfin {series_info!r}')
        return None


    def __get_season_id(self,
            series_id: str,
            season_number: int,
        ) -> str | None:
        """
        Get the Jellyfin ID of the given season.

        Args:
            series_id: Jellyfin ID of the associated series.
            season_number: Season number whose ID is being queried.

        Returns:
            The Jellyfin ID of the season, if found. None otherwise.
        """

        seasons = self._session.get(
            '/Items',
            parameters={
                'recursive': True,
                'includeItemTypes': 'Season',
                'parentId': series_id,
                'startIndex': season_number-1,
                'limit': 1,
            },
            response_model=ItemQuery,
        )

        if not seasons or not seasons.items:
            return None

        return seasons.items[0].id


    def __get_episode_id(self,
            library_name: str,
            series_jellyfin_id: str,
            episode_info: EpisodeInfo,
        ) -> str | None:
        """
        Get the Jellyfin ID for the given episode.

        Args:
            library_name: Name of the library containing the series.
            episode_info: The episode being evaluated.

        Returns:
            Jellyfin ID of the episode, if found. None otherwise.
        """

        # If episode has a Jellyfin ID, return that
        if episode_info.has_id('jellyfin', self._interface_id, library_name):
            return episode_info.jellyfin_id.get_id(
                self._interface_id, library_name
            )

        # Query for this episode
        episodes = self._session.get(
            '/Items',
            parameters={
                'recursive': True,
                'includeItemTypes': 'Episode',
                'ParentId': series_jellyfin_id,
                'parentIndexNumber': episode_info.season_number,
                'startIndex': episode_info.episode_number - 1,
                'limit': 1,
            },
            response_model=ItemQuery,
        )

        if not episodes or not episodes.items:
            return None

        return episodes.items[0].id


    @overload
    def __find_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: None,
        ) -> tuple[None, None] | tuple[str, None]:
        ...

    @overload
    def __find_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
        ) -> tuple[None, None] | tuple[str, str]:
        ...

    def __find_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo | None,
        ) -> tuple[str | None, str | None]:
        """
        Get the Jellyfin ID's for the given series and episode.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series being evaluated.
            episode_info: The episode being evaluated.

        Returns:
            Tuple of the series and episode Jellyfin ID's. The series ID
            will be None if the series cannot be found; the epispde ID
            will be None if an episode was not provided or the episode
            cannot be found.
        """

        # Find series
        series_id = self.__get_series_id(library_name, series_info)
        if series_id is None:
            return None, None

        # If no episode to find, return
        if episode_info is None:
            return series_id, None

        return (
            series_id,
            self.__get_episode_id(library_name, series_id, episode_info)
        )


    @testing_override(TestingJellyfinInterface.get_usernames)
    def get_usernames(self) -> list[str]:
        """
        Get all the usernames for this interface's Jellyfin server.

        Returns:
            List of usernames.
        """

        users = self._session.get(
            '/Users',
            response_model=list[UserQueryItem],
        )

        if not users:
            return []

        return [user.name for user in users]


    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> None:
        """
        Set the series ID's for the given SeriesInfo object.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to set the ID of.
        """

        # Find series
        result = self.__get_series_id(
            library_name, series_info, raw_obj=True
        )
        if result is None:
            log.warning((
                f'Series "{series_info}" was not found under library '
                f'"{library_name}" in Jellyfin'
            ))
            return None

        series_info.jellyfin_id.delete_id(self._interface_id, library_name)
        series_info.copy_ids(result)
        return None


    def set_episode_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
        ) -> None:
        """
        Set the Episode ID's for the given EpisodeInfo objects.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.
            infos: List of EpisodeInfo objects to set the ID's of.
        """

        # Get all episodes for this series
        new_episode_infos = self.get_all_episodes(
            library_name, series_info
        )

        # Match to existing info
        for old_episode_info in episode_infos:
            for new_episode_info, _ in new_episode_infos:
                if old_episode_info == new_episode_info:
                    old_episode_info.copy_ids(new_episode_info)
                    break

        return None


    def query_series(self,
            query: str,
            *,
            return_all: bool = False,
        ) -> list[SearchResult]:
        """
        Search Jellyfin for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            return_all: Whether to return all Series, instead of those
                returned by the given query.

        Returns:
            List of SearchResults for the given query. Results are from
            any library.
        """

        search_results = self._session.get(
            '/Items',
            parameters={
                'recursive': True,
                'includeItemTypes': 'Series',
                'searchTerm': '' if return_all else query,
                'fields': 'ParentId,ProviderIds,Overview',
                'enableImages': False,
            },
            response_model=ItemQuery,
        )

        if not search_results:
            return []

        return [
            SearchResult(
                name=result.name,
                year=result.production_year,
                ongoing=result.status == 'Continuing',
                overview=result.overview or 'No overview available',
                poster=f'{self.url}/Items/{result.id}/Images/Primary?quality=75',
                imdb_id=result.provider_ids.get('Imdb'),
                tmdb_id=result.provider_ids.get('Tmdb'), # type: ignore
                tvdb_id=result.provider_ids.get('Tvdb'), # type: ignore
                tvrage_id=result.provider_ids.get('TvRage'), # type: ignore
            )
            for result in search_results.items
            if result.production_year
        ]


    def get_all_series(self,
            required_libraries: list[str] = [],
            excluded_libraries: list[str] = [],
            required_tags: list[str] = [],
            excluded_tags: list[str] = [],
        ) -> list[tuple[SeriesInfo, str]]:
        """
        Get all series within Jellyfin, as filtered by the given
        libraries and tags.

        Args:
            required_libraries: Library names that a series must be
                present in to be returned.
            excluded_libraries: Library names that a series cannot be
                present in to be returned.
            required_tags: Tags that a series must have all of in order
                to be returned.
            excluded_tags: Tags that a series cannot have any of in
                order to be returned.

        Returns:
            List of tuples of the filtered series info and their
            corresponding library names.
        """

        # Base params for all queries
        parameters: dict[str, Any] = {
            'recursive': True,
            'includeItemTypes': 'Series',
            'fields': 'ProviderIds,Tags',
            'enableImages': False,
        }

        # Also filter by tags if any were provided
        if len(required_tags) > 0:
            parameters.update({'tags': '|'.join(required_tags)})

        # Get all series library at a time
        all_series = []
        for library, library_id in self.libraries.items():
            # Filter by library
            if (required_libraries and library not in required_libraries
                or excluded_libraries and library in excluded_libraries):
                continue

            series_results = self._session.get(
                '/Items',
                parameters=parameters | {'ParentId': library_id},
                response_model=ItemQuery,
            )

            if not series_results:
                continue

            for series in series_results.items:
                # Skip series without airdate/year
                if series.premiere_date is None:
                    log.debug(f'Series {series.name} has no premiere date')
                    continue

                # Skip series if an excluded tag is present
                if any(tag in series.tags for tag in excluded_tags):
                    continue

                all_series.append((
                    SeriesInfo.from_jellyfin_info(
                        series, self._interface_id, library
                    ),
                    library
                ))

        return all_series


    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
        """
        Gets all episode info for the given series. Only episodes that
        have  already aired are returned.

        Args:
            library_name: Name of the library containing the series.
            series_info: Series to get the episodes of.

        Returns:
            List of tuples of the EpisodeInfo objects and the episode
            watched statuses for this series.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info)
        if series_id is None:
            log.warning(f'Series {series_info} not found in Jellyfin')
            return []

        # Get all episodes for this series
        episodes = self._session.get(
            f'/Shows/{series_id}/Episodes',
            parameters={
                'UserId': self.user_id,
                'Fields': 'ProviderIds,PremiereDate'
            },
            response_model=ItemQuery,
        )

        # Invalid return, exit
        if not episodes or not episodes.items:
            log.warning('Jellyfin returned bad Episode data')
            log.trace(episodes)
            return []

        # Parse each returned episode into EpisodeInfo object
        all_episodes = []
        for episode in episodes.items:
            # Skip episodes without required a title, season, or
            # episode number
            if not all((
                episode.name,
                episode.index_number,
                episode.parent_index_number,
            )):
                log.debug(
                    f'Series {series_info} is missing required episode data'
                )
                log.trace(episode)
                continue

            all_episodes.append((
                EpisodeInfo.from_jellyfin_info(
                    episode, self._interface_id, library_name,
                ),
                WatchedStatus(
                    self._interface_id, library_name, episode.user_data.played,
                )
            ))

        return all_episodes


    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episodes: list['Episode'],
        ) -> bool:
        """
        Modify the Episodes' watched attribute according to the watched
        status of the corresponding episodes within Jellyfin.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episodes: List of Episode objects to update.

        Returns:
            Whether any Episode's watched statuses were modified.
        """

        # If no episodes, exit
        if not episodes:
            return False

        # Find this series
        series_id = self.__get_series_id(library_name, series_info)
        if series_id is None:
            return False

        # Get data for each Jellyfin episode
        jellyfin_episodes = self.get_all_episodes(
            library_name, series_info,
        )

        # Update watched statuses of all Episodes
        changed = False
        for episode in episodes:
            episode_info = episode.as_episode_info
            for jellyfin_episode, watched_status in jellyfin_episodes:
                if episode_info == jellyfin_episode:
                    changed |= episode.add_watched_status(
                        watched_status
                    )
                    break

        return changed


    def load_title_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_and_cards: Union[
                list[tuple['Episode', 'Card']],
                list[tuple['Episode', 'Card', str]]
            ],
        ) -> list[tuple['Episode', 'Card']]:
        """
        Load the title cards for the given Series and Episodes.

        Args:
            library_name: Name of the library containing the series.
            series_info: SeriesInfo whose cards are being loaded.
            episode_and_cards: List of tuple of Episode and their
                corresponding Card objects to load. Each tuple may
                optionally include a UID to force load that Card into.

        Returns:
            List of tuples of the Episode and the corresponding Card
            that was loaded.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info)
        if series_id is None:
            return []

        # Load each episode and card
        loaded = []
        for episode, card, *uid in episode_and_cards:
            # UID provided, match directly
            if uid:
                episode_id = uid[0]
            # Find episode, skip if not found
            else:
                episode_id = self.__get_episode_id(
                    library_name, series_id, episode.as_episode_info
                )
                if episode_id is None:
                    continue

            # Shrink image if necessary, skip if cannot be compressed
            if (image := self.compress_image(card.card_file)) is None:
                continue

            # Submit POST request for image upload on Base64 encoded image
            self._session.post_base64_image(
                f'/Items/{episode_id}/Images/Primary',
                image.read_bytes(),
            )
            loaded.append((episode, card))

        # Log load operations to user
        if loaded:
            log.info(f'Loaded {len(loaded)} cards for "{series_info}"')

        return loaded


    def load_season_posters(self,
            library_name: str,
            series_info: SeriesInfo,
            posters: dict[int, str | Path],
        ) -> None:
        """
        Load the given season posters into Jellyfin.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            posters: Dictionary of season numbers to poster URLs or
                files to upload.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info)
        if series_id is None:
            return None

        # Load each episode and card
        for season_number, image in posters.items():
            sid = self.__get_season_id(series_id, season_number)
            if sid is None:
                continue

            # Shrink image if necessary, skip if cannot be compressed
            if (isinstance(image, Path)
                and (image := self.compress_image(image)) is None):
                continue

            # Download or read image
            if isinstance(image, str):
                image_bytes = WebInterface.download_image_raw(image)
                if image_bytes is None:
                    continue
            else:
                image_bytes = image.read_bytes()

            # Upload image
            self._session.post_base64_image(
                f'/Items/{sid}/Images/Primary',
                image_bytes,
            )
            log.debug(
                f'{series_info} loaded poster into season {season_number}'
            )

        return None


    def load_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
            image: str | Path,
        ) -> None:
        """
        Load the given series poster into Jellyfin.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            image: URL or Path to the file to upload.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info)
        if series_id is None:
            return None

        # Shrink image if necessary, skip if cannot be compressed
        if (isinstance(image, Path)
            and (image := self.compress_image(image)) is None):
            return None

        # Download or read image
        if isinstance(image, str):
            image_bytes = WebInterface.download_image_raw(image)
            if image_bytes is None:
                return None
        else:
            image_bytes = image.read_bytes()

        # Upload image
        self._session.post_base64_image(
            f'/Items/{series_id}/Images/Primary',
            image_bytes,
        )
        log.debug(f'{series_info} loaded poster')

        return None


    def load_series_background(self,
            library_name: str,
            series_info: SeriesInfo,
            image: str | Path,
        ) -> None:
        """
        Load the given series background image into Jellyfin.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            image: URL or Path to the file to upload.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info)
        if series_id is None:
            return None

        # Shrink image if necessary, skip if cannot be compressed
        if (isinstance(image, Path)
            and (image := self.compress_image(image)) is None):
            return None

        # Download or read image
        if isinstance(image, str):
            image_bytes = WebInterface.download_image_raw(image)
            if image_bytes is None:
                return None
        else:
            image_bytes = image.read_bytes()

        # Upload image
        self._session.post_base64_image(
            f'/Items/{series_id}/Images/Backdrop',
            image_bytes,
        )
        log.debug(f'{series_info} loaded backdrop')

        return None


    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
        ) -> bytes | None:
        """
        Get the source image for the given episode within Jellyfin.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series whose episode is being queried.
            episode_info: The episode to get the source image of.

        Returns:
            Bytes of the source image for the given Episode. None if the
            episode does not exist in Jellyfin, or no valid image was
            returned.
        """

        # Find series and episode
        series_id, episode_id = self.__find_ids(
            library_name, series_info, episode_info
        )

        # Exit if either series or episode was not found
        if series_id is None:
            log.warning(f'Series {series_info!r} not found in Jellyfin')
            return None
        if episode_id is None:
            log.warning(
                f'{series_info} Episode {episode_info!r} not found in Jellyfin'
            )
            return None

        # Get the source image for this episode
        image = self._session.get_raw(
            f'/Items/{episode_id}/Images/Primary',
            parameters={'Quality': 100},
        )

        # Check if valid content was returned
        if not image or b'does not have an image of type' in image:
            log.warning(f'Episode {episode_info} has no source images')
            return None

        return image


    def get_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> SourceImage:
        """
        Get the poster for the given Series.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series to get the poster of.

        Returns:
            URL to the poster for the given series. None if the library,
            series, or thumbnail cannot be found.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info)
        if series_id is None:
            return None

        # Get the poster image for this Series
        image = self._session.get_raw(
            f'/Items/{series_id}/Images/Primary',
            parameters={'Quality': 100},
        )

        # Check if valid content was returned
        if not image or b'does not have an image of type' in image:
            log.warning(f'Series {series_info} has no poster')
            return None

        return image


    def get_series_logo(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> SourceImage:
        """
        Get the logo for the given Series within Jellyfin.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series to get the logo of.

        Returns:
            Bytes of the logo for given series. None if the series does
            not exist in Jellyfin, or no valid image was returned.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info)
        if series_id is None:
            return None

        # Get the source image for this episode
        image = self._session.get_raw(
            f'/Items/{series_id}/Images/Logo',
            parameters={'Quality': 100},
        )

        # Check if valid content was returned
        if not image or b'does not have an image of type' in image:
            log.warning(f'Series {series_info} has no logo')
            return None

        return image


    def get_libraries(self) -> list[str]:
        """
        Get the names of all libraries within this server.

        Returns:
            List of library names.
        """

        return list(self.libraries)
