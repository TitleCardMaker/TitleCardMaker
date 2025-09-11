from collections import namedtuple
from pathlib import Path
from sys import exit as sys_exit
from typing import Any, Iterator, Literal, overload

from app.core.v1 import finalize_yaml
from app.schemas.yaml import PreferencesYaml, SeriesYaml, YamlFile
from fastapi import HTTPException
from tqdm import tqdm
from yaml import safe_load

from app.interfaces.v1 import (
    EmbyInterfaceV1,
    JellyfinInterfaceV1,
    PlexInterfaceV1,
    TMDbInterfaceV1,
    TautulliInterfaceV1,
)
from app.info.series import SeriesInfoV1
from app.logging.logger import log
from app.magick.summary import StylizedSummary
from app.settings import TQDM_KWARGS, settings
from app.yaml.font import Font
from app.yaml.reader import YamlReader
from app.yaml.template import Template
from modules.CleanPath import CleanPath
from modules.FormatString import FormatString
from modules.Manager import Manager
from modules.Show import Show
from modules.StyleSet import StyleSet
from modules.TitleCard import TitleCard


YamlWriterSet = namedtuple(
    'YamlWriterSet', ('interface_id', 'writer', 'update_args')
)


class PreferenceParser:
    """
    This class describes a preference parser that reads a given
    preference YAML file and parses it into individual attributes.
    """

    """Valid image source identifiers"""
    VALID_IMAGE_SOURCES = ('emby', 'jellyfin', 'plex', 'tmdb')

    """Valid episode data source identifiers"""
    VALID_EPISODE_DATA_SOURCES = ('emby', 'jellyfin', 'sonarr', 'plex', 'tmdb')
    DEFAULT_EPISODE_DATA_SOURCE = 'sonarr'

    """Default season folder format string"""
    DEFAULT_SEASON_FOLDER_FORMAT = 'Season {season}'

    """Default directory for temporary database objects"""
    DEFAULT_TEMP_DIR = Path(__file__).parent / '.objects'


    def __init__(self, file: Path, is_docker: bool = False) -> None:
        """
        Constructs a new instance of this object. This reads the given
        file, errors and exits if any required options are missing, and
        then parses the preferences into object attributes.

        Args:
            file: The file to parse for preferences.
            is_docker: Whether executing within a Docker container.

        Raises:
            SystemExit (1): Any required YAML options are missing from
                `file`.
        """

        self.valid = True
        self.version = settings.config.CURRENT_VERSION
        self.is_docker = is_docker

        # Initialize parent YamlReader object - errors are critical
        self.version = settings.config.CURRENT_VERSION
        self.is_docker = settings.config.IS_DOCKER

        # Store, read, and parse file
        self.file = file
        if not self.file.exists():
            log.critical(
                f'Preference file "{self.file.resolve()}" does not exist'
            )
            sys_exit(1)
        try:
            self.settings = PreferencesYaml.model_validate(
                safe_load(file.read_text())
            )
        except Exception:
            log.exception(f'Preference file is invalid "{self.file.resolve()}"')
            sys_exit(1)

        # Update global config settings
        settings.config.V1_IMAGEMAGICK_CONTAINER = (
            self.settings.imagemagick.container
            if self.settings.imagemagick
            else settings.config.V1_IMAGEMAGICK_CONTAINER
        )


    def __repr__(self) -> str:
        """Returns an unambiguous string representation of the object."""

        attributes = ', '.join(
            f'{attr}={getattr(self, attr)!r}' for attr in self.__dict__
            if not attr.startswith('_')
        )

        return f'<PreferenceParser {attributes}>'


    @staticmethod
    def apply_template(
            templates: dict[str, Template],
            series_yaml: SeriesYaml,
            series_name: str,
            *,
            raise_exc: bool = False
        ) -> bool:
        """
        Apply the correct Template object (if indicated) to the given
        series YAML. This effectively "fill out" the indicated template,
        and updates the series YAML directly.

        Args:
            templates: Dictionary of Template objects to potentially
                apply.
            series_yaml: The YAML of the series to modify.
            series_name: The name of the series being modified.
            raise_exc: Whether to raise an Exception if the YAML is
                invalid.

        Returns:
            True if the given series contained all the required template
            variables for application, False if it did not.
        """

        # No templates defined for this series, skip
        if not series_yaml.template:
            return True

        # Get the specified template for this series
        if isinstance(series_yaml.template, str):
            # Assume if only a string, then its the template name
            template_name = series_yaml.template
            series_yaml.template = {'template_name': series_yaml.template}

        # Warn and return if template name not mapped
        template_name = series_yaml.template.get('name', None)
        if not (template := templates.get(template_name, None)):
            template_names = '"' + '", "'.join(templates.keys()) + '"'
            log.error(f'Template "{template_name}" not defined for {series_name}')
            log.info(f'The only defined templates are: {template_names}')
            return False

        # Parse title/year from the series to add as "built-in" template data
        try:
            series_info = SeriesInfoV1(series_name, series_yaml.year)
        except Exception as e:
            if raise_exc:
                raise HTTPException(
                    status_code=422,
                    detail=f'Error identifying series info of {series_name}',
                ) from e
            log.exception(f'Error identifying series info of {series_name}')
            log.debug(f'Series YAML: {series_yaml}')
            series_info = None

        # Apply using Template object
        return template.apply_to_series(
            series_info, series_yaml, raise_exc=raise_exc
        )


    @staticmethod
    def finalize_series_yaml(
            yaml: SeriesYaml,
            templates: dict[str, Template],
            *,
            default_media_server: str = 'plex',
            raise_exc: bool = False
        ) -> SeriesYaml | None:
        """
        Apply the indicated template, and merge the specified
        library/font to the given show YAML.

        Args:
            show_yaml: Base show YAML with potential template/library/
                font identifiers.
            library_map: Library map of library names/identifiers to
                library specifications.
            font_map: Font map of font names/identifiers to custom font
                specifications.

        Returns:
            Modified YAML, None if the modification failed.
        """

        # Apply template to series, stop if invalid
        if not PreferenceParser.apply_template(
            templates, show_yaml, show_name, raise_exc=raise_exc
        ):
            return None

        # Parse library from map
        if (len(library_map) > 0
            and (library_name := show_yaml.get('library')) is not None):
            # If library identifier is not in the map, error and exit
            if (library_yaml := library_map.get(library_name)) is None:
                library_names = '"' + '", "'.join(library_map.keys()) + '"'
                log.error(
                    f'Library "{library_name}" of series "{show_name}" is  not '
                    f'present in libraries list'
                )
                log.info(f'Listed library names are {library_names}')
                return None
            # Library identifier in map, merge YAML
            Template.recurse_priority_union(show_yaml, library_yaml)
            server = library_yaml.get('media_server', default_media_server)
            show_yaml['library'] = {
                'name': library_yaml.get('library_name', library_name),
                'path': CleanPath(library_yaml.get('path')).sanitize(),
                'media_server': server,
            }

        # Parse font from map (if given font is just an identifier)
        if (len(font_map) > 0
            and (font_name := show_yaml.get('font')) is not None
            and isinstance(font_name, str)):
            # If font identifier is not in map, error and exit
            if (font_yaml := font_map.get(font_name)) is None:
                font_names = '"' + '", "'.join(font_map.keys()) + '"'
                log.error(
                    f'Font "{font_name}" of series "{show_name}" is not '
                    f'present in font list'
                )
                log.info(f'Listed font names are {font_names}')
                return None
            # Font identifier in map, merge YAML
            show_yaml['font'] = {}
            Template.recurse_priority_union(show_yaml['font'], font_yaml)

        return show_yaml


    def iterate_series_files(self) -> Iterator[Show]:
        """
        Iterate through all series file listed in the preferences. For
        each series encountered in each file, yield a Show object. Files
        that do not exist or have invalid YAML are skipped.

        Returns:
            An iterable of Show objects created by the entry listed in
            all the known (valid) series files.
        """

        # Reach each file in the list of series YAML files
        for file_ in (pbar := tqdm(self.settings.options.series, **TQDM_KWARGS)):
            # Create Path object for this file
            try:
                file = CleanPath(file_).sanitize()
            except Exception:
                log.exception(f'Invalid series file "{file_}"')
                continue

            # Update progress bar for this file
            pbar.set_description(f'Reading {file.name}')
            log.info(f'Reading series YAML file "{file.resolve()}"..')

            # If the file doesn't exist, error and skip
            if not file.exists():
                log.error(f'Series file "{file.resolve()}" does not exist')
                continue

            # Read file, parse yaml
            try:
                file_yaml = finalize_yaml(
                    YamlFile.model_validate(safe_load(file.read_text()))
                )
            except Exception:
                log.exception(f'Error reading series file "{file.resolve()}"')
                continue

            if not file_yaml.series:
                log.warning(f'Series file "{file.resolve()}" has no entries')
                continue

            library_map = file_yaml.libraries
            font_map = file_yaml.fonts
            breakpoint()
            # Construct Template objects for this file
            templates: dict[str, Template] = {
                name: Template(name, template)
                for name, template in file_yaml.templates.items()
            }

            # Go through each series in this file
            for show_name in tqdm(
                file_yaml.series, desc='Reading entries', **TQDM_KWARGS
            ):
                # Apply template and merge libraries+font maps
                show_yaml = finalize_yaml(
                    file_yaml,
                )

                # If returned YAML is None (invalid) skip series
                if not show_yaml:
                    log.error(f'Skipping "{show_name}" from "{file_}"')
                    continue

                yield Show(show_name, show_yaml, self.source_directory, self)

                # Get all specified variations for this show
                variations = show_yaml.pop('archive_variations', [])
                if not isinstance(variations, list):
                    log.error(f'Invalid archive variations for {show_name}')
                    continue

                # Yield each variation
                show_yaml.pop('archive_name', None)
                show_yaml.pop('archive', None)
                for variation in variations:
                    # Apply template and merge libraries+font maps to variation
                    variation = self.finalize_show_yaml(
                        show_name, variation, templates, library_map, font_map,
                        default_media_server=self.default_media_server,
                    )

                    # Skip if finalization failed
                    if variation is None:
                        log.error(
                            f'Skipping archive variation of "{show_name}"'
                            f' from "{file_}"'
                        )
                        continue

                    # Get priority union of variation and base series
                    Template.recurse_priority_union(variation, show_yaml)

                    # Remove any library-specific details
                    variation.pop('media_directory', None)
                    variation.pop('library', None)

                    yield Show(show_name, variation, self.source_directory,self)


    def meets_minimum_resolution(self, width: int, height: int) -> bool:
        """
        Determine whether the given dimensions meet the minimum
        resolution requirements indicated in the preference file.

        Args:
            width: The width of the image.
            height: The height of the image.

        Returns:
            True if the dimensions are suitable, False otherwise.
        """

        return (
            width >= self.tmdb_minimum_resolution['width']
            and height >= self.tmdb_minimum_resolution['height']
        )


    def get_season_folder(self, season_number: int) -> str:
        """
        Get the season folder name for the given season number, padding
        the season number if indicated by the preference file, and
        returning an empty string if season folders are hidden.

        Args:
            season_number: The season number to get the folder name of.

        Returns:
            The season folder name. Empty string if folders are hidden,
            'Specials' for season 0, and either a zero-padded or not
            zero- padded version of "Season {x}" otherwise.

        Raises:
            SystemExit if the season folder formatting fails.
        """

        # If season folders are hidden, return empty string
        if (self.season_folder_format is None
            or len(self.season_folder_format.strip()) == 0):
            return ''

        # Season 0 is always Specials (never padded)
        if season_number == 0:
            return 'Specials'

        # Format season folder as indicated (zero-padding, whatever..)
        try:
            return FormatString(
                self.season_folder_format,
                data={'season': season_number},
            ).result
        except Exception:
            log.exception(f'Invalid season folder format')
            sys_exit(1)


    @overload
    def filesize_as_bytes(self, filesize: str) -> int: ...
    @overload
    def filesize_as_bytes(self, filesize: Literal[None]) -> None: ...

    def filesize_as_bytes(self, filesize: str | None) -> int | None:
        """
        Convert the given filesize string to its integer byte equivalent.

        Args:
            filesize: Filesize string to parse. Should be formatted like
                '{integer} {unit}' - e.g. 2 KB, 4 GiB, 1 B, etc.

        Returns:
            Number of bytes indicated by the given filesize string.
        """

        # If no limit was provided, return None
        if filesize is None:
            return None

        units = {
            'B': 1, 'KB':  2**10, 'MB':  2**20, 'GB':  2**30, 'TB':  2**40,
            '': 1, 'KIB': 10**3, 'MIB': 10**6, 'GIB': 10**9, 'TIB':10**12
        }

        number, unit = map(str.strip, filesize.split())
        value, unit_scale = float(number), units[unit.upper()]

        return int(value * unit_scale)
