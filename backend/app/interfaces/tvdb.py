from datetime import datetime, timedelta
from typing import Annotated, Any, ClassVar
from urllib.parse import quote as url_quote, urlencode

from fastapi import HTTPException
from pydantic import ValidationError

from app.interfaces.base import (
    EpisodeDataSource,
    Interface,
    SearchResult,
    WatchedStatus,
)
from app.interfaces.web import WebInterface
from app.info.episode import EpisodeInfo
from app.info.series import SeriesInfo
from app.interfaces.schemas.tvdb import (
    ArtType,
    ArtworkExtendedRecord,
    Authentication,
    EpisodeBaseRecord,
    EpisodeExtendedResponse,
    EpisodeTranslationResponse,
    LanguageCode,
    RemoteID,
    RemoteIDSearchResult,
    SearchResultResponse,
    SeasonOrder,
    SeasonTranslationResponse,
    SeriesArtworkResponse,
    SeriesEpisodeResponse,
    SeriesExtendedRecord,
)
from app.interfaces.testing import testing_override
from app.logging.logger import Logger, log


class TVDbInterface(EpisodeDataSource, WebInterface, Interface):
    """
    This class defines an interface to TheTV Database (TVDb). Once
    initialized  with a valid API key, the primary purpose of this class
    is to communicate with TVDb.
    """

    INTERFACE_TYPE: Annotated[
        ClassVar[str],
        'Name of this type of Interface'
    ] = 'TVDb'

    ARTWORK_TYPES: Annotated[
        ClassVar[dict[ArtType, int]],
        'TVDb ID mappings for each type of artwork'
    ] = {
        'banner': 1,
        'poster': 2,
        'background': 3,
        'icon': 5,
        'season': 7,
        'clearart': 22,
        'logo': 23
    }

    __ROOT_API_URL: Annotated[
        ClassVar[str],
        'Root URL of all API requests'
    ] = 'https://api4.thetvdb.com/v4'

    __TOKEN_DURATION: Annotated[
        ClassVar[timedelta],
        'Auth tokens are valid for 1 month per the API docs: '
        '(https://thetvdb.github.io/v4-api/). Refresh every 25 days to be sure'
    ] = timedelta(days=25)


    def __init__(self,
            api_key: str,
            episode_ordering: SeasonOrder = 'default',
            include_movies: bool = False,
            minimum_source_width: int = 0,
            minimum_source_height: int = 0,
            language_priority: list[LanguageCode] = ['eng'],
            *,
            interface_id: int = 0,
            log: Logger = log,
        ) -> None:
        """
        Construct a new instance of an interface to TVDb.

        Args:
            api_key: The API key to communicate with TVDb.
            episode_ordering: Which order of episode data to query.
            include_movies: Whether to include episodes which are movies
                in the episode data queries of this connection.
            minimum_source_width: Minimum width (in pixels) required for
                source images.
            minimum_source_height: Minimum height (in pixels) required
                for source images.
            language_priority: Priority which artwork should be
                evaluated at.
            interface_id: Interface ID of this interface.
            log: Logger for all log messages.

        Raises:
            HTTPException (401): The API key is invalid.
        """

        super().__init__('TVDb', log=log)

        self.minimum_source_width = minimum_source_width
        self.minimum_source_height = minimum_source_height
        self.language_priority = language_priority
        self._interface_id = interface_id
        self._order_type = episode_ordering
        self._include_movies = include_movies

        # Authenticate with TVDb, generate session token
        self.__api_key = api_key
        self.__token_expiration: datetime | None = None
        self.__initialize_token(log=log) # This will initialize the interface


    def __generate_login_token(self, api_key: str, *, log: Logger = log) -> str:
        """
        Generate a login token which can be used for API requests with
        the given key.

        Args:
            api_key: The API key to communicate with TVDb.
            log: Logger for all log messages.

        Returns:
            Token which can be used in a simple OAuth `Bearer` field
            for API requests.

        Raises:
            Raises: ValueError: The API key is invalid or no auth token
                was returned.
        """

        # Submit login request
        response = self.session.post(
            url=f'{self.__ROOT_API_URL}/login',
            json={'apikey': api_key},
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            timeout=30,
        )

        try:
            auth = Authentication.model_validate(response.json())
        except ValidationError:
            log.debug(
                f'API login failed [{response.status_code}] - {response.text}'
            )
            raise ValueError('Unable to generate TVDb API token')

        if auth.status == 'failure' or auth.data is None or not auth.data.token:
            log.debug((
                f'Authentication failed [{response.status_code}] - '
                f'{auth.message or response.text}'
            ))
            raise ValueError('API key is invalid')

        return auth.data.token

    @testing_override(lambda *args, **kwargs: None)
    def __initialize_token(self, *, log: Logger = log) -> None:
        """
        Initialize the session token for communicating with TVDb. This
        can also re-initialize an expired session. Once initialized,
        this sets this object's session headers to use the OAuth2 bearer
        token.

        Args:
            log: Logger for all log messages.

        Raises:
            HTTPException (401): The API key is invalid.
        """

        # Token has not yet expired, skip
        if (self.__token_expiration
            and datetime.now() > self.__token_expiration):
            return None

        # Token has expired, regenerate and update expiration
        try:
            token = self.__generate_login_token(self.__api_key, log=log)
            self.__token_expiration = datetime.now() + self.__TOKEN_DURATION
            self.activate()
        except ValueError:
            log.exception('Failed to authenticate with TVDb')
            self.active = False
            raise HTTPException(
                status_code=401,
                detail='Invalid API key',
            )

        # Set default headers on this object's session with new token
        self.session.headers = { # Pulled from tvdb_v4_official
            'Authorization': f'Bearer {token}',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }


    def __find_by_remote_id(self,
            info: SeriesInfo | EpisodeInfo,
            /,
        ) -> int | None:
        """
        Find the TVDb ID of the given Series or Episode by searching
        for any associated IMDb or TMDb ID.

        Args:
            info: Series or Episode to search for.

        Returns:
            TVDb ID of the given Series or Episode. None if it cannot be
            found.
        """

        # Can only search by IMDb or TMDb ID
        ids: list[str] = []
        if info.imdb_id:
            ids.append(str(info.imdb_id))
        if info.tmdb_id:
            ids.append(str(info.tmdb_id))

        for id_ in ids:
            # Query API for each ID, and then validate the response
            try:
                response = RemoteIDSearchResult.model_validate(
                    self.get(f'{self.__ROOT_API_URL}/search/remoteid/{id_}')
                )
            # Validation error, skip
            except ValidationError:
                continue

            # No data, skip
            if not response.data:
                continue

            # If provided a Series, return first series
            if isinstance(info, SeriesInfo):
                for result in response.data:
                    if result.series:
                        return result.series.id
            # If provided an Episode, return first episode
            elif isinstance(info, EpisodeInfo):
                for result in response.data:
                    if result.episode:
                        return result.episode.id

        return None


    def __get_series_id(self, series_info: SeriesInfo) -> int | None:
        """
        Get the TVDb ID of the given series. This looks up by database
        ID, if present, otherwise series name and year.

        Args:
            series_info: Series to search for.

        Returns:
            TVDb ID of the series. None if it cannot be found.
        """

        # If Series already has a TVDb ID, return
        if series_info.tvdb_id:
            return series_info.tvdb_id

        # Attempt to match by remote ID
        if (id_ := self.__find_by_remote_id(series_info)):
            return id_

        # Search by name and year
        params = urlencode({
            'query': series_info.name,
            'year': series_info.year,
            'type': 'series'
        })

        try:
            response = SearchResultResponse.model_validate(
                self.get(f'{self.__ROOT_API_URL}/search?{params}')
            )
        except ValidationError:
            log.exception(f'Failed to query series {series_info} on TVDb')
            return None

        if response.data and response.data[0].tvdb_id:
            return response.data[0].tvdb_id

        return None


    def __get_episode_id(self,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            log: Logger = log,
        ) -> int | None:
        """
        Find the TVDb ID of the indicated episode.

        Args:
            series_info: Series associated with the given episode.
            episode_info: Episode whose ID is being queried.
            log: Logger for all log messages.

        Returns:
            TVDb ID of the indicated episode. None if the episode cannot
            be found.
        """

        if episode_info.tvdb_id:
            return episode_info.tvdb_id

        # Attempt to match by remote ID
        if (id_ := self.__find_by_remote_id(episode_info)):
            return id_

        # Cannot search by episode title; not supported via /search
        # endpoint

        # If series has no TVDb ID, cannot identify episode
        if not (tvdb_id := self.__get_series_id(series_info)):
            return None

        # Generate query URL
        params = urlencode({
            'season': episode_info.season_number,
            'episodeNumber': episode_info.episode_number,
        })

        # Make request
        try:
            response = SeriesEpisodeResponse.model_validate(
                self.get((
                    f'{self.__ROOT_API_URL}/series/{tvdb_id}/episodes/'
                    f'{self._order_type}?{params}'
                ))
            )
        except (ValidationError, Exception):
            log.exception(f'Failed to query episode {episode_info} on TVDb')
            return None

        if not response.data.episodes:
            log.debug(f'No associated episode {episode_info} on TVDb')
            return None

        return response.data.episodes[0].id


    def __get_all_episodes(self, tvdb_id: int) -> list[EpisodeBaseRecord]:
        """
        Get all the episodes (across all pages) for the series with the
        given TVDb ID.

        Args:
            tvdb_id: ID of the series whose episodes are being
                requested.

        Returns:
            List of all Episodes for the given series.
        """

        def _query_page(page: int, /) -> list[EpisodeBaseRecord]:
            """Query the episodes on the given page number"""

            try:
                return SeriesEpisodeResponse.model_validate(
                    self.get((
                        f'{self.__ROOT_API_URL}/series/{tvdb_id}/episodes'
                        f'/{self._order_type}?page={page}'
                    ))
                ).data.episodes or []
            except Exception:
                log.exception(
                    f'Failed to query episodes for {tvdb_id} on page {page}'
                )
                return []

        # Query first page of episodes
        page_number, last_length = 0, 0
        results = _query_page(page_number)

        # Default page size is 500; if an exact multiple of 500 episodes
        # were returned, query next page until no new episodes are
        # returned (in case there is an exact multiple of 500 episodes)
        while len(results) % 500 == 0 and len(results) != last_length:
            last_length = len(results)
            results += _query_page(page_number := page_number + 1)

        return results


    def __get_series_artwork(self,
            tvdb_id: int,
            language: str,
            art_type: ArtType,
        ) -> list[ArtworkExtendedRecord]:
        """
        Get all the artwork of the given type for the series with the
        given TVDb ID.

        Args:
            tvdb_id: TVDb ID of the series whose artwork is being
                requested.
            language: Language code of the artwork to request.
            art_type: Name of the type of art being requested.

        Returns:
            List of artwork.
        """

        url = f'{self.__ROOT_API_URL}/series/{tvdb_id}/artworks?lang={language}'

        try:
            return [
                art
                for art in SeriesArtworkResponse.model_validate(
                    self.get(url)
                ).data.artworks
                if art.type == self.ARTWORK_TYPES[art_type]
            ]
        except ValidationError:
            return []


    def __get_best_artwork(self,
            tvdb_id: int,
            art_type: ArtType,
        ) -> str | None:
        """
        Get the URL for the "best" artwork of the specified type.

        Args:
            tvdb_id: ID of the series whose artwork is being queried.
            art_type: Type of the artwork to query.

        Returns:
            URL to the highest resolution artwork of the specified type.
            None if there is no artwork.
        """

        artwork: list[ArtworkExtendedRecord] = []
        for language in self.language_priority:
            artwork += self.__get_series_artwork(tvdb_id, language, art_type)

        if not artwork:
            log.debug(f'TVDb has no {art_type}s for TVDb {tvdb_id}')
            return None

        # Find best (valid) poster by pixel count, starting with the first one
        best = artwork[0]
        for art in artwork:
            if (art.width >= self.minimum_source_width
                and art.height >= self.minimum_source_height
                and art.width * art.height > best.width * best.height):
                best = art

        return best.image


    def set_series_ids(self,
            library_name: str,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all possible series ID's for the given SeriesInfo object.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo to update.
            log: Logger for all log messages.
        """

        # If all possible ID's are defined
        if series_info.has_ids('imdb_id', 'tmdb_id', 'tvdb_id'):
            return None

        # Exit if the series cannot be found on TVDb
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None
        series_info.set_tvdb_id(tvdb_id)

        try:
            response = SeriesExtendedRecord.model_validate(
                self.get(
                    f'{self.__ROOT_API_URL}/series/{tvdb_id}/extended?short=true'
                )
            )
        except ValidationError:
            return None

        if response.remoteIds:
            for id_ in response.remoteIds:
                if id_.sourceName == 'IMDB':
                    series_info.set_imdb_id(id_.id)
                elif id_.sourceName == 'TheMovieDB.com':
                    series_info.set_tmdb_id(id_.id)

        return None


    def query_series(self,
            query: str,
            *,
            log: Logger = log,
        ) -> list[SearchResult]:
        """
        Search TVDb for any Series matching the given query.

        Args:
            query: Series name or substring to look up.
            log: Logger for all log messages.

        Returns:
            List of SearchResults for the given query.
        """

        try:
            results = SearchResultResponse.model_validate(
                self.get(
                    f'{self.__ROOT_API_URL}/search?query={url_quote(query)}'
                )
            ).data
        except ValidationError:
            return []

        def _get_id(ids: list[RemoteID], source_name: str) -> str | None:
            for id_ in ids:
                if id_.sourceName == source_name:
                    return id_.id
            return None

        return [
            SearchResult(
                name=result.translations.get('eng', result.name),
                year=result.year,
                poster=result.image_url,
                overview=result.overview or 'No Overview',
                ongoing=(result.status or '') == 'Continuing',
                imdb_id=_get_id(result.remote_ids, 'IMDB'),
                tvdb_id=result.tvdb_id,
            )
            for result in results
            if result.year
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
            series_info: Series to get the episodes of.
            log: Logger for all log messages.

        Returns:
            List of EpisodeInfo objects and None (as watched statuses
            cannot be determined) for this series.
        """

        # Cannot query TVDb if no series TVDb ID
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.error(f'Cannot source episodes from TVDb for {series_info}')
            return []

        return [
            (
                EpisodeInfo(
                    title=episode.name,
                    season_number=episode.seasonNumber,
                    episode_number=episode.number,
                    absolute_number=(
                        episode.number
                        if self._order_type == 'absolute'
                        else None
                    ),
                    tvdb_id=episode.id,
                    airdate=episode.aired or None,
                ),
                WatchedStatus(self._interface_id)
            )
            for episode in self.__get_all_episodes(tvdb_id)
            if (
                (self._include_movies or not episode.isMovie)
                and episode.name
            )
        ]


    def set_episode_ids(self,
            library_name: Any,
            series_info: SeriesInfo,
            episode_infos: list[EpisodeInfo],
            *,
            log: Logger = log,
        ) -> None:
        """
        Set all the ID's for the given list of EpisodeInfo objects. This
        can provide the IMDb, TMDb, or TVDb ID for each episode.

        Args:
            library_name: Unused argument.
            series_info: SeriesInfo for the entry.
            infos: List of EpisodeInfo objects to update.
            log: Logger for all log messages.
        """

        for episode_info in episode_infos:
            # Skip if has IMDb, TMDb, and TVDb IDs
            if episode_info.has_ids('imdb_id', 'tmdb_id', 'tvdb_id'):
                continue

            # Get and set the episode TVDb ID
            tvdb_id = self.__get_episode_id(series_info, episode_info, log=log)
            if tvdb_id is None:
                log.debug(f'Cannot find {series_info} {episode_info} on TVDb')
                continue
            episode_info.set_tvdb_id(tvdb_id)

            # Query extended info for this episode
            try:
                response = EpisodeExtendedResponse.model_validate(
                    self.get(
                        f'{self.__ROOT_API_URL}/episodes/{tvdb_id}/extended'
                    )
                )
            except ValidationError:
                log.debug(f'{series_info} {episode_info} returned no TVDb data')
                continue

            # Update all ID data for this episode
            if response.data.remoteIds:
                for id_ in response.data.remoteIds:
                    if id_.sourceName == 'IMDB':
                        episode_info.set_imdb_id(id_.id)
                    elif id_.sourceName == 'TheMovieDB.com':
                        episode_info.set_tmdb_id(id_.id)

        return None


    def get_all_logos(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> list[str] | None:
        """
        Get all logos for the requested series.

        Args:
            series_info: SeriesInfo for this entry.
            log: Logger for all log messages.

        Returns:
            List of URLs of all logos corresponding to this Series. None
            if the Series cannot be found on TVDb.
        """

        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None

        return [
            art.image
            for language in self.language_priority
            for art in self.__get_series_artwork(tvdb_id, language, 'logo')
        ]


    def get_all_backdrops(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> list[str] | None:
        """
        Get all backdrops for the requested series.

        Args:
            series_info: SeriesInfo for this entry.
            log: Logger for all log messages.

        Returns:
            List of URLs to series backdrops. None if it cannot be
            found.
        """

        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None

        return [
            art.image
            for language in self.language_priority
            for art in self.__get_series_artwork(
                tvdb_id, language, 'background'
            )
        ]


    def get_source_image(self,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            *,
            check_dimensions: bool = True,
            log: Logger = log,
        ) -> str | None:
        """
        Get the source image for the requested episode.

        Args:
            series_info: SeriesInfo for this episode.
            episode_info: EpisodeInfo for this episode.
            check_dimensions: Whether to check the dimensions of the
                image against the requirements of this Interface.
            log: Logger for all log messages.

        Returns:
            URL to the source image for the requested episode. None if
            no image is available.
        """

        # Find Episode
        tvdb_id = self.__get_episode_id(series_info, episode_info, log=log)
        if tvdb_id is None:
            log.warning(f'Cannot find {series_info} {episode_info} on TVDb')
            return None

        # Get associated image for this Episode
        try:
            response = EpisodeExtendedResponse.model_validate(
                self.get(f'{self.__ROOT_API_URL}/episodes/{tvdb_id}/extended')
            )
        except ValidationError:
            log.warning(f'Cannot find {series_info} {episode_info} on TVDb')
            return None

        if not (image_url := response.data.image):
            log.debug(f'TVDb has no images for "{series_info}" {episode_info}')
            return None

        # Bypass dimensional check
        if not check_dimensions:
            return image_url

        # Skip dimension check if requirements are >640p since TVDb
        # never has images of that quality
        if self.minimum_source_width > 640 or self.minimum_source_height > 360:
            log.debug((
                f'TVDb images for "{series_info}" {episode_info} do not meet '
                f'dimensional requirements'
            ))
            return None

        # Verify image meets dimensional requirements
        width, height = self.get_image_size(image_url, log=log)
        if (width >= self.minimum_source_width
            and height >= self.minimum_source_height):
            return image_url

        log.debug((
            f'TMDb images for "{series_info}" {episode_info} do not meet '
            f'dimensional requirements'
        ))
        return None


    def get_episode_title(self,
            series_info: SeriesInfo,
            episode_info: EpisodeInfo,
            language_code: LanguageCode = 'eng',
            *,
            log: Logger = log,
        ) -> str | None:
        """
        Get the episode title for the episode in the given language.

        Args:
            series_info: SeriesInfo for the entry.
            episode_info: EpisodeInfo for the entry.
            language_code: The language code for the desired title.
            log: Logger for all log messages.

        Args:
            The episode title, None if it cannot be found.
        """

        # Find Episode ID, warn and exit if cannot be found
        tvdb_id = self.__get_episode_id(series_info, episode_info, log=log)
        if tvdb_id is None:
            log.warning(f'Cannot find {series_info} {episode_info} on TVDb')
            return None

        try:
            return EpisodeTranslationResponse.model_validate(
                self.get((
                    f'{self.__ROOT_API_URL}/episodes/{tvdb_id}/translations/'
                    f'{language_code}'
                ))
            ).data.name
        except ValidationError:
            return None


    def get_series_logo(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> str | None:
        """
        Get the best logo for the given series.

        Args:
            series_info: Series to get the logo of.
            log: Logger for all log messages.

        Returns:
            URL to the 'best' logo for the given series, and None if no
            images  are available.
        """

        # Find Series
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None

        return self.__get_best_artwork(tvdb_id, 'logo')


    def get_series_backdrop(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> str | None:
        """
        Get the best backdrop for the given series.

        Args:
            series_info: Series to get the logo of.
            log: Logger for all log messages.

        Returns:
            URL to the 'best' backdrop for the given series, and None if
            no images are available.
        """

        # Find Series
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None

        return self.__get_best_artwork(tvdb_id, 'banner')


    def get_series_poster(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log,
        ) -> str | None:
        """
        Get the best poster for the given series.

        Args:
            series_info: Series to get the poster of.
            log: Logger for all log messages.

        Returns:
            URL to the 'best' poster for the given series, and None if
            no images are available.
        """

        # Find Series
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return None

        return self.__get_best_artwork(tvdb_id, 'poster')


    def get_season_titles(self,
            series_info: SeriesInfo,
            *,
            log: Logger = log
        ) -> dict[str, dict[int, str]]:
        """
        Get all custom season titles for all languages of the given
        series.

        >>> get_season_titles(...)
        {'eng': {1: 'Part One', 2: 'Part Two'}, 'ita': {...}}

        Args:
            series_info: Series whose season titles to query.
            log: Logger for all log messages.

        Returns:
            Dictionary whose keys are the language code and whose values
            are dictionaroes whose keys are the season numbers and
            whose values are the season titles.
        """

        # Find Series
        if (tvdb_id := self.__get_series_id(series_info)) is None:
            log.warning(f'Cannot find {series_info} on TVDb')
            return {}

        # Read all season data
        try:
            series_data = SeriesExtendedRecord.model_validate(
                self.get(
                    f'{self.__ROOT_API_URL}/series/{tvdb_id}/extended?short=true'
                )
            )
        except ValidationError:
            log.exception(f'{series_info} returned invalid series data')
            return {}

        # No season data, return empty dictionary
        if not series_data.seasons:
            return {}

        # Determine effective season type
        if self._order_type == 'default':
            season_type = series_data.defaultSeasonType
        else:
            season_type = self._order_type

        # Look for alternate translations of all seasons
        translations: dict[str, dict[int, str]] = {}
        for season in series_data.seasons:
            # Skip seasons for alternate orderings
            if season_type not in (season.type.id, season.type.name):
                log.debug(f'Skipping {season=}, wrong type')
                continue

            # Skip seasons with no name translations
            if not season.nameTranslations:
                log.debug(f'Skipping {season=}, no translations')
                continue

            # Translations are listed as comma-separated string, for some reason..
            for language in season.nameTranslations[0].split(','):
                # Query translated season data
                try:
                    season_data = SeasonTranslationResponse.model_validate(
                        self.get((
                            f'{self.__ROOT_API_URL}/seasons/{season.id}'
                            f'/translations/{language}'
                        ))
                    ).data
                except ValidationError:
                    log.exception('Invalid season translation subdata')
                    continue

                # Add translation
                if language in translations:
                    translations[language][season.number] = season_data.name
                else:
                    translations[language] = {season.number: season_data.name}

        return translations
