from time import sleep

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.cards import create_episode_cards
from app.core.episodes import refresh_episode_data
from app.core.series import load_all_series_title_cards
from app.core.snapshot import take_snapshot
from app.core.sources import download_episode_source_images
from app.core.translate import translate_episode
from app.db.query import get_connection
from app.dependencies import PlexInterface
from app.exceptions import InvalidCardSettings
from app.logging.logger import Logger, log
from app.models.episode import Episode
from app.models.series import Series


def process_rating_key(
        db: Session,
        plex_interface: PlexInterface,
        key: int,
        new_only: bool = False,
        *,
        snapshot: bool = True,
        log: Logger = log,
    ) -> None:
    """
    Create the Title Card for the item associated with the given Plex
    Rating Key. This item can be a Show, Season, or Episode.

    Args:
        db: Database to query for Card details.
        plex_interface: Interface to Plex which has the details
            associated with this Key.
        key: Rating Key within Plex that identifies the item to create
            the Card(s) for.
        new_only: Whether to only process newly added Episodes. If False
            then ALL Episodes associated with the given Key will be
            reloaded.
        snapshot: Whether to take a snapshot of the database afterwards.
        log: Logger for all log messages.

    Raises:
        HTTPException (404): There are no details associated with the
            given Rating Key.
    """

    # Get details of each key from Plex, raise 404 if not found/invalid
    if len(details := plex_interface.get_episode_details(key, log=log)) == 0:
        raise HTTPException(
            status_code=404,
            detail=f'Rating key {key} does not correspond to any content'
        )
    log.debug(f'Identified {len(details)} entries from Rating Key {key}')

    # Process each set of details
    episodes_to_load: list[Episode] = []
    new_episodes: list[Episode] = []
    for series_info, episode_info, watched_status in details:
        # Find all matching Episodes, filter out false matches for other Series
        episodes = [
            episode
            for episode in
            db.query(Episode)
                .filter(episode_info.filter_conditions(Episode))
                .all()
            if episode.series.as_series_info == series_info
        ]

        # Episode does not exist, refresh episode data and try again
        if not episodes:
            # Try and find associated Series, skip if DNE
            log.trace((
                f'No Episode found for ({episode_info!r}) - refreshing Episode '
                f'data'
            ))
            series = (
                db.query(Series)
                    .filter(series_info.filter_conditions(Series))
                    .first()
            )
            if series is None:
                log.debug(f'Cannot find Series for {series_info}')
                continue

            # Series found, refresh data and look for Episode again
            sleep(5)
            new_episodes = refresh_episode_data(db, series, log=log)
            episodes = [
                episode
                for episode in
                db.query(Episode)
                    .filter(episode_info.filter_conditions(Episode))
                    .all()
                if episode.series.as_series_info == series_info
            ]
            if not episodes:
                log.info(f'Cannot find Episode for {series_info} {episode_info}')
                continue
        elif new_only and all(ep not in new_episodes for ep in episodes):
            continue

        # Get first Episode that matches this Series
        episode, found = None, False
        for episode in episodes:
            if episode.series.as_series_info == series_info:
                found = True
                break

        # If no match, exit
        if not found or not episode:
            log.info(f'Cannot find Episode for {series_info} {episode_info}')
            continue

        # Update Episode watched status
        episode.add_watched_status(watched_status, log=log)

        # Look for source, add translation, create card if source exists
        download_episode_source_images(db, episode, log=log)
        translate_episode(db, episode, log=log)
        try:
            new_cards = create_episode_cards(db, episode, log=log)
        except (HTTPException, InvalidCardSettings):
            log.exception(
                f'Unable to create Title Card for {episode} - skipping'
            )
            continue

        # Determine whether the Episode has any Kometa integration
        # associated with it
        integrate_with_kometa = any(
            lib['interface'] == 'Plex'
            and get_connection(db, lib['interface_id']).integrate_with_kometa
            for lib in episode.series.libraries
        )

        # Add this Episode to list of Episodes to load if Kometa
        # integration is not enabled (if Episode is not already queued);
        # or if there is a new Card and Kometa is enabled (to avoid
        # resetting overlays unnecessarily)
        if ((new_cards or not integrate_with_kometa)
            and episode not in episodes_to_load):
            episodes_to_load.append(episode)
            db.refresh(episode)

    # Load all Episodes of the same Series together
    for series in set(episode.series for episode in episodes_to_load):
        sub_episodes = [ep for ep in episodes_to_load if ep.series == series]
        load_all_series_title_cards(
            series, db, episodes=sub_episodes, raise_exc=False, log=log,
        )

    if snapshot:
        take_snapshot(db, log=log)
