import contextlib
from typing import Any, TypeVar

from plexapi.video import Episode as PlexEpisode

from app.info.episode import EpisodeInfo


_RefT = TypeVar('_RefT')
_SearchT = TypeVar('_SearchT')


def _to_episode_info(item: Any) -> EpisodeInfo:
    """
    Normalize any supported episode info type to an EpisodeInfo suitable
    for index- and ID-based matching.

    Interface-specific IDs (plex_id, emby_id, jellyfin_id) are not set on
    the returned object, so only cross-platform IDs (IMDb, TMDb, TVDb,
    TVRage) and season/episode indices drive equality comparisons.

    Args:
        item: An EpisodeInfo, plexapi.video.Episode, Emby EpisodeDetails,
            or Jellyfin ItemDetails object.

    Returns:
        EpisodeInfo built purely from cross-platform metadata.

    Raises:
        TypeError: When `item` is not a recognised episode info type.
    """

    if isinstance(item, EpisodeInfo):
        return item

    if isinstance(item, PlexEpisode):
        if item.parentIndex is None or item.index is None:
            raise ValueError(
                f'Cannot normalize PlexEpisode {item!r}: missing season/episode index'
            )
        ep = EpisodeInfo(
            title=item.title or '',
            season_number=int(item.parentIndex),
            episode_number=int(item.index),
            airdate=item.originallyAvailableAt,
        )
        for guid in item.guids:
            if 'imdb://' in guid.id:
                ep.set_imdb_id(guid.id[len('imdb://'):])
            elif 'tmdb://' in guid.id:
                ep.set_tmdb_id(int(guid.id[len('tmdb://'):]))
            elif 'tvdb://' in guid.id:
                ep.set_tvdb_id(int(guid.id[len('tvdb://'):]))
        return ep

    # Duck-typed path for Emby EpisodeDetails and Jellyfin ItemDetails,
    # which share the same set of relevant attributes.
    if (hasattr(item, 'parent_index_number')
        and hasattr(item, 'index_number')
        and hasattr(item, 'provider_ids')
        and hasattr(item, 'name')
    ):
        provider_ids: dict[str, str] = item.provider_ids

        # TMDb IDs from Emby/Jellyfin may be formatted as '{id}-{name}'
        # or '../{name}/{id}'; extract the numeric part only.
        tmdb_id: int | None = None
        if (tmdb_raw := provider_ids.get('Tmdb')) is not None:
            with contextlib.suppress(ValueError):
                if '-' in tmdb_raw:
                    tmdb_id = int(tmdb_raw.split('-', maxsplit=1)[0])
                elif '/' in tmdb_raw:
                    tmdb_id = int(tmdb_raw.rsplit('/', maxsplit=1)[-1])
                else:
                    tmdb_id = int(tmdb_raw)

        tvdb_id: int | None = None
        if (tvdb_raw := provider_ids.get('Tvdb')) is not None:
            with contextlib.suppress(ValueError):
                tvdb_id = int(tvdb_raw)

        tvrage_id: int | None = None
        if (tvrage_raw := provider_ids.get('TvRage')) is not None:
            with contextlib.suppress(ValueError):
                tvrage_id = int(tvrage_raw)

        return EpisodeInfo(
            title=item.name,
            season_number=item.parent_index_number,
            episode_number=item.index_number,
            imdb_id=provider_ids.get('Imdb'),
            tmdb_id=tmdb_id,
            tvdb_id=tvdb_id,
            tvrage_id=tvrage_id,
            airdate=item.premiere_date,
        )

    raise TypeError(
        f'Cannot normalize {type(item).__qualname__!r} to EpisodeInfo; '
        f'expected EpisodeInfo, plexapi.video.Episode, '
        f'app.interfaces.schemas.emby.EpisodeDetails, or '
        f'app.interfaces.schemas.jellyfin.ItemDetails'
    )


def match_episode_infos(
        references: list[_RefT],
        searches: list[_SearchT],
    ) -> tuple[list[tuple[_RefT, list[_SearchT]]], list[_SearchT]]:
    """
    Map episode info objects from `searches` onto episode info objects in
    `references`.

    Cardinality is many-search-to-one-reference: multiple `searches`
    items may be associated with the same `references` item (e.g. when
    an interface returns duplicate entries for the same episode). Each
    `searches` item is consumed by at most one `references` item — the
    first one it matches.

    Supported types for both lists:
        - app.info.episode.EpisodeInfo
        - plexapi.video.Episode
        - app.interfaces.schemas.emby.EpisodeDetails
        - app.interfaces.schemas.jellyfin.ItemDetails

    Args:
        references: Driving list of episode info objects. Every element
            appears exactly once in the returned pairs, even when it has
            no matching search items.
        searches: Pool of episode info objects to match against the
            references.

    Returns:
        A two-element tuple:

        - ``matched``: a list of ``(reference, matches)`` pairs
          preserving the order of `references`. ``matches`` is the
          (possibly empty) list of `searches` items that correspond to
          that reference.
        - ``unmatched``: the subset of `searches` items that were not
          associated with any reference, in their original order.

    Example::

        matched, unmatched = match_episode_infos(episode_infos, plex_episodes)
        for episode_info, plex_matches in matched:
            for plex_ep in plex_matches:
                ...
        for leftover in unmatched:
            log.warning(f'No reference found for {leftover}')
    """

    ref_infos = [_to_episode_info(ref) for ref in references]
    match_lists: list[list[_SearchT]] = [[] for _ in references]
    unmatched: list[_SearchT] = []

    for search in searches:
        search_info = _to_episode_info(search)
        for i, ref_info in enumerate(ref_infos):
            if ref_info == search_info:
                match_lists[i].append(search)
                break
        else:
            unmatched.append(search)

    return list(zip(references, match_lists)), unmatched
