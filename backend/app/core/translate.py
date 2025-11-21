from sqlalchemy.orm import Session

from app.dependencies import get_tmdb_interfaces
from app.core.templates import get_effective_templates
from app.models.episode import Episode
from app.logging.logger import log
from app.utils.tiered_settings import TieredSettings


def translate_episode(
        db: Session,
        episode: Episode,
        *,
        commit: bool = True,
    ) -> None:
    """
    Add the given Episode's translations to the Database.

    Args:
        db: Database to query and update.
        series_template: Template of the Series that can define
            translations.
        episode: Episode to translate and add translations to.
        commit: Whether to commit the translations to the database.
    """

    # Skip if there are no TMDbInterfaces
    if not get_tmdb_interfaces():
        return None

    # Evaluate per-library
    changed, series = False, episode.series
    libraries = series.libraries if series.libraries else [None]
    for library in libraries:
        # Get the Series and Episode Template
        g_template, s_template, e_template = get_effective_templates(
            series, episode, library,
        )

        # Get the highest priority translation setting
        translations = TieredSettings.resolve_singular_setting(
            getattr(g_template, 'translations', None),
            getattr(s_template, 'translations', None),
            series.translations,
            getattr(e_template, 'translations', None)
        )

        # Exit if there are no translations to add
        if not translations:
            continue

        # Look for and add each translation for this Episode
        for translation in translations:
            # Get this translation's data key and language code
            data_key = translation['data_key']
            language_code = translation['language_code']

            # Skip if this translation already exists
            if data_key in episode.translations:
                continue

            # Get new translation from TMDb, add to Episode
            for _, interface in get_tmdb_interfaces():
                translation = interface.get_episode_title(
                    series.as_series_info,
                    episode.as_episode_info,
                    language_code,
                )
                if (translation is None
                    or translation.lower() == episode.title.lower()):
                    log.debug(
                        f'{episode} no translation available for {language_code}'
                    )
                else:
                    episode.translations[data_key] = translation
                    log.debug((
                        f'{episode} translated {language_code} ({data_key}) as '
                        f'"{translation}"'
                    ))
                    changed = True
                    break

    # If any translations were added, commit updates to database
    if commit and changed:
        db.commit()

    return None
