from sqlalchemy.orm import Session

from app.core.card_registry import CARD_CLASSES, DEFAULT_BLUR_PROFILES
from app.models.connection import Connection
from app.schemas.preferences import EpisodeDataSourceToggle
from app.settings import settings


def get_episode_data_sources(db: Session) -> list[EpisodeDataSourceToggle]:
    """
    Get the list of Episode data sources.

    Args:
        db: Database to query for Connections

    Returns:
        List of episode data source details for all enabled Connections.
    """

    return [
        dict(
            interface=connection.interface_type,
            interface_id=connection.id,
            name=connection.name,
            selected=settings.episode_data_source == connection.id,
        )
        for connection in db.query(Connection).all()
    ]


def apply_card_type_blur_profiles() -> None:
    """
    Apply the global default blur profiles to all card type classes
    which have non-default specifications.
    """

    # Apply custom profile mappings
    for identifier, profile in settings.default_blur_profiles.items():
        if identifier not in CARD_CLASSES:
            continue

        CARD_CLASSES[identifier].BLUR_PROFILE = profile

    # Reset default profiles
    for card_type, blur in DEFAULT_BLUR_PROFILES.items():
        if card_type not in settings.default_blur_profiles:
            CARD_CLASSES[card_type].BLUR_PROFILE = blur
