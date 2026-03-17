"""Amount parsing and formatting utilities for BAC bank email strings."""

import re

# Pattern: "CRC 72,000.00" or "USD 1,250.50"
_AMOUNT_PATTERN = re.compile(
    r"^(?P<currency>[A-Z]{3})\s+(?P<amount>\d[\d,]*(?:\.\d{1,2})?)$"
)


def parse_amount_string(raw: str) -> tuple[int, str]:
    """Parse a BAC amount string into (cents, currency_code).

    Input format: "CRC 72,000.00" or "USD 1,250.50"
    Returns: (7200000, "CRC") or (125050, "USD")

    Converts the decimal amount to integer cents (multiply by 100).
    Strips commas used for grouping. Handles amounts with no decimal part
    or a single decimal digit.

    Args:
        raw: Raw amount string from the BAC email.

    Returns:
        A tuple of (amount_in_cents: int, currency_code: str).

    Raises:
        ValueError: If the string is empty, malformed, or contains a negative amount.
    """
    if not raw or not raw.strip():
        raise ValueError(f"Cannot parse empty amount string: {raw!r}")

    if "-" in raw:
        raise ValueError(f"Negative amounts are not supported: {raw!r}")

    match = _AMOUNT_PATTERN.match(raw.strip())
    if not match:
        raise ValueError(
            f"Cannot parse amount string {raw!r}. "
            "Expected format: 'CRC 72,000.00' or 'USD 1,250.50'"
        )

    currency = match.group("currency")
    amount_str = match.group("amount").replace(",", "")

    cents = _to_cents(amount_str, raw)
    return cents, currency


def _to_cents(amount_str: str, original: str) -> int:
    """Convert a decimal string to integer cents.

    Args:
        amount_str: Cleaned numeric string (no grouping commas), e.g. "72000.00".
        original: Original raw string for error messages.

    Returns:
        Integer cent value.

    Raises:
        ValueError: If the string cannot be converted.
    """
    if "." in amount_str:
        integer_part, decimal_part = amount_str.split(".", 1)
        # Pad single-digit decimal to 2 digits (e.g. ".5" → "50")
        decimal_part = (decimal_part + "0")[:2]
    else:
        integer_part = amount_str
        decimal_part = "00"

    try:
        return int(integer_part) * 100 + int(decimal_part)
    except ValueError as exc:
        raise ValueError(f"Cannot convert amount {original!r} to cents: {exc}") from exc


def cents_to_display(amount: int, currency: str) -> str:
    """Format an integer cent value back to a display string.

    Input: (7200000, "CRC")
    Output: "CRC 72,000.00"

    Args:
        amount: Amount in cents (non-negative integer).
        currency: ISO 4217 currency code, e.g. "CRC" or "USD".

    Returns:
        Formatted amount string matching BAC email format.

    Raises:
        ValueError: If amount is negative.
    """
    if amount < 0:
        raise ValueError(f"Amount must be non-negative, got {amount}")
    whole = amount // 100
    cents = amount % 100
    formatted_whole = f"{whole:,}"
    return f"{currency} {formatted_whole}.{cents:02d}"
