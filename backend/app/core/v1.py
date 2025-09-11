from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from app.info.series import SeriesInfoV1
from app.logging.logger import log
from app.schemas.yaml import PreferencesYaml, SeriesYaml, YamlFile
from app.yaml.template import Template


def read_preferences_file(file: Path, /) -> PreferencesYaml:
    ...


def sync_series_files(preferences: PreferencesYaml, /) -> ...:
    ...


def finalize_yaml(
        yaml: YamlFile,
        /,
        *,
        default_media_server: Literal['emby', 'jellyfin', 'plex'] = 'plex',
    ) -> YamlFile:

    # Convert raw YAML into Template objects
    templates = {
        name: Template(name, template)
        for name, template in yaml.templates.items()
    }

    def apply_template(
            series_info: SeriesInfoV1,
            series_yaml: SeriesYaml,
        ) -> SeriesYaml | None:
        """

        """

        # No Template identified, return as is
        if not series_yaml.template:
            return series_yaml

        # Direct name - e.g. {template: "example"}
        # Convert to "name" variant
        if isinstance(series_yaml.template, str):
            series_yaml.template = {'name': series_yaml.template}

        # Verify this template exists in the YAML file
        template_name = series_yaml.template.get('name', None)
        if not (template := templates.get(template_name, None)):
            template_names = '"' + '", "'.join(templates.keys()) + '"'
            log.error(f'Template "{template_name}" not defined for {series_name}')
            if not templates:
                log.info('There are no templates defined in the YAML file')
            else:
                log.info(f'The only defined templates are: {template_names}')
            return None

        # Template exists, apply
        series_yaml: dict | None = template.apply_to_series(
            series_info,
            series_yaml.model_dump(exclude_unset=True),
        )
        if not series_yaml:
            return None

        try:
            return SeriesYaml.model_validate(series_yaml)
        except Exception:
            log.exception(f'Error validating series YAML: {series_yaml}')
            return None


    def apply_library(series_yaml: SeriesYaml) -> SeriesYaml | None:
        """
        """

        # No library specified, return as is
        if not series_yaml.library:
            return series_yaml

        if series_yaml.library not in yaml.libraries:
            log.error(f'Library "{series_yaml.library}" is not defined in libraries')
            return None

        yaml_dict = series_yaml.model_dump(exclude_unset=True)
        Template.recurse_priority_union(
            yaml_dict,
            yaml.libraries[series_yaml.library].model_dump(exclude_unset=True)
        )

        try:
            return SeriesYaml.model_validate(yaml_dict)
        except Exception:
            log.exception(f'Error validating series YAML: {yaml_dict}')
            return None


    def apply_font(series_yaml: SeriesYaml) -> SeriesYaml | None:
        """"""

        # No font specified, return as-is
        if not series_yaml.font:
            return series_yaml

        # Font is just an identifier, merge from font map and return
        if isinstance(series_yaml.font, str):
            if (font_name := series_yaml.font) not in yaml.fonts:
                log.error(f'Font "{font_name}" is not defined in font list')
                return None

            yaml_dict = series_yaml.model_dump(exclude_unset=True)
            font_yaml: dict = yaml_dict.pop('font', {})
            Template.recurse_priority_union(
                font_yaml,
                yaml.fonts[font_name].model_dump(exclude_unset=True)
            )

            try:
                yaml_dict['font'] = font_yaml
                return SeriesYaml.model_validate(yaml_dict)
            except Exception:
                log.exception(f'Error validating series YAML: {yaml_dict}')
                return None

        # Font is a direct dictionary, return as-is
        return series_yaml


    finalized_yaml = yaml.model_copy(deep=True)
    for series_name, series_yaml in yaml.series.items():
        try:
            series_info = SeriesInfoV1.from_series_yaml(series_name,series_yaml)
        except Exception:
            log.exception(f'Error identifying series info of {series_name}')
            log.debug(f'Series YAML: {series_yaml}')
            del finalized_yaml.series[series_name]
            continue

        # Apply Template, library map, and font map - if indicated
        if not (series_yaml := apply_template(series_info, series_yaml)):
            del finalized_yaml.series[series_name]
            continue
        if not (series_yaml := apply_library(series_yaml)):
            del finalized_yaml.series[series_name]
            continue
        if not (series_yaml := apply_font(series_yaml)):
            del finalized_yaml.series[series_name]
            continue

        finalized_yaml.series[series_name] = series_yaml

    return finalized_yaml


def iterate_series_files(preferences: PreferencesYaml, /) -> Iterator[Path]:
    ...


def iterate_series_file(file: Path, /) -> Iterator[SeriesYaml]:
    ...
