from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Iterator,
    Literal,
    overload,
)

from fastapi import HTTPException

from app.core.config import config
from app.info.episode import EpisodeInfo
from app.info.series import SeriesInfo
from app.info.util import match_episode_infos
from app.interfaces.base import (
    EpisodeDataSource,
    Interface,
    MediaServer,
    SearchResult,
    SourceImage,
    SyncInterface,
    WatchedStatus,
)
from app.interfaces.schemas.emby import (
    EpisodeDetails,
    EpisodeQueryResult,
    ItemDetails,
    LibraryMediaFolder,
    QueryResult,
    SystemInfo,
    UserDetails,
    UserQuery,
)
from app.interfaces.testing import testing_override
from app.interfaces.web import WebInterface, WebSession
from app.logging.logger import log

if TYPE_CHECKING:
    from app.models.card import Card
    from app.models.episode import Episode


class TestingEmbyInterface:
    def _get_user_id(self, username: str | None) -> str:
        return 'Admin'

    def _map_libraries(self) -> dict[str, tuple[int, ...]]:
        return { 'TV': (1, 2), 'TV 4K': (3, 4), 'Anime': (5, ) }

    def get_usernames(self) -> list[str]:
        return ['Admin', 'User']

    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> None:
        return None

    def get_series_poster(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> SourceImage:
        return None

    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
        # TODO Populate with test data
        return []


class EmbyInterface(MediaServer, EpisodeDataSource, SyncInterface, Interface):
    """
    This class describes an interface to an Emby media server. This is a
    type of EpisodeDataSource (e.g. interface by which Episode data can
    be retrieved), as well as a MediaServer (e.g. a server in which
    cards can be loaded into).
    """

    INTERFACE_TYPE: ClassVar[str] = 'Emby'

    DEFAULT_FILESIZE_LIMIT: Annotated[
        ClassVar[str | None],
        'Filesize limit for all uploading assets - no limit by default'
    ] = None

    """Series ID's that can be set by Emby"""
    SERIES_IDS = ('emby_id', 'imdb_id', 'tmdb_id', 'tvdb_id')

    AIRDATE_FORMAT: Annotated[
        ClassVar[str],
        'Datetime format string for airdates reported by Emby'
    ] = '%Y-%m-%dT%H:%M:%S.%f000000Z'

    YEARS: Annotated[
        ClassVar[str],
        'Range of years to query series by'
    ] = ','.join(map(str, range(1960, 2030)))


    def __init__(self,
            url: str,
            api_key: str,
            username: str | None,
            use_ssl: bool = True,
            filesize_limit: int | None = None,
            *,
            interface_id: int = 0,
        ) -> None:
        """
        Construct a new instance of an interface to an Emby server.

        Args:
            url: The API url communicating with Emby.
            api_key: The API key for API requests.
            username: Username of the Emby account to get watch statuses
                of.
            use_ssl: Whether to use SSL in all requests.
            filesize_limit: Number of bytes to limit a single file to
                during upload.
            interface_id: ID of this interface.

        Raises:
            HTTPException (400): Invalid connection/user details.
        """

        # Intiialize parent classes
        super().__init__(filesize_limit)

        # Store attributes of this Interface
        self._interface_id = interface_id
        self.url = url.removesuffix('/')
        self._session = WebSession(
            url,
            verify_ssl=use_ssl,
            base_parameters={'api_key': api_key},
            timeout=config.EMBY_REQUEST_TIMEOUT,
        )
        self.user_id = ''
        self.libraries = {}

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
            log.critical(f'Cannot connect to Emby - returned error {exc}')
            log.exception('Bad Emby connection')
            raise HTTPException(
                status_code=400,
                detail=f'Cannot connect to Emby - {exc}',
            ) from exc

        # Get user ID
        if (user_id := self._get_user_id(username)) is None:
            log.critical(f'Cannot identify ID of user "{username}"')
            raise HTTPException(
                status_code=400,
                detail=f'Cannot identify ID of user "{username}"',
            )
        self.user_id = user_id

        # Make mapping of folder ID to library name
        self.libraries = self._map_libraries()
        self._library_ids = {
            id_: library_name
            for library_name, library in self.libraries.items()
            for id_ in library
        }

        self.activate()


    @testing_override(TestingEmbyInterface._get_user_id)
    def _get_user_id(self, username: str | None) -> str:
        """
        Get the User ID associated with the given username.

        Args:
            username: Username to query for. If omitted, the first user
                on the server will be used.

        Returns:
            User ID hexstring associated with the given username.

        Raises:
            HTTPException (400): Cannot identify any users on this
                server or user not found.
        """

        users = self._session.get(
            '/Users/Query',
            response_model=UserQuery,
        )

        if not users or not users.items:
            log.critical('Cannot identify any users on this server')
            raise HTTPException(
                status_code=400,
                detail='Cannot identify any users on this server',
            )

        for user in users.items:
            if not username:
                return user.id
            if user.name == username:
                return user.id

        log.error(f'User "{username}" not found in Emby ({users})')
        raise HTTPException(
            status_code=400,
            detail=f'User "{username}" not found in Emby ({users})',
        )


    @testing_override(TestingEmbyInterface._map_libraries)
    def _map_libraries(self) -> dict[str, tuple[int, ...]]:
        """
        Map the libraries on this interface's Emby server.

        Returns:
            Dictionary whose keys are the names of the libraries, and
            whose values are tuples of the folder ID's for those
            libraries.
        """

        libraries = self._session.get(
            '/Library/SelectableMediaFolders',
            response_model=list[LibraryMediaFolder],
        )

        if libraries is None:
            return {}

        return {
            library.name: tuple(
                int(subfolder.id) for subfolder in library.subfolders
            )
            for library in libraries
        }


    @overload
    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            raw_obj: Literal[False] = False,
        ) -> int | None: ...

    @overload
    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            raw_obj: Literal[True],
        ) -> SeriesInfo | None: ...

    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            raw_obj: bool = False,
        ) -> int | SeriesInfo | None:
        """
        Get the Jellyfin ID for the given series.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series being evaluated.
            raw_obj: Whether to return the raw object from the `/Items`
                endpoint (rather than just the series ID).

        Returns:
            None if the series is not found. The Jellyfin ID of the
            series if raw_obj is False, otherwise the SeriesInfo of the
            found series.
        """

        if (not raw_obj
            and (id_ := series_info.emby_id.get_id(
                self._interface_id, library_name
            )) is not None
        ):
            # Query for this item within Emby
            details = self._session.get(
                f'/Users/{self.user_id}/Items/{id_}',
                response_model=ItemDetails,
            )

            # Item found, ID is still valid
            if details and details.id == int(id_):
                return details.id

            # No item found, ID must be invalid - reset and re-query
            log.trace((
                f'Emby ID ({id_}) has been dynamically re-assigned. Querying '
                f'for new one..'
            ))
            series_info.emby_id.delete_id(self._interface_id, library_name)

        # Get ID of this library
        if (library_ids := self.libraries.get(library_name)) is None:
            log.error(f'Library "{library_name}" not found in Emby')
            return None

        # Base parameters for all queries
        parameters: dict[str, Any] = {
            'Recursive': True,
            'Years': series_info.year,
            'IncludeItemTypes': 'series',
            'EnableUserData': False,
            'SearchTerm': series_info.name,
            'Fields': 'ProviderIds,PremiereDate',
        }
        if (pid := series_info.emby_provider_id_string) is not None:
            parameters['AnyProviderIdEquals'] = pid

        for library_id in library_ids:
            # Search for this series in this library
            query = self._session.get(
                '/Items',
                parameters=parameters | {'ParentId': library_id},
                response_model=QueryResult,
            )

            # No results found, continue to next library
            if not query or not query.total_record_count:
                continue

            # Process each returned series
            for item in query.items:
                # Skip non-series items
                if item.type != 'Series':
                    continue

                # Skip series without premiere date / year
                if item.premiere_date is None:
                    log.debug(f'Series {item.name} has no premiere date')
                    continue

                this_series = SeriesInfo.from_emby_info(
                    item, self._interface_id, library_name
                )
                if this_series == series_info:
                    return this_series if raw_obj else item.id

        log.warning(f'Series "{series_info}" was not found in Emby')
        return None


    def __get_season_id(self, series_id: int, season_number: int) -> int | None:
        """
        Get the Emby ID of the given season.

        Args:
            series_id: Emby ID of the associated series.
            season_number: Season number whose ID is being queried.

        Returns:
            The Emby ID of the season, if found. None otherwise.
        """

        seasons = self._session.get(
            '/Items',
            parameters={
                'recursive': True,
                'includeItemTypes': 'Season',
                'parentId': series_id,
            },
            response_model=QueryResult,
        )

        if not seasons or not seasons.total_record_count:
            return None

        for season in seasons.items:
            if (season.series_id == series_id
                and season.index_number == season_number):
                return season.id

        return None


    def __get_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> Iterator[EpisodeDetails]:
        """
        Iterate through all the episodes associated with the given
        series.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.

        Yields:
            ItemDetails objects of episode data as returned by the
            `/Shows/{id}/Episodes` API endpoint.
        """

        # Find series
        emby_id = self.__get_series_id(library_name, series_info)
        if emby_id is None:
            return None

        episodes = self._session.get(
            f'/Shows/{emby_id}/Episodes',
            parameters={
                'UserId': self.user_id,
                'Fields': 'ProviderIds',
            },
            response_model=EpisodeQueryResult,
        )

        if not episodes or not episodes.total_record_count:
            return None

        for episode in episodes.items:
            if (episode.index_number is None
                or episode.parent_index_number is None):
                log.debug(f'Series {series_info} episode is missing index data')
                continue

            yield episode

        return None


    @testing_override(TestingEmbyInterface.get_usernames)
    def get_usernames(self) -> list[str]:
        """
        Get all the usernames for this interface's Emby server.

        Returns:
            List of usernames.
        """

        users = self._session.get(
            '/Users',
            response_model=list[UserDetails],
        )

        if not users:
            return []

        return [user.name for user in users]


    @testing_override(TestingEmbyInterface.set_series_ids)
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

        series = self.__get_series_id(library_name, series_info, raw_obj=True)
        if not series:
            log.warning((
                f'Series "{series_info}" was not found under library '
                f'"{library_name}" in Emby'
            ))
            return None

        # Remove existing Emby ID if one exists
        if series_info.emby_id.get_id(self._interface_id, library_name):
            series_info.emby_id.delete_id(self._interface_id, library_name)

        # Add new ID's
        series_info.copy_ids(series)
        return None


    def set_episode_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
        ) -> None:
        """
        Set the Episode ID's for the given EpisodeInfo objects.

        Args:
            library_name: Name of the library the series is under.
            series_info: Series to get the episodes of.
            infos: List of EpisodeInfo objects to set the ID's of.
        """

        new_episode_infos = self.get_all_episodes(library_name, series_info)

        matched, _ = match_episode_infos(
            episode_infos,
            [info for info, _ in new_episode_infos],
        )
        for old_info, new_matches in matched:
            if new_matches:
                old_info.copy_ids(new_matches[0])


    def query_series(self,
            query: str,
            *,
            return_all: bool = False,
        ) -> list[SearchResult]:
        """
        Search Emby for any Series matching the given query.

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
                'Recursive': True,
                'IncludeItemTypes': 'Series',
                'SearchTerm': '' if return_all else query,
                'Fields': 'ParentId,ProviderIds,Overview,ProductionYear,Status',
                'EnableUserData': False,
                'EnableImages': True,
                'ImageTypes': 'Primary',
            },
            response_model=QueryResult,
        )

        if not search_results or not search_results.total_record_count:
            return []

        def get_emby_id(result: ItemDetails, /) -> str | None:
            if result.parent_id is None:
                return None
            if (library := self._library_ids.get(result.parent_id)) is None:
                return None
            return f'{self._interface_id}:{library}:{result.id}'

        return [
            SearchResult.from_emby_resource(
                result,
                f'{self.url}/Items/{result.id}/Images/Primary?quality=75',
                get_emby_id(result),
            )
            for result in search_results.items
            if result.production_year
        ]


    def get_library_paths(self,
            filter_libraries: list[str] = [],
        ) -> dict[str, list[str]]:
        """
        Get all libraries and their associated base directories.

        Args:
            filer_libraries: List of library names to filter the return.

        Returns:
            Dictionary whose keys are the library names, and whose
            values are the list of paths to that library's base
            directories.
        """

        libraries = self._session.get(
            '/Library/SelectableMediaFolders',
            response_model=list[LibraryMediaFolder],
        )

        if not libraries:
            return {}

        return {
            library.name: [folder.path for folder in library.subfolders]
            for library in libraries
            if (
                not filter_libraries
                or library.name in filter_libraries
            )
        }


    def get_all_series(self,
            required_libraries: list[str] = [],
            excluded_libraries: list[str] = [],
            required_tags: list[str] = [],
            excluded_tags: list[str] = [],
        ) -> list[tuple[SeriesInfo, str]]:
        """
        Get all series within Emby, as filtered by the given libraries.

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

        # Base parameters for all queries
        parameters: dict[str, Any] = {
            'Recursive': True,
            'IncludeItemTypes': 'Series',
            'Fields': 'ProviderIds,PremiereDate',
        }

        # Get excluded series ID's if excluding by tags
        if excluded_tags:
            excluded_series = self._session.get(
                '/Items',
                parameters=parameters | {'Tags': '|'.join(excluded_tags)},
                response_model=QueryResult,
            )

            if excluded_series:
                parameters.update({
                    'ExcludeItemIds': ','.join((
                        str(item.id) for item in excluded_series.items
                    ))
                })

        # Filter by required tags if provided
        if required_tags:
            parameters.update({'Tags': '|'.join(required_tags)})

        # Add years query
        parameters.update({'Years': self.YEARS})

        # Go through each library in this server
        all_series: list[tuple[SeriesInfo, str]] = []
        for library, library_ids in self.libraries.items():
            # Filter by library
            if ((required_libraries and library not in required_libraries)
                or (excluded_libraries and library in excluded_libraries)):
                continue

            # Go through every subfolder (the parent ID) in this library
            for parent_id in library_ids:
                # Get all items (series) in this subfolder
                series_query = self._session.get(
                    '/Items',
                    parameters=parameters | {'ParentId': parent_id},
                    response_model=QueryResult,
                )

                if not series_query or not series_query.total_record_count:
                    continue

                for series in series_query.items:
                    if series.premiere_date is None:
                        log.debug(f'Series {series.name} has no premiere date')
                        continue

                    all_series.append((
                        SeriesInfo.from_emby_info(
                            series, self._interface_id, library
                        ),
                        library,
                    ))

        return all_series


    @testing_override(TestingEmbyInterface.get_all_episodes)
    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
        """
        Gets all episode info for the given series. Only episodes that
        have already aired are returned.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.

        Returns:
            List of tuples of EpisodeInfo and WatchStatus objects for
            this series.
        """

        return [
            (
                EpisodeInfo.from_emby_info(
                    episode, self._interface_id, library_name
                ),
                WatchedStatus(
                    self._interface_id, library_name, episode.user_data.played
                )
            )
            for episode in self.__get_episodes(library_name, series_info)
        ]


    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfo,
            episodes: list['Episode'],
        ) -> bool:
        """
        Modify the Episodes' watched attribute according to the watched
        status of the corresponding episodes within Emby.

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

        # Get data for each Emby episode
        emby_episodes = [
            (
                EpisodeInfo.from_emby_info(
                    episode, self._interface_id, library_name
                ),
                WatchedStatus(
                    self._interface_id, library_name, episode.user_data.played,
                )
            )
            for episode in
            self.__get_episodes(library_name, series_info)
        ]
        emby_infos = [info for info, _ in emby_episodes]
        ws_by_info_id = {id(info): ws for info, ws in emby_episodes}

        # Update watched statuses of all Episodes
        changed = False
        matched, _ = match_episode_infos(
            [episode.as_episode_info for episode in episodes],
            emby_infos,
        )
        for episode, (_, emby_matches) in zip(episodes, matched):
            for emby_info in emby_matches:
                changed |= episode.add_watched_status(
                    ws_by_info_id[id(emby_info)],
                )

        return changed


    def load_title_cards(self,
            library_name: str,
            series_info: SeriesInfo,
            episode_and_cards: (
                list[tuple['Episode', 'Card']]
                | list[tuple['Episode', 'Card', str]]
            ),
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
            List of tuple of Episode and Card pairs which were loaded.
        """

        # If series has no Emby ID, or no episodes, exit
        if not episode_and_cards:
            return []

        # Get Emby ID for each Episode/Card pair
        matched: list[tuple['Episode', 'Card', str]] = []

        # UID provided, use directly
        if len(episode_and_cards[0]) == 3:
            matched = episode_and_cards # type: ignore
        # Match each episode via episode info
        else:
            emby_eps = list(self.__get_episodes(library_name, series_info))
            matched_map, _ = match_episode_infos(
                [episode.as_episode_info for episode, *_ in episode_and_cards],
                emby_eps,
            )
            for (_, emby_matches), (episode, card) in zip(
                matched_map, episode_and_cards
            ):
                for emby_ep in emby_matches:
                    emby_info = EpisodeInfo.from_emby_info(
                        emby_ep, self._interface_id, library_name
                    )
                    emby_id = emby_info.emby_id.get_id(
                        self._interface_id, library_name
                    )
                    if emby_id is not None:
                        matched.append((episode, card, emby_id))
                    break

        # Load each episode and card
        loaded = []
        for episode, card, emby_id in matched:
            if (image := self.compress_image(card.card_file)) is None:
                continue

            # Submit POST request for image upload on Base64 encoded image
            self._session.post_base64_image(
                f'/Items/{emby_id}/Images/Primary',
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
        Load the given season posters into Emby.

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

        # Load each season's poster
        for season_number, image in posters.items():
            sid = self.__get_season_id(series_id, season_number)
            if sid is None:
                log.warning(f'Season {season_number} not found')
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
        Load the given series poster into Emby.

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
        Load the given series background image into Emby.

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

        # Submit POST request for image upload on Base64 encoded image
        self._session.delete(f'/Items/{series_id}/Images/Backdrop')
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
        Get the source image for the given episode within Emby.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the source image of.
            episode_info: The episode to get the source image of.

        Returns:
            Bytes of the source image for the given Episode. None if the
            episode does not exist in Emby, or no valid image was
            returned.
        """

        for episode in self.__get_episodes(library_name, series_info):
            emby_episode = EpisodeInfo.from_emby_info(
                episode, self._interface_id, library_name
            )

            if emby_episode == episode_info:
                emby_id = emby_episode.emby_id.get_id(
                    self._interface_id, library_name
                )

                # Get the source image for this episode
                image = self._session.get_raw(
                    f'/Items/{emby_id}/Images/Primary',
                    parameters={'Quality': 100},
                )

                # Check if valid content was returned
                if not image or b'does not have an image of type' in image:
                    log.warning(f'Episode {episode_info} has no source images')
                    return None

                return image

        log.warning(f'Episode {episode_info} not found in Emby')
        return None


    @testing_override(TestingEmbyInterface.get_series_poster)
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

        emby_id = self.__get_series_id(library_name, series_info)
        if emby_id is None:
            return None

        # Get the poster image for this Series
        content = self._session.get_raw(
            f'/Items/{emby_id}/Images/Primary',
            parameters={'Quality': 100}
        )

        # Check if valid content was returned
        if content is None or b'does not have an image of type' in content:
            log.warning(f'Series {series_info} has no poster')
            return None

        return content


    def get_series_logo(self,
            library_name: str,
            series_info: SeriesInfo,
        ) -> SourceImage:
        """
        Get the logo for the given Series within Emby.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series to get the logo of.

        Returns:
            Bytes of the logo for given series. None if the series does
            not exist in Emby, or no valid image was returned.
        """

        emby_id = self.__get_series_id(library_name, series_info)
        if emby_id is None:
            return None

        # Get the poster image for this Series
        content = self._session.get_raw(
            f'/Items/{emby_id}/Images/Logo',
            parameters={'Quality': 100}
        )

        # Check if valid content was returned
        if content is None or b'does not have an image of type' in content:
            log.warning(f'Series {series_info} has no logo')
            return None

        return content


    def get_libraries(self) -> list[str]:
        """
        Get the names of all libraries within this server.

        Returns:
            List of library names.
        """

        return list(self.libraries.keys())
