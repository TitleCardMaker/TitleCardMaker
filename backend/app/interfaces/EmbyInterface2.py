from base64 import b64encode
from datetime import datetime
from pathlib import Path
from sys import exit as sys_exit
from typing import TYPE_CHECKING, Iterator, Literal, Union, overload

from fastapi import HTTPException

from modules.Debug import Logger, log
from modules.Episode import Episode
from modules.EpisodeDataSource import (
    EpisodeDataSource,
    EpisodeDataSourceV1,
    SearchResult,
    WatchedStatus,
)
from modules.EpisodeInfo2 import EmbyEpisodeDict, EpisodeInfo, EpisodeInfoV1
from modules.MediaServer import MediaServer, MediaServerV1
from modules.SeasonPosterSet import SeasonPosterSet
from modules.SeriesInfo2 import SeriesInfoV1
from modules.StyleSet import StyleSet
from modules.Interface import Interface
from modules.MediaServer import SourceImage
from modules.SyncInterface import SyncInterface
from modules.WebInterface import WebInterface

if TYPE_CHECKING:
    from app.models.card import Card
    from app.models.episode import Episode


class EmbyInterface(MediaServer, EpisodeDataSource, SyncInterface, Interface):
    """
    This class describes an interface to an Emby media server. This is a
    type of EpisodeDataSource (e.g. interface by which Episode data can
    be retrieved), as well as a MediaServer (e.g. a server in which
    cards can be loaded into).
    """

    INTERFACE_TYPE = 'Emby'

    """Default no filesize limit for all uploaded assets"""
    DEFAULT_FILESIZE_LIMIT = None

    """Filepath to the database of each episode's loaded card characteristics"""
    LOADED_DB = 'loaded_emby.json'

    """Series ID's that can be set by Emby"""
    SERIES_IDS = ('emby_id', 'imdb_id', 'tmdb_id', 'tvdb_id')

    """Datetime format string for airdates reported by Emby"""
    AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f000000Z'

    """Range of years to query series by"""
    YEARS = ','.join(map(str, range(1960, datetime.now().year)))


    def __init__(self,
            url: str,
            api_key: str,
            username: str,
            use_ssl: bool = True,
            filesize_limit: int | None = None,
            *,
            interface_id: int = 0,
            log: Logger = log,
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
            log: Logger for all log messages.

        Raises:
            SystemExit: Invalid URL/API key provided.
        """

        # Intiialize parent classes
        super().__init__(filesize_limit)

        # Store attributes of this Interface
        self._interface_id = interface_id
        self.session = WebInterface('Emby', use_ssl, log=log)
        self.url = url[:-1] if url.endswith('/') else url
        self.__params = {'api_key': api_key}
        self.username = username

        # Authenticate with server
        try:
            response = self.session.get(
                f'{self.url}/System/Info',
                params=self.__params
            )
            if not set(response).issuperset({'ServerName', 'Version', 'Id'}):
                raise ConnectionError(f'Unable to authenticate with server')
        except Exception as e:
            log.critical(f'Cannot connect to Emby - returned error {e}')
            log.exception(f'Bad Emby connection')
            raise HTTPException(
                status_code=400,
                detail=f'Cannot connect to Emby - {e}',
            ) from e

        # Get user ID
        self.user_id = None
        if self.username:
            if (user_id := self._get_user_id(username)) is None:
                log.critical(f'Cannot identify ID of user "{username}"')
                raise HTTPException(
                    status_code=400,
                    detail=f'Cannot identify ID of user "{username}"',
                )
            self.user_id = user_id

        # Get the ID's of all libraries within this server
        self.libraries: dict[str, tuple[int]] = self._map_libraries()
        self.activate()


    def _get_user_id(self, username: str) -> str | None:
        """
        Get the User ID associated with the given username.

        Args:
            username: Username to query for.

        Returns:
            User ID hexstring associated with the given username. None
            if the username was not found.
        """

        # Query for list of all users on this server
        response: dict = self.session.get(
            f'{self.url}/Users/Query',
            params=self.__params,
        )

        # Go through returned list of users, returning when username matches
        for user in response.get('Items', []):
            if user.get('Name') == username:
                return user.get('Id')

        return None


    def _map_libraries(self) -> dict[str, tuple[int]]:
        """
        Map the libraries on this interface's Emby server.

        Returns:
            Dictionary whose keys are the names of the libraries, and
            whose values are tuples of the folder ID's for those
            libraries.
        """

        # Get all library folders
        libraries = self.session.get(
            f'{self.url}/Library/SelectableMediaFolders',
            params=self.__params
        )

        # Parse each library name into tuples of parent ID's
        return {
            lib['Name']:tuple(int(folder['Id']) for folder in lib['SubFolders'])
            for lib in libraries
        }


    @overload
    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfoV1,
            *,
            raw_obj: Literal[False] = False,
            log: Logger = log
        ) -> str | None: ...
    @overload
    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfoV1,
            *,
            raw_obj: Literal[True] = True,
            log: Logger = log
        ) -> SeriesInfoV1 | None: ...
    def __get_series_id(self,
            library_name: str,
            series_info: SeriesInfoV1,
            *,
            raw_obj: bool = False,
            log: Logger = log,
        ) -> str | SeriesInfoV1 | None:
        """
        Get the Jellyfin ID for the given series.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series being evaluated.
            raw_obj: Whether to return the raw object from the `/Items`
                endpoint (rather than just the series ID).
            log: Logger for all log messages.

        Returns:
            None if the series is not found. The Jellyfin ID of the
            series if raw_obj is False, otherwise the SeriesInfo of the
            found series.
        """

        if (not raw_obj
            and series_info.has_id('emby_id', self._interface_id, library_name)):
            # Query for this item within Jellyfin
            id_ = series_info.emby_id[self._interface_id, library_name]
            resp = self.session.get(
                f'{self.url}/Users/{self.user_id}/Items/{id_}',
                params=self.__params,
            )

            # If one item was returned, ID is still valid
            if isinstance(resp, dict) and resp.get('Id') == id_:
                return id_

            # No item found, ID must be invalid - reset and re-query
            log.trace(
                f'Emby ID ({id_}) has been dynamically re-assigned. Querying '
                f'for new one..'
            )
            del series_info.emby_id[self._interface_id, library_name]

        # Get ID of this library
        if (library_ids := self.libraries.get(library_name, None)) is None:
            log.error(f'Library "{library_name}" not found in Emby')
            return None

        # Base params for all requests
        pid_str = series_info.emby_provider_id_string
        params = {
            'Recursive': True,
            'Years': series_info.year,
            'IncludeItemTypes': 'series',
            'SearchTerm': series_info.name,
            'Fields': 'ProviderIds,PremiereDate',
        } | self.__params \
          | ({'AnyProviderIdEquals': pid_str} if pid_str else {})

        # Look for this series in each library subfolder
        for parent_id in library_ids:
            response: dict = self.session.get(
                f'{self.url}/Items',
                params=params | {'ParentId': parent_id}
            )

            # If no responses, skip
            if response['TotalRecordCount'] == 0:
                continue

            # Go through all items and match name and type, setting database IDs
            for result in response['Items']:
                if result['Type'] == 'Series':
                    # Skip results w/o premiere dates
                    if result.get('PremiereDate') is None:
                        log.debug(f'Series {result["Name"]} has no premiere date')
                        continue

                    this_series = SeriesInfoV1.from_emby_info(
                        result, self._interface_id, library_name,
                    )
                    if series_info == this_series:
                        return this_series if raw_obj else result['Id']

        log.warning(f'Series "{series_info}" was not found in Emby')
        return None


    def __get_season_id(self,
            series_id: str,
            season_number: int,
        ) -> str | None:
        """
        Get the Emby ID of the given season.

        Args:
            series_id: Emby ID of the associated series.
            season_number: Season number whose ID is being queried.

        Returns:
            The Emby ID of the season, if found. None otherwise.
        """

        response = self.session.get(
            f'{self.url}/Items',
            params={
                'recursive': True,
                'includeItemTypes': 'Season',
                'parentId': series_id,
            } | self.__params,
        )

        if not isinstance(response, dict) or not response.get('Items'):
            return None

        for season in response['Items']:
            if (season.get('SeriesId') == series_id
                and season.get('IndexNumber') == season_number):
                return season['Id']

        return None


    def __get_episodes(self,
            library_name: str,
            series_info: SeriesInfoV1,
            *,
            log: Logger = log,
        ) -> Iterator[EmbyEpisodeDict]:
        """
        Iterate through all the episodes associated with the given
        series.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.

        Yields:
            Dictionary of episode data as returned by the
            `/Shows/{id}/Episodes` API endpoint.
        """

        # Find series
        emby_id = self.__get_series_id(library_name, series_info, log=log)
        if emby_id is None:
            return None

        # Get all episodes for this series
        response = self.session.get(
            f'{self.url}/Shows/{emby_id}/Episodes',
            params=self.__params | {
                'UserId': self.user_id,
                'Fields': 'ProviderIds'
            }
        )

        # Parse each returned episode into EpisodeInfo object
        for episode in response['Items']:
            # Skip episodes without episode or season numbers
            if (episode.get('IndexNumber', None) is None
                or episode.get('ParentIndexNumber', None) is None):
                log.debug(f'Series {series_info} episode is missing index data')
                continue

            yield episode

        return None


    def get_usernames(self) -> list[str]:
        """
        Get all the usernames for this interface's Emby server.

        Returns:
            List of usernames.
        """

        return [
            user['Name'] for user in
            self.session.get(f'{self.url}/Users', params=self.__params)
        ]


    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfoV1,
            *,
            log: Logger = log,
        ) -> None:
        """
        Set the series ID's for the given SeriesInfo object.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to set the ID of.
            log: Logger for all log messages.
        """

        series = self.__get_series_id(
            library_name, series_info, raw_obj=True, log=log
        )
        if not series:
            log.warning(f'Series "{series_info}" was not found under library '
                        f'"{library_name}" in Emby')
            return None

        # Remove existing Emby ID if one exists
        if series_info.has_id('emby_id', self._interface_id, library_name):
            del series_info.emby_id[self._interface_id, library_name]

        # Add new ID's
        series_info.copy_ids(series)
        return None


    def set_episode_ids(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """
        Set the Episode ID's for the given EpisodeInfo objects.

        Args:
            library_name: Name of the library the series is under.
            series_info: Series to get the episodes of.
            infos: List of EpisodeInfo objects to set the ID's of.
            log: Logger for all log messages.
        """

        # Get all episodes for this series
        new_episode_infos = self.get_all_episodes(
            library_name, series_info, log=log
        )

        # Match to existing info
        for old_episode_info in episode_infos:
            for new_episode_info, _ in new_episode_infos:
                if (isinstance(old_episode_info, EpisodeInfo)
                    and isinstance(new_episode_info, EpisodeInfo)):
                    if old_episode_info == new_episode_info:
                        old_episode_info.copy_ids(new_episode_info, log=log)
                        break


    def query_series(self,
            query: str,
            *,
            return_all: bool = False,
            log: Logger = log,
        ) -> list[SearchResult]:
        """
        Search Emby for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            return_all: Whether to return all Series, instead of those
                returned by the given query.
            log: Logger for all log messages.

        Returns:
            List of SearchResults for the given query. Results are from
            any library.
        """

        # Perform query
        search_results = self.session.get(
            f'{self.url}/Items',
            params=self.__params | {
                'Recursive': True,
                'IncludeItemTypes': 'Series',
                'SearchTerm': '' if return_all else query,
                'Fields': 'ProviderIds,Overview,ProductionYear,Status',
                'EnableImages': True,
                'ImageTypes': 'Primary',
            },
        )

        return [
            SearchResult(
                name=result['Name'],
                year=result['ProductionYear'],
                ongoing=result.get('Status') == 'Continuing',
                overview=result.get('Overview', 'No overview available'),
                poster=f'{self.url}/Items/{result["Id"]}/Images/Primary?quality=75',
                imdb_id=result.get('ProviderIds', {}).get('Imdb'),
                tmdb_id=result.get('ProviderIds', {}).get('Tmdb'),
                tvdb_id=result.get('ProviderIds', {}).get('Tvdb'),
                tvrage_id=result.get('ProviderIds', {}).get('TvRage'),
            )
            for result in search_results['Items']
            if 'ProductionYear' in result
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

        # Get all library folders
        libraries = self.session.get(
            f'{self.url}/Library/SelectableMediaFolders',
            params=self.__params
        )

        # Inner function on whether to include this library in the return
        def include_library(emby_library: str) -> bool:
            if not filter_libraries:
                return True
            return emby_library in filter_libraries

        # Parse each library name into tuples of parent ID's
        return {
            lib['Name']: list(folder['Path'] for folder in lib['SubFolders'])
            for lib in libraries
            if include_library(lib['Name'])
        }


    def get_all_series(self,
            required_libraries: list[str] = [],
            excluded_libraries: list[str] = [],
            required_tags: list[str] = [],
            excluded_tags: list[str] = [],
            *,
            log: Logger = log,
        ) -> list[tuple[SeriesInfoV1, str]]:
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
            log: Logger for all log messages.

        Returns:
            List of tuples of the filtered series info and their
            corresponding library names.
        """

        # Temporarily override request timeout to 240s (4 min)
        self.REQUEST_TIMEOUT = 240

        # Base params for all queries
        params = {
            'Recursive': True,
            'IncludeItemTypes': 'series',
            'Fields': 'ProviderIds,PremiereDate',
        } | self.__params

        # Get excluded series ID's if excluding by tags
        if excluded_tags:
            # Get all items (series) for any of the excluded tags
            response = self.session.get(
                f'{self.url}/Items',
                params=params | {'Tags': '|'.join(excluded_tags)},
            )
            params |= {
                'ExcludeItemIds': ','.join(
                    map(str, [series['Id'] for series in response['Items']])
                )
            }

        # Also filter by tags if any were provided
        if required_tags:
            params |= {'Tags': '|'.join(required_tags)}

        # Go through each library in this server
        all_series: list[tuple[SeriesInfoV1, str]] = []
        for library, library_ids in self.libraries.items():
            # Filter by library
            if ((required_libraries and library not in required_libraries)
                or (excluded_libraries and library in excluded_libraries)):
                continue

            # Go through every subfolder (the parent ID) in this library
            for parent_id in library_ids:
                # Get all items (series) in this subfolder
                response = self.session.get(
                    f'{self.url}/Items',
                    params=params | {'ParentId': parent_id, 'Years': self.YEARS}
                )

                # Process each returned Series
                for series in response['Items']:
                    try:                     
                        if (premiere := series.get('PremiereDate')) is None:
                            log.error(f'Series {series["Name"]} has no premiere date')
                            continue
                        datetime.strptime(premiere, self.AIRDATE_FORMAT).year

                        all_series.append((
                            SeriesInfoV1.from_emby_info(
                                series, self._interface_id, library,
                            ),
                            library
                        ))
                    except ValueError:
                        log.error(f'Series {series["Name"]} is missing a year')
                        continue

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


    def get_all_episodes(self,
            library_name: str,
            series_info: SeriesInfoV1,
            *,
            log: Logger = log,
        ) -> list[tuple[EpisodeInfo, WatchedStatus]]:
        """
        Gets all episode info for the given series. Only episodes that
        have already aired are returned.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to get the episodes of.
            log: Logger for all log messages.

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
                    self._interface_id,
                    library_name,
                    episode.get('UserData', {}).get('Played')
                )
            )
            for episode in
            self.__get_episodes(library_name, series_info, log=log)
        ]


    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episodes: list['Episode'],
            *,
            log: Logger = log,
        ) -> bool:
        """
        Modify the Episodes' watched attribute according to the watched
        status of the corresponding episodes within Emby.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episodes: List of Episode objects to update.
            log: Logger for all log messages.

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
                    self._interface_id,
                    library_name,
                    episode.get('UserData', {}).get('Played'),
                )
            )
            for episode in
            self.__get_episodes(library_name, series_info, log=log)
        ]

        # Update watched statuses of all Episodes
        changed = False
        for episode in episodes:
            episode_info = episode.as_episode_info
            for emby_episode, watched_status in emby_episodes:
                if episode_info == emby_episode:
                    changed |= episode.add_watched_status(
                        watched_status, log=log,
                    )
                    break

        return changed


    def load_title_cards(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episode_and_cards: Union[
                list[tuple['Episode', 'Card']],
                list[tuple['Episode', 'Card', str]]
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
        # Match each episode 
        else:
            for emby_ep in self.__get_episodes(library_name, series_info, log=log):
                # Create EpisodeInfo object for this episode
                emby_info = EpisodeInfo.from_emby_info(
                    emby_ep, self._interface_id, library_name
                )
                emby_id = emby_info.emby_id[self._interface_id, library_name]

                for episode, card, *_ in episode_and_cards:
                    if episode.as_episode_info == emby_info:
                        matched.append((episode, card, emby_id))
                        break

        # Load each episode and card
        loaded = []
        for episode, card, emby_id in matched:
            if (image := self.compress_image(card.card_file, log=log)) is None:
                continue

            # Submit POST request for image upload on Base64 encoded image
            card_base64 = b64encode(image.read_bytes())
            try:
                self.session.session.post(
                    url=f'{self.url}/Items/{emby_id}/Images/Primary',
                    headers={'Content-Type': 'image/jpeg'},
                    params=self.__params,
                    data=card_base64,
                )
                loaded.append((episode, card))
            except Exception:
                log.exception(
                    f'Unable to upload {image.resolve()} to {series_info}'
                )
        # for emby_ep in self.__get_episodes(library_name, series_info, log=log):
        #     # Create EpisodeInfo object for this episode
        #     emby_info = EpisodeInfo.from_emby_info(
        #         emby_ep, self._interface_id, library_name
        #     )
        #     emby_id = emby_info.emby_id[self._interface_id, library_name]

        #     # Iterate through all the given episodes/cards, upload to match
        #     for episode, card, *uid in episode_and_cards:
        #         if episode.as_episode_info == emby_info:
        #             # Shrink image if necessary, skip if cannot be compressed
        #             if (image := self.compress_image(card.card_file, log=log)) is None:
        #                 continue

        #             # Submit POST request for image upload on Base64 encoded image
        #             card_base64 = b64encode(image.read_bytes())
        #             try:
        #                 self.session.session.post(
        #                     url=f'{self.url}/Items/{emby_id}/Images/Primary',
        #                     headers={'Content-Type': 'image/jpeg'},
        #                     params=self.__params,
        #                     data=card_base64,
        #                 )
        #                 loaded.append((episode, card))
        #             except Exception:
        #                 log.exception(f'Unable to upload {image.resolve()} to '
        #                               f'{series_info}')
        #             break

        # Log load operations to user
        if loaded:
            log.info(f'Loaded {len(loaded)} cards for "{series_info}"')

        return loaded


    def load_season_posters(self,
            library_name: str,
            series_info: SeriesInfoV1,
            posters: dict[int, str | Path],
            *,
            log: Logger = log,
        ) -> None:
        """
        Load the given season posters into Emby.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            posters: Dictionary of season numbers to poster URLs or
                files to upload.
            log: Logger for all log messages.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return None

        # Load each episode and card
        for season_number, image in posters.items():
            if (sid := self.__get_season_id(series_id, season_number)) is None:
                log.warning(f'Season {season_number} not found')
                continue

            # Shrink image if necessary, skip if cannot be compressed
            if (isinstance(image, Path)
                and (image := self.compress_image(image, log=log)) is None):
                continue

            # Download or read image
            if isinstance(image, str):
                image_bytes = WebInterface.download_image_raw(image, log=log)
                if image_bytes is None:
                    continue
            else:
                image_bytes = image.read_bytes()
            image_base64 = b64encode(image_bytes)

            # Submit POST request for image upload on Base64 encoded image
            try:
                self.session.session.post(
                    url=f'{self.url}/Items/{sid}/Images/Primary',
                    headers={'Content-Type': 'image/jpeg'},
                    params=self.__params,
                    data=image_base64,
                )
                log.debug(
                    f'{series_info} loaded poster into season {season_number}'
                )
            except Exception:
                log.exception(f'Unable to upload {image} to {series_info}')
                continue

        return None


    def load_series_poster(self,
            library_name: str,
            series_info: SeriesInfoV1,
            image: str | Path,
            *,
            log: Logger = log
        ) -> None:
        """
        Load the given series poster into Emby.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            image: URL or Path to the file to upload.
            log: Logger for all log messages.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return None

        # Shrink image if necessary, skip if cannot be compressed
        if (isinstance(image, Path)
            and (image := self.compress_image(image, log=log)) is None):
            return None

        # Download or read image
        if isinstance(image, str):
            image_bytes = WebInterface.download_image_raw(image, log=log)
            if image_bytes is None:
                return None
        else:
            image_bytes = image.read_bytes()
        image_base64 = b64encode(image_bytes)

        # Submit POST request for image upload on Base64 encoded image
        try:
            self.session.session.post(
                url=f'{self.url}/Items/{series_id}/Images/Primary',
                headers={'Content-Type': 'image/jpeg'},
                params=self.__params,
                data=image_base64,
            )
            log.debug(f'{series_info} loaded poster')
        except Exception:
            log.exception(f'Unable to upload {image} to {series_info}')

        return None


    def load_series_background(self,
            library_name: str,
            series_info: SeriesInfoV1,
            image: str | Path,
            *,
            log: Logger = log
        ) -> None:
        """
        Load the given series background image into Emby.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            image: URL or Path to the file to upload.
            log: Logger for all log messages.
        """

        # Find this series
        series_id = self.__get_series_id(library_name, series_info, log=log)
        if series_id is None:
            return None

        # Shrink image if necessary, skip if cannot be compressed
        if (isinstance(image, Path)
            and (image := self.compress_image(image, log=log)) is None):
            return None

        # Download or read image
        if isinstance(image, str):
            image_bytes = WebInterface.download_image_raw(image, log=log)
            if image_bytes is None:
                return None
        else:
            image_bytes = image.read_bytes()
        image_base64 = b64encode(image_bytes)

        # Submit POST request for image upload on Base64 encoded image
        try:
            self.session.session.post(
                url=f'{self.url}/Items/{series_id}/Images/Backdrop',
                headers={'Content-Type': 'image/jpeg'},
                params=self.__params,
                data=image_base64,
            )
            log.debug(f'{series_info} loaded backdrop')
        except Exception:
            log.exception(f'Unable to upload {image} to {series_info}')

        return None


    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episode_info: EpisodeInfo,
            *,
            log: Logger = log,
        ) -> bytes | None:
        """
        Get the source image for the given episode within Emby.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the source image of.
            episode_info: The episode to get the source image of.
            log: Logger for all log messages.

        Returns:
            Bytes of the source image for the given Episode. None if the
            episode does not exist in Emby, or no valid image was
            returned.
        """

        for episode in self.__get_episodes(library_name, series_info, log=log):
            emby_episode = EpisodeInfo.from_emby_info(
                episode, self._interface_id, library_name
            )
            if emby_episode == episode_info:
                emby_id = emby_episode.emby_id[self._interface_id, library_name]

                # Get the source image for this episode
                response = self.session.session.get(
                    f'{self.url}/Items/{emby_id}/Images/Primary',
                    params={'Quality': 100} | self.__params,
                ).content

                # Check if valid content was returned
                if b'does not have an image of type' in response:
                    log.warning(f'Episode {episode_info} has no source images')
                    return None

                return response

        log.warning(f'Episode {episode_info} not found in Emby')
        return None


    def get_series_poster(self,
            library_name: str,
            series_info: SeriesInfoV1,
            *,
            log: Logger = log,
        ) -> SourceImage:
        """
        Get the poster for the given Series.

        Args:
            series_info: The series to get the poster of.
            log: Logger for all log messages.

        Returns:
            URL to the poster for the given series. None if the library,
            series, or thumbnail cannot be found.
        """

        emby_id = self.__get_series_id(library_name, series_info, log=log)
        if emby_id is None:
            return None

        # Get the poster image for this Series
        response = self.session.session.get(
            f'{self.url}/Items/{emby_id}/Images/Primary',
            params={'Quality': 100} | self.__params,
        ).content

        # Check if valid content was returned
        if b'does not have an image of type' in response:
            log.warning(f'Series {series_info} has no poster')
            return None

        return response


    def get_series_logo(self,
            library_name: str,
            series_info: SeriesInfoV1,
            *,
            log: Logger = log,
        ) -> SourceImage:
        """
        Get the logo for the given Series within Emby.

        Args:
            library_name: Name of the library containing the series.
            series_info: The series to get the logo of.
            log: Logger for all log messages.

        Returns:
            Bytes of the logo for given series. None if the series does
            not exist in Emby, or no valid image was returned.
        """

        emby_id = self.__get_series_id(library_name, series_info, log=log)
        if emby_id is None:
            return None

        # Get the source image for this episode
        response = self.session.session.get(
            f'{self.url}/Items/{emby_id}/Images/Logo',
            params={'Quality': 100} | self.__params,
        ).content

        # Check if valid content was returned
        if b'does not have an image of type' in response:
            log.warning(f'Series {series_info} has no logo')
            return None

        return response


    def get_libraries(self) -> list[str]:
        """
        Get the names of all libraries within this server.

        Returns:
            List of library names.
        """

        return list(self.libraries)


class EmbyInterfaceV1(EpisodeDataSourceV1, MediaServerV1, SyncInterface):
    """
    This class describes an interface to an Emby media server. This is a
    type of EpisodeDataSource (e.g. interface by which Episode data can
    be retrieved), as well as a MediaServer (e.g. a server in which
    cards can be loaded into).
    """

    """Default no filesize limit for all uploaded assets"""
    DEFAULT_FILESIZE_LIMIT = None

    """Filepath to the database of each episode's loaded card characteristics"""
    LOADED_DB = 'loaded_emby.json'

    """Series ID's that can be set by Emby"""
    SERIES_IDS = ('emby_id', 'imdb_id', 'tmdb_id', 'tvdb_id')

    """Datetime format string for airdates reported by Emby"""
    AIRDATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f000000Z'

    """Range of years to query series by"""
    YEAR_RANGE = range(1960, datetime.now().year)


    def __init__(self,
            url: str,
            api_key: str,
            username: str,
            verify_ssl: bool = True,
            filesize_limit: int | None = None,
        ) -> None:
        """
        Construct a new instance of an interface to an Emby server.

        Args:
            url: The API url communicating with Emby.
            api_key: The API key for API requests.
            username: Username of the Emby account to get watch statuses
                of.
            verify_ssl: Whether to verify SSL requests.
            filesize_limit: Number of bytes to limit a single file to
                during upload.

        Raises:
            SystemExit: Invalid URL/API key provided.
        """

        # Intiialize parent classes
        super().__init__(filesize_limit)

        # Store attributes of this Interface
        self.session = WebInterface('Emby', verify_ssl)
        self.info_set = global_objects.info_set
        self.url = url[:-1] if url.endswith('/') else url
        self.__params = {'api_key': api_key}
        self.username = username

        # Authenticate with server
        try:
            response = self.session.get(
                f'{self.url}/System/Info',
                params=self.__params
            )
            if not set(response).issuperset({'ServerName', 'Version', 'Id'}):
                raise ConnectionError(f'Unable to authenticate with server')
        except Exception as exc: # pylint: disable=broad-except
            log.critical(f'Cannot connect to Emby - returned error {exc}')
            log.exception(f'Bad Emby connection')
            sys_exit(1)

        # Get user ID
        if (user_id := self._get_user_id(username)) is None:
            log.critical(f'Cannot identify ID of user "{username}"')
            sys_exit(1)
        else:
            self.user_id = user_id

        # Get the ID's of all libraries within this server
        self.libraries = self._map_libraries()


    def _get_user_id(self, username: str) -> str | None:
        """
        Get the User ID associated with the given username.

        Args:
            username: Username to query for.

        Returns:
            User ID hexstring associated with the given username. None
            if the  username was not found.
        """

        # Query for list of all users on this server
        response = self.session.get(
            f'{self.url}/Users/Query',
            params=self.__params,
        )

        # Go through returned list of users, returning when username matches
        for user in response.get('Items'):
            if user.get('Name') == username:
                return user.get('Id')

        return None


    def _map_libraries(self) -> dict[str, tuple[int]]:
        """
        Map the libraries on this interface's Emby server.

        Returns:
            Dictionary whose keys are the names of the libraries, and
            whose values are tuples of the folder ID's for those
            libraries.
        """

        # Get all library folders
        libraries = self.session.get(
            f'{self.url}/Library/SelectableMediaFolders',
            params=self.__params
        )

        # Parse each library name into tuples of parent ID's
        return {
            lib['Name']:tuple(int(folder['Id']) for folder in lib['SubFolders'])
            for lib in libraries
        }


    def get_usernames(self) -> list[str]:
        """
        Get all the usernames for this interface's Emby server.

        Returns:
            List of usernames.
        """

        users = self.session.get(
            f'{self.url}/Users',
            params=self.__params
        )

        return [user['Name'] for user in users]


    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfoV1,
        ) ->None:
        """
        Set the series ID's for the given SeriesInfo object.

        Args:
            library_name: The name of the library containing the series.
            series_info: Series to set the ID of.
        """

        # If all possible ID's are defined
        if series_info.has_ids(*self.SERIES_IDS):
            return None

        # If library not mapped, error and exit
        if (library_ids := self.libraries.get(library_name)) is None:
            log.error(f'Library "{library_name}" not found in Emby')
            return None

        # Generate provider ID query string
        ids = []
        if series_info.has_id('imdb_id'):
            ids += [f'imdb.{series_info.imdb_id}']
        if series_info.has_id('tmdb_id'):
            ids += [f'tmdb.{series_info.tmdb_id}']
        if series_info.has_id('tvdb_id'):
            ids += [f'tvdb.{series_info.tvdb_id}']
        provider_id_str = ','.join(ids)

        # Base params for all requests
        params = {
            'Recursive': True,
            'Years': series_info.year,
            'IncludeItemTypes': 'series',
            'SearchTerm': series_info.name,
            'Fields': 'ProviderIds',
        } | self.__params \
          |({'AnyProviderIdEquals': provider_id_str} if provider_id_str else {})

        # Look for this series in each library subfolder
        for parent_id in library_ids:
            response = self.session.get(
                f'{self.url}/Items',
                params=params | {'ParentId': parent_id}
            )

            # If no responses, skip
            if response['TotalRecordCount'] == 0:
                continue

            # Go through all items and match name and type, setting database IDs
            for result in response['Items']:
                if (result['Type'] == 'Series'
                    and series_info.matches(result['Name'])):
                    ids = result.get('ProviderIds', {})
                    # No MediaInfoSet, set directly
                    if self.info_set is None:
                        series_info.set_emby_id(result['Id'])
                        series_info.set_imdb_id(ids.get('IMDB', None))
                        series_info.set_tmdb_id(ids.get('Tmdb', None))
                        series_info.set_tvdb_id(ids.get('Tvdb', None))
                    # Set using global MediaInfoSet
                    else:
                        self.info_set.set_emby_id(series_info, result['Id'])
                        self.info_set.set_emby_id(
                            series_info, ids.get('IMDb', None)
                        )
                        self.info_set.set_tmdb_id(
                            series_info, ids.get('Tmdb', None)
                        )
                        self.info_set.set_tmdb_id(
                            series_info, ids.get('Tvdb', None)
                        )

                    return None

        # Not found on server
        log.warning(f'Series "{series_info}" was not found under library '
                    f'"{library_name}" in Emby')
        return None


    def set_episode_ids(self,
            library_name: str | None,
            series_info: SeriesInfoV1,
            episode_infos: list[EpisodeInfoV1],
            *,
            inplace: bool = False,
        ) -> None:
        """
        Set the Episode ID's for the given EpisodeInfo objects.

        Args:
            series_info: Series to get the episodes of.
            infos: List of EpisodeInfo objects to set the ID's of.
        """

        if inplace:
            self.get_all_episodes(library_name, series_info, episode_infos)
        else:
            self.get_all_episodes(library_name, series_info)


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

        # Get all library folders
        libraries = self.session.get(
            f'{self.url}/Library/SelectableMediaFolders',
            params=self.__params
        )

        # Inner function on whether to include this library in the return
        def include_library(emby_library) -> bool:
            if len(filter_libraries) == 0:
                return True
            return emby_library in filter_libraries

        # Parse each library name into tuples of parent ID's
        return {
            lib['Name']: list(folder['Path'] for folder in lib['SubFolders'])
            for lib in libraries
            if include_library(lib['Name'])
        }


    def get_all_series(self,
            filter_libraries: list[str] = [],
            required_tags: list[str] = [],
        ) -> list[tuple[SeriesInfoV1, str, str]]:
        """
        Get all series within Emby, as filtered by the given libraries.

        Args:
            filter_libraries: Optional list of library names to filter
                returned list by. If provided, only series that are
                within a given library are returned.
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

        # Base params for all queries
        params = {
            'Recursive': True,
            'IncludeItemTypes': 'series',
            'Fields': 'ProviderIds,Path',
        } | self.__params

        # Also filter by tags if any were provided
        if len(required_tags) > 0:
            params |= {'Tags': '|'.join(required_tags)}

        # Go through each library in this server
        all_series = []
        for library, library_ids in self.libraries.items():
            # If filtering, skip unspecified libraries
            if filter_libraries and library not in filter_libraries:
                continue

            # Go through every subfolder (the parent ID) in this library
            for parent_id in library_ids:
                # Have to query year by year, for SOME stupid reason...
                for year in self.YEAR_RANGE:
                    # Get all items (series) in this subfolder for this year
                    response = self.session.get(
                        f'{self.url}/Items',
                        params=params | {'ParentId': parent_id, 'Years': year}
                    )

                    for series in response['Items']:
                        series_info = SeriesInfoV1(series['Name'], year,
                                                 emby_id=series['Id'])
                        all_series.append((series_info, series['Path'],library))

        # Reset request timeout
        self.REQUEST_TIMEOUT = 30

        return all_series


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
            episode_infos: List of EpisodeInfos to modify.

        Returns:
            List of EpisodeInfo objects for this series.
        """

        # If series has no Emby ID, cannot query episodes
        if not series_info.has_id('emby_id'):
            log.warning(f'Series not found in Emby {series_info!r}')
            return []

        # Get all episodes for this series
        response = self.session.get(
            f'{self.url}/Shows/{series_info.emby_id}/Episodes',
            params={'Fields': 'ProviderIds'} | self.__params
        )

        # Parse each returned episode into EpisodeInfo object
        all_episodes = []
        for episode in response['Items']:
            # Parse airdate for this episode
            airdate = None
            try:
                airdate = datetime.strptime(episode['PremiereDate'],
                                            self.AIRDATE_FORMAT)
            except ValueError:
                log.exception(f'Cannot parse airdate')
                log.debug(f'Episode data: {episode}')

            # Create new EpisodeInfo via global MediaInfoSet object
            if episode_infos is None:
                episode_info = self.info_set.get_episode_info(
                    series_info,
                    episode['Name'],
                    episode['ParentIndexNumber'],
                    episode['IndexNumber'],
                    emby_id=int(episode.get('Id')),
                    imdb_id=episode['ProviderIds'].get('Imdb'),
                    tmdb_id=episode['ProviderIds'].get('Tmdb'),
                    tvdb_id=episode['ProviderIds'].get('Tvdb'),
                    tvrage_id=episode['ProviderIds'].get('TvRage'),
                    airdate=airdate,
                    title_match=True,
                    queried_emby=True,
                )

                # Add to list
                if episode_info is not None:
                    all_episodes.append(episode_info)
            # If updating existing infos, match by index
            else:
                tmp_ei = (episode['ParentIndexNumber'], episode['IndexNumber'])
                for episode_info in episode_infos:
                    # Index match, update ID's
                    if episode_info == tmp_ei:
                        ep_ids = episode['ProviderIds']
                        episode_info.set_emby_id(episode.get('Id'))
                        episode_info.set_imdb_id(ep_ids.get('Imdb'))
                        episode_info.set_tmdb_id(ep_ids.get('Tmdb'))
                        episode_info.set_tvdb_id(ep_ids.get('Tvdb'))
                        episode_info.set_tvrage_id(ep_ids.get('TvRage'))
                        all_episodes.append(episode_info)
                        break

            # Add to list
            if episode_info is not None:
                all_episodes.append(episode_info)

        return all_episodes


    def has_series(self,
            library_name: str,
            series_info: SeriesInfoV1,
        ) -> bool:
        """
        Determine whether the given series is present within Emby.

        Args:
            library_name: The name of the library potentially containing
                the series.
            series_info: The series to being evaluated.

        Returns:
            True if the series is present within Emby. False otherwise.
        """

        return series_info.has_id('emby_id')


    def update_watched_statuses(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episode_map: dict[str, Episode],
            style_set: 'StyleSet',
        ) -> None:
        """
        Modify the Episode objects according to the watched status of
        the corresponding episodes within Emby, and the spoil status of
        the object. If a loaded card needs its spoiler status changed,
        the card is deleted and the loaded map is updated to reload that
        card.

        Args:
            library_name: The name of the library containing the series.
            series_info: The series to update.
            episode_map: Dictionary of episode keys to Episode objects
                to modify.
            style_set: StyleSet object to update the style of the
                Episodes with.
        """

        # If no episodes, or series has no Emby ID, exit
        if len(episode_map) == 0 or not series_info.has_id('emby_id'):
            return None

        # Get current loaded characteristics of the series
        loaded_series = self.loaded_db.search(
            self._get_condition(library_name, series_info)
        )

        # Query for all episodes of this series
        response = self.session.get(
            f'{self.url}/Shows/{series_info.emby_id}/Episodes',
            params={'UserId': self.user_id} | self.__params
        )

        # Go through each episode in Emby, update Episode status/card
        for emby_episode in response['Items']:
            # Skip if this episode isn't in TCM
            season_number = emby_episode['ParentIndexNumber']
            ep_key = f'{season_number}-{emby_episode["IndexNumber"]}'
            if not (episode := episode_map.get(ep_key)):
                continue

            # Set Episode watch/spoil statuses
            episode.update_statuses(emby_episode['UserData']['Played'], style_set)

            # Get characteristics of this Episode's loaded card
            details = self._get_loaded_episode(loaded_series, episode)
            loaded = details is not None
            spoiler_status = details['spoiler'] if loaded else None

            # Delete and reset card if current spoiler type doesn't match
            delete_and_reset = ((episode.spoil_type != spoiler_status)
                                and bool(spoiler_status))

            # Delete card, reset size in loaded map to force reload
            if delete_and_reset and loaded:
                episode.delete_card(reason='updating style')
                self.loaded_db.update(
                    {'filesize': 0},
                    self._get_condition(library_name, series_info, episode)
                )

        return None


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

        # If series has no Emby ID, cannot set title cards
        if not series_info.has_id('emby_id'):
            return None

        # Filter loaded cards
        filtered_episodes = self._filter_loaded_cards(
            library_name, series_info, episode_map
        )

        # If no episodes remain, exit
        if len(filtered_episodes) == 0:
            return None

        # Go through each remaining episode and load the card
        loaded_count = 0
        for episode in filtered_episodes.values():
            # Skip episodes without Emby ID's (e.g. not in Emby)
            if (emby_id := episode.episode_info.emby_id) is None:
                continue

            # Shrink image if necessary, skip if cannot be compressed
            if (card := self.compress_image(episode.destination)) is None:
                continue

            # Image content must be Base64-encoded
            card_base64 = b64encode(card.read_bytes())

            # Submit POST request for image upload
            try:
                self.session.session.post(
                    url=f'{self.url}/Items/{emby_id}/Images/Primary',
                    headers={'Content-Type': 'image/jpeg'},
                    params=self.__params,
                    data=card_base64,
                )
                loaded_count += 1
            except Exception as e:
                log.exception(f'Unable to upload {card.resolve()} to '
                              f'{series_info}', e)
                continue

            # Update loaded database for this episode
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


    def set_season_posters(self,
            library_name: str,
            series_info: SeriesInfoV1,
            season_poster_set: SeasonPosterSet,
        ) -> None:
        """
        Set the season posters from the given set within Emby.

        Args:
            library_name: Name of the library containing the series to
                update.
            series_info: The series to update.
            season_poster_set: SeasonPosterSet with season posters to
                set.
        """

        return None


    def get_source_image(self,
            library_name: str,
            series_info: SeriesInfoV1,
            episode_info: EpisodeInfoV1,
        ) -> SourceImage:
        """
        Get the source image given episode within Emby.

        Args:
            library_name: Name of the library the series is under.
            series_info: The series to get the source image of.
            episode_info: The episode to get the source image of.

        Returns:
            Bytes of the source image for the given Episode. None if the
            episode does not exist in Emby, or no valid image was
            returned.
        """

        # If series has no Emby ID, cannot query episodes
        if not episode_info.has_id('emby_id'):
            log.warning(f'Episode {episode_info} not found in Emby')
            return None

        # Get the source image for this episode
        response = self.session.session.get(
            f'{self.url}/Items/{episode_info.emby_id}/Images/Primary',
            params={'Quality': 100} | self.__params,
        ).content

        # Check if valid content was returned
        if b'does not have an image of type' in response:
            log.warning(f'Episode {episode_info} has no source images')
            return None

        return response


    def get_libraries(self) -> list[str]:
        """
        Get the names of all libraries within this server.

        Returns:
            List of library names.
        """

        return list(self.libraries)

