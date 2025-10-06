from os import getenv
from pathlib import Path
from re import IGNORECASE, compile as re_compile
from typing import TYPE_CHECKING, Callable, Iterable

from app.yaml.sync import SeriesYamlWriter
from tqdm import tqdm
from yaml import dump

from app.interfaces.v1 import (
    EmbyInterfaceV1,
    JellyfinInterfaceV1,
    PlexInterfaceV1,
    SonarrInterfaceV1,
    TautulliInterfaceV1,
    TMDbInterfaceV1,
)
from app.logging.logger import log
from app.settings import TQDM_KWARGS
from modules.Show import Show
from modules.ShowArchive import ShowArchive

if TYPE_CHECKING:
    from modules.PreferenceParser import PreferenceParser


def notify(message: str) -> Callable:
    """
    Return a decorator that notifies the given message when the
    decorated function starts executing. Only notify if the global
    execution mode is batch. Logging is done in info level.

    Args:
        message: Message to log.

    Returns:
        Wrapped decorator.
    """

    def decorator(function: Callable) -> Callable:
        def inner(*args, **kwargs):
            # if settings.options.execution_mode == 'batch':
            log.info(message)

            return function(*args, **kwargs)
        return inner
    return decorator


class Manager:
    """
    This class describes a title card manager. The Manager is used to
    control title card and archive creation/management from a high
    level, and is meant to be the main entry point of the program.
    """

    """Default execution mode for Manager.run()"""
    DEFAULT_EXECUTION_MODE = 'serial'

    """Valid execution modes for Manager.run()"""
    VALID_EXECUTION_MODES = ('serial', 'batch')


    def __init__(self,
            preferences: 'PreferenceParser',
            *,
            check_tautulli: bool = True,
        ) -> None:
        """
        Constructs a new instance of the Manager.

        Args:
            preferences: PreferenceParser to use for the Manager.
            check_tautulli: Whether to check Tautulli integration (for
                fast start).
        """

        self.preferences = preferences

        # Optionally integrate with Tautulli
        if check_tautulli and self.preferences.settings.tautulli:
            TautulliInterfaceV1(
                **self.preferences.settings.tautulli.model_dump()
            ).integrate()

        # Optionally assign EmbyInterface
        self.emby_interface = None
        if self.preferences.settings.emby:
            self.emby_interface = EmbyInterfaceV1(
                **self.preferences.settings.emby.model_dump(
                    exclude={'watched_style', 'unwatched_style', 'sync'}
                )
            )

        # Optionally assign JellyfinInterface
        self.jellyfin_interface = None
        if self.preferences.settings.jellyfin:
            self.jellyfin_interface = JellyfinInterfaceV1(
                **self.preferences.settings.jellyfin.model_dump(
                    exclude={'watched_style', 'unwatched_style', 'sync'}
                )
            )

        # Optionally assign PlexInterface
        self.plex_interface = None
        if self.preferences.settings.plex:
            self.plex_interface = PlexInterfaceV1(
                **self.preferences.settings.plex.model_dump(
                    exclude={'watched_style', 'unwatched_style', 'sync'}
                )
            )

        # Optionally assign SonarrInterface
        self.sonarr_interfaces = []
        if self.preferences.settings.sonarr:
            self.sonarr_interfaces = [
                SonarrInterfaceV1(
                    **settings.model_dump(
                        exclude={'watched_style', 'unwatched_style', 'sync'}
                    ),
                    server_id=server_id,
                )
                for server_id, settings in enumerate(
                    self.preferences.settings.sonarr
                )
            ]

        # Optionally assign TMDbInterface
        self.tmdb_interface = None
        if self.preferences.settings.tmdb:
            self.tmdb_interface = TMDbInterfaceV1(
                **self.preferences.settings.tmdb.model_dump(),
            )

        # Setup blank show and archive lists
        self.shows: list[Show] = []
        self.archives: list[ShowArchive] = []


    def sync_series_files(self) -> None:
        """Sync series YAML files from Emby/Jellyfin/Sonarr/Plex."""

        # If no sync-able interfaces are enabled, skip
        if (not self.preferences.settings.emby
            and not self.preferences.settings.jellyfin
            and not self.preferences.settings.sonarr
            and not self.preferences.settings.plex):
            return None

        # Always notify the user
        log.info('Starting to sync to series YAML files..')

        if (self.preferences.settings.emby
            and self.preferences.settings.emby.sync):
            for sync in self.preferences.settings.emby.sync:
                sync.sync_writer.update_from_emby(
                    self.emby_interface,
                    filter_libraries=sync.filter_libraries,
                    required_tags=sync.required_tags,
                    exclusions=sync.exclusions
                )

        if (self.preferences.settings.jellyfin
            and self.preferences.settings.jellyfin.sync):
            for sync in self.preferences.settings.jellyfin.sync:
                sync.sync_writer.update_from_jellyfin(
                    self.jellyfin_interface,
                    filter_libraries=sync.filter_libraries,
                    required_tags=sync.required_tags,
                    exclusions=sync.exclusions
                )

        if (self.preferences.settings.plex
            and self.preferences.settings.plex.sync):
            for sync in self.preferences.settings.plex.sync:
                sync.sync_writer.update_from_plex(
                    self.plex_interface,
                    filter_libraries=sync.filter_libraries,
                    required_tags=sync.required_tags,
                    exclusions=sync.exclusions
                )
    
        if (self.preferences.settings.sonarr
            and self.preferences.settings.sonarr.sync):
            for interface, sonarr in zip(
                self.sonarr_interfaces,
                self.preferences.settings.sonarr
            ):
                for sync in sonarr.sync:
                    sync.sync_writer.update_from_sonarr(
                        interface,
                        libraries=sync.filter_libraries,
                        required_tags=sync.required_tags,
                        monitored_only=sync.monitored_only,
                        downloaded_only=sync.downloaded_only,
                        series_type=sync.series_type,
                        exclusions=sync.exclusions
                    )

        return None


    @notify('Starting to read series YAML files..')
    def create_shows(self) -> None:
        """
        Create Show and ShowArchive objects for each series YAML files
        known to the global PreferenceParser. This updates the Manager's
        show and archives lists.
        """

        # Look for series filter
        name_filter = None
        if (raw_filter := getenv('TCM_V1_SERIES_FILTER')):
            name_filter = re_compile(raw_filter, IGNORECASE)

        # Go through each Series YAML file
        for show in self.preferences.iterate_series_files():
            # Skip shows whose YAML was invalid
            if not show.valid:
                log.warning(f'Skipping series {show}')
                continue

            # If filter was specified, apply
            if name_filter and not name_filter.match(show.series_info.name):
                continue
            self.shows.append(show)

            # If archives are disabled globally, or for this show - skip
            if (not self.preferences.create_archive or not show.archive
                or not self.preferences.archive_directory):
                continue

            self.archives.append(
                ShowArchive(self.preferences.archive_directory, show)
            )


    @notify('Starting to assign interfaces..')
    def assign_interfaces(self) -> None:
        """Assign all interfaces to each Show known to this Manager"""

        # Assign interfaces for each show
        for show in tqdm(
            self.shows + self.archives,
            desc='Assigning interfaces',
            **TQDM_KWARGS
        ):
            show.assign_interfaces(
                self.emby_interface,
                self.jellyfin_interface,
                self.plex_interface,
                self.sonarr_interfaces,
                self.tmdb_interface
            )


    @notify("Starting to set show ID's..")
    def set_show_ids(self) -> None:
        """Set the series ID's of each Show known to this Manager"""

        # For each show in the Manager, set series IDs
        for show in tqdm(
            self.shows + self.archives,
            desc='Setting series IDs',
            **TQDM_KWARGS
        ):
            show.set_series_ids()


    @notify('Starting to read source files..')
    def read_show_source(self) -> None:
        """
        Reads all source files known to this manager. This reads Episode
        objects for all Show and ShowArchives, and also looks for
        multipart episodes.
        """

        # Read source files for Show objects
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Reading source files for {show}')
            show.read_source()
            show.find_multipart_episodes()


    @notify('Starting to add new episodes..')
    def add_new_episodes(self) -> None:
        """Add any new episodes to this Manager's shows."""

        # For each show in the Manager, look for new episodes using any of the
        # possible interfaces
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Adding new episodes for {show}')
            show.add_new_episodes()


    @notify("Starting to set episode ID's..")
    def set_episode_ids(self) -> None:
        """Set all episode ID's for all shows."""

        # For each show in the Manager, set IDs for every episode
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Setting episode IDs for {show}')
            show.set_episode_ids()


    @notify('Starting to add translations..')
    def add_translations(self) -> None:
        """Query TMDb for all translated episode titles (if indicated)."""

        # If the TMDbInterface isn't enabled, skip
        if not self.preferences.use_tmdb:
            return None

        # For each show in the Manager, add translation
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Adding translations for {show}')
            show.add_translations()

        return None


    @notify('Starting to download logos..')
    def download_logos(self) -> None:
        """Download logo files for all shows."""

        # If the TMDbInterface isn't enabled, skip
        if not self.preferences.use_tmdb:
            return None

        # For each show in the Manager, download a logo
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Downloading logo for {show}')
            show.download_logo()

        return None


    @notify('Starting to select source images..')
    def select_source_images(self) -> None:
        """Select and download the source images for all shows."""

        # Go through each show and download source images
        for show in (pbar := tqdm(self.shows + self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Selecting sources for {show}')
            show.select_source_images()


    @notify('Starting to create missing title cards..')
    def create_missing_title_cards(self) -> None:
        """Creates all missing title cards for all shows."""

        # Go through every show in the Manager, create cards
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            pbar.set_description(f'Creating cards for {show}')
            show.create_missing_title_cards()


    @notify('Starting to create season posters..')
    def create_season_posters(self) -> None:
        """Create season posters for all shows."""

        # For each show in the Manager, create its posters
        for show in tqdm(
            self.shows + self.archives,
            desc='Creating season posters',
            **TQDM_KWARGS
        ):
            show.create_season_posters()


    @notify('Starting to update Media Servers..')
    def update_media_server(self) -> None:
        """
        Update Plex/Emby for all cards for all shows. This only executes
        if Emby/Jellyfin/Plex are globally enabled.
        """

        # If no media servers are enabled, skip
        if (not self.preferences.use_emby
            and not self.preferences.use_jellyfin
            and not self.preferences.use_plex):
            return None

        # Go through each show in the Manager, update Plex
        for show in (pbar := tqdm(self.shows, **TQDM_KWARGS)):
            pbar.set_description(f'Updating Server for {show}')
            show.update_media_server()

        return None


    @notify('Starting to update archives..')
    def update_archive(self) -> None:
        """Update the title card archives for every show."""

        # If archives are globally disabled, skip
        if not self.preferences.create_archive:
            return None

        # Update each archive
        for show_archive in (pbar := tqdm(self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Updating archive for {show_archive}')
            show_archive.create_missing_title_cards()

        return None


    @notify('Starting to create summaries..')
    def create_summaries(self) -> None:
        """
        Creates summaries for every ShowArchive. This only executes if
        archives and summaries are globally enabled.
        """

        # If summaries aren't enabled, skip
        if (not self.preferences.create_archive
            or not self.preferences.create_summaries):
            return None

        # Go through each archive and create summaries
        for show_archive in (pbar := tqdm(self.archives, **TQDM_KWARGS)):
            pbar.set_description(f'Creating Summary for {show_archive}')
            show_archive.create_summary()

        return None


    def __run(self, *, serial: bool = False) -> None:
        """
        Run the Manager. If serial execution is not indicated, then sync
        is run and Show/ShowArchive objects are created.

        Args:
            serial: Whether execution is serial.
        """

        # If serial, don't update series files or create shows
        if not serial:
            self.sync_series_files()
            self.create_shows()

        # Always execute these, even in serial mode
        self.assign_interfaces()
        self.set_show_ids()
        self.read_show_source()
        self.add_new_episodes()
        self.set_episode_ids()
        self.add_translations()
        self.download_logos()
        self.select_source_images()
        self.create_missing_title_cards()
        self.create_season_posters()
        self.update_media_server()
        self.update_archive()
        self.create_summaries()


    def __run_serially(self) -> None:
        """Run the Manager, executing each step for each show at a time."""

        # Sync YAML files
        self.sync_series_files()

        # Look for series filter
        name_filter = None
        if (raw_filter := getenv('TCM_V1_SERIES_FILTER')):
            name_filter = re_compile(raw_filter, IGNORECASE)

        # Go through each Series YAML file, creating Show/ShowArchive objects
        for show in self.preferences.iterate_series_files():
            # Skip shows whose YAML was invalid
            if not show.valid:
                log.warning(f'Skipping series {show}')
                continue

            # If filter was specified, apply
            if name_filter and not name_filter.match(show.series_info.name):
                continue

            # Create ShowArchive object if archive enabled globally + show
            self.shows = [show]
            if self.preferences.create_archive and show.archive:
                archive = ShowArchive(self.preferences.archive_directory, show)
                self.archives = [archive]

            # Run all functions on this series
            try:
                self.__run(serial=True)
            except Exception:
                log.exception(f'Uncaught Exception while processing {show}')
                continue


    def run(self) -> None:
        """Run the Manager either in either serial or batch mode"""

        if self.preferences.settings.options.execution_mode == 'serial':
            self.__run_serially()
        elif self.preferences.settings.options.execution_mode == 'batch':
            self.__run()


    def remake_cards(self, rating_keys: Iterable[int]) -> None:
        """
        Remake the title cards associated with the given list of rating
        keys. These keys are used to identify their corresponding
        episodes within Plex.

        Args:
            rating_keys: List of Plex rating keys corresponding to
                Episodes to update the cards of.
        """

        # Exit if Plex is not enabled
        if not self.preferences.use_plex:
            log.error('Tautulli integration requires Plex')
            return None

        # Get details for each rating key from Plex
        entry_list = []
        for key in rating_keys:
            if len(details := self.plex_interface.get_episode_details(key)) ==0:
                log.error(f'Rating key {key} has no associated episodes')
            else:
                log.debug(f'Rating key {key} -> {len(details)} item(s)')
                entry_list += details

        # Go through every series in all series YAML files
        for show in self.preferences.iterate_series_files():
            # If no more entries, exit
            if len(entry_list) == 0:
                break

            # Check if this show is one of the entries to update
            is_found = False
            for index, (series_info, episode_info, library_name) \
                in enumerate(entry_list):
                # Match the library and series name
                full_match_name = show.series_info.full_match_name
                if (show.valid
                    and show.library_name == library_name
                    and full_match_name == series_info.full_match_name):
                    self.shows = [show]
                    self.__run(serial=True)
                    is_found = True
                    break

            # If an entry was found, delete from list
            if is_found:
                del entry_list[index] # pylint: disable=undefined-loop-variable

        # Warn for all entries not found
        for series_info, episode_info, library_name in entry_list:
            log.warning(f'Cannot update card for "{series_info}" {episode_info}'
                        f' within library "{library_name}" - no matching YAML '
                        f'entry was found')

        return None


    def report_missing(self, file: Path) -> None:
        """Report all missing assets for all shows."""

        # Serial mode won't have an accurate show list
        if self.preferences.settings.options.execution_mode == 'serial':
            self.create_shows()
            self.read_show_source()

        missing = {}
        # Go through each show
        for show in self.shows:
            show_dict = {}
            # Go through each episode for this show, add missing source/cards
            for episode in show.episodes.values():
                # Add key for this episode
                key = str(episode)
                show_dict[key] = {}

                # If source file doesn't exist, add to report
                if (show.card_class.USES_UNIQUE_SOURCES
                    and (
                        not show.style_set.watched_style_is_art
                        or not show.style_set.unwatched_style_is_art
                    )
                    and not episode.source.exists()):
                    show_dict[key]['source'] = episode.source.name

                # If destination card doesn't exist, add to report
                if (episode.destination is not None
                    and not episode.destination.exists()):
                    show_dict[key]['card'] = episode.destination.name

                # If translation is requested and doesn't exist, add
                missing_translations = [
                    translation['key'] for translation in show.title_languages
                    if not episode.key_is_specified(translation['key'])
                ]
                if len(missing_translations) > 0:
                    show_dict[key]['translations'] = missing_translations

                # Delete entry if no missing assets
                if len(show_dict[key]) == 0:
                    del show_dict[key]

            # Report missing logo if archives and summaries are enabled
            if (show.archive
                and self.preferences.create_summaries
                and not show.logo.exists()):
                show_dict['logo'] = show.logo.name

            # Report missing backdrop if art style is used
            if ((show.style_set.watched_style_is_art
                or show.style_set.unwatched_style_is_art)
                and not show.backdrop.exists()):
                show_dict['backdrop'] = show.backdrop.name

            # If this show is missing at least one thing, add to missing dict
            if len(show_dict.keys()) > 0:
                missing[str(show)] = show_dict

        # Create parent directories if necessary
        file.parent.mkdir(parents=True, exist_ok=True)

        # Write updated data with this entry added
        with file.open('w', encoding='utf-8') as file_handle:
            dump(missing, file_handle, allow_unicode=True, width=160)

        log.info(f'Wrote missing assets to "{file.resolve()}"')
