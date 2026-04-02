

from datetime import datetime, timezone

from zoneinfo import ZoneInfo


def normalize_dates(d1: datetime, d2: datetime, /) -> tuple[datetime, datetime]:
    """
    Normalize the given dates to the same level of timezone-awareness.

    Args:
        d1: First date to normalize.
        d2: Second date to normalize.

    Returns:
        Tuple of the two normalized dates. The timezone-awareness of
        both dates will be the same (both have or both have not).
    """

    # If these two dates have the same timezone awareness, return as-is
    if (d1.tzinfo is None) == (d2.tzinfo is None):
        return d1, d2

    # There is a mismatch in their awareness, normalize both to UTC
    return d1.astimezone(ZoneInfo('UTC')), d2.astimezone(ZoneInfo('UTC'))
