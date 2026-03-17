"""Date parsing utilities for BAC bank email strings."""

from datetime import datetime

# Mapping of month abbreviations (Spanish and English) to English equivalents.
# English entries that differ from Spanish are included so the lookup covers both.
_MONTH_TO_ENGLISH: dict[str, str] = {
    "Ene": "Jan",
    "Jan": "Jan",
    "Feb": "Feb",
    "Mar": "Mar",
    "Abr": "Apr",
    "Apr": "Apr",
    "May": "May",
    "Jun": "Jun",
    "Jul": "Jul",
    "Ago": "Aug",
    "Aug": "Aug",
    "Sep": "Sep",
    "Oct": "Oct",
    "Nov": "Nov",
    "Dic": "Dec",
    "Dec": "Dec",
}

# Expected format after normalization: "Mon DD, YYYY, HH:MM"
_BAC_DATE_FORMAT = "%b %d, %Y, %H:%M"


def parse_bac_date(raw: str) -> datetime:
    """Parse a BAC date string into a datetime object.

    Handles both English and Spanish month abbreviations.
    Input format: "Mar 16, 2026, 08:27" or "Ene 22, 2025, 07:45"
    Strips leading/trailing whitespace before parsing.

    Args:
        raw: Raw date string from the BAC email.

    Returns:
        A datetime object with year, month, day, hour, and minute populated.

    Raises:
        ValueError: If the string cannot be parsed (invalid format or month).
    """
    stripped = raw.strip()

    if not stripped:
        raise ValueError(f"Cannot parse empty date string: {raw!r}")

    normalized = _normalize_month(stripped)

    try:
        return datetime.strptime(normalized, _BAC_DATE_FORMAT)
    except ValueError as exc:
        raise ValueError(f"Cannot parse BAC date string {raw!r}: {exc}") from exc


def _normalize_month(date_str: str) -> str:
    """Replace a Spanish month abbreviation with the English equivalent.

    Args:
        date_str: Date string that may start with a Spanish month abbreviation.

    Returns:
        Date string with Spanish abbreviation replaced by English, if applicable.

    Raises:
        ValueError: If the month abbreviation is unrecognized.
    """
    parts = date_str.split(" ", 1)
    if len(parts) < 2:
        raise ValueError(f"Cannot extract month from {date_str!r}")

    month_candidate = parts[0]

    # Dict contains both Spanish→English and English→English mappings
    if month_candidate in _MONTH_TO_ENGLISH:
        return _MONTH_TO_ENGLISH[month_candidate] + " " + parts[1]

    raise ValueError(
        f"Unknown month abbreviation {month_candidate!r} in date string {date_str!r}"
    )
