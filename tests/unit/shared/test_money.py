"""Tests for shared.money — BAC amount string parsing and formatting."""

import pytest

from bank_ingest.shared.money import cents_to_display, parse_amount_string


class TestParseAmountString:
    """Unit tests for parse_amount_string."""

    # --- Happy path ---

    def test_crc_amount(self):
        cents, currency = parse_amount_string("CRC 72,000.00")
        assert cents == 7_200_000
        assert currency == "CRC"

    def test_usd_amount(self):
        cents, currency = parse_amount_string("USD 1,250.50")
        assert cents == 125_050
        assert currency == "USD"

    def test_small_usd_amount(self):
        cents, currency = parse_amount_string("USD 0.99")
        assert cents == 99
        assert currency == "USD"

    def test_fixture_amount(self):
        """Matches amount from the BAC fixture: CRC 10,000.00."""
        cents, currency = parse_amount_string("CRC 10,000.00")
        assert cents == 1_000_000
        assert currency == "CRC"

    def test_no_grouping_comma(self):
        cents, currency = parse_amount_string("USD 100.00")
        assert cents == 10_000
        assert currency == "USD"

    def test_large_amount_multiple_commas(self):
        cents, currency = parse_amount_string("CRC 1,000,000.00")
        assert cents == 100_000_000
        assert currency == "CRC"

    def test_zero_amount(self):
        cents, currency = parse_amount_string("CRC 0.00")
        assert cents == 0
        assert currency == "CRC"

    # --- Edge cases: missing or incomplete decimals ---

    def test_no_decimal_part(self):
        """'CRC 1000' — treated as zero cents."""
        cents, currency = parse_amount_string("CRC 1000")
        assert cents == 100_000
        assert currency == "CRC"

    def test_single_decimal_digit(self):
        """'CRC 1000.5' — one decimal digit padded to two."""
        cents, currency = parse_amount_string("CRC 1000.5")
        assert cents == 100_050
        assert currency == "CRC"

    # --- Different currencies ---

    def test_eur_currency(self):
        cents, currency = parse_amount_string("EUR 500.00")
        assert cents == 50_000
        assert currency == "EUR"

    def test_returns_tuple(self):
        result = parse_amount_string("USD 1.00")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_currency_code_is_string(self):
        _, currency = parse_amount_string("USD 1.00")
        assert isinstance(currency, str)

    def test_cents_is_int(self):
        cents, _ = parse_amount_string("USD 1.00")
        assert isinstance(cents, int)

    # --- Error cases ---

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_amount_string("")

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError):
            parse_amount_string("USD -100.00")

    def test_missing_currency_raises(self):
        with pytest.raises(ValueError):
            parse_amount_string("100.00")

    def test_invalid_amount_raises(self):
        with pytest.raises(ValueError):
            parse_amount_string("USD abc.de")

    def test_more_than_two_decimal_digits_raises(self):
        """Amounts with >2 decimal digits are rejected (no silent truncation)."""
        with pytest.raises(ValueError):
            parse_amount_string("USD 1.999")


class TestCentsToDisplay:
    """Unit tests for cents_to_display."""

    def test_crc_formatting(self):
        assert cents_to_display(7_200_000, "CRC") == "CRC 72,000.00"

    def test_usd_formatting(self):
        assert cents_to_display(125_050, "USD") == "USD 1,250.50"

    def test_fixture_amount_formatting(self):
        assert cents_to_display(1_000_000, "CRC") == "CRC 10,000.00"

    def test_zero_cents(self):
        assert cents_to_display(0, "CRC") == "CRC 0.00"

    def test_small_amount(self):
        assert cents_to_display(99, "USD") == "USD 0.99"

    def test_large_amount(self):
        assert cents_to_display(100_000_000, "CRC") == "CRC 1,000,000.00"

    def test_returns_string(self):
        result = cents_to_display(100, "USD")
        assert isinstance(result, str)

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            cents_to_display(-1, "USD")

    def test_roundtrip(self):
        """parse → display → parse should be consistent."""
        original = "USD 1,250.50"
        cents, currency = parse_amount_string(original)
        assert cents_to_display(cents, currency) == original
