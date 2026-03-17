"""Tests for shared.datetime — BAC date string parsing."""

from datetime import datetime

import pytest

from bank_ingest.shared.datetime import parse_bac_date


class TestParseBacDate:
    """Unit tests for parse_bac_date."""

    # --- English month abbreviations ---

    def test_english_march(self):
        result = parse_bac_date("Mar 16, 2026, 08:27")
        assert result == datetime(2026, 3, 16, 8, 27)

    def test_english_january(self):
        result = parse_bac_date("Jan 22, 2025, 07:45")
        assert result == datetime(2025, 1, 22, 7, 45)

    def test_english_december(self):
        result = parse_bac_date("Dec 31, 2024, 23:59")
        assert result == datetime(2024, 12, 31, 23, 59)

    def test_english_all_months(self):
        months = [
            ("Jan", 1),
            ("Feb", 2),
            ("Mar", 3),
            ("Apr", 4),
            ("May", 5),
            ("Jun", 6),
            ("Jul", 7),
            ("Aug", 8),
            ("Sep", 9),
            ("Oct", 10),
            ("Nov", 11),
            ("Dec", 12),
        ]
        for abbr, expected_month in months:
            result = parse_bac_date(f"{abbr} 15, 2025, 12:00")
            assert result.month == expected_month, f"Failed for {abbr}"

    # --- Spanish month abbreviations ---

    def test_spanish_january_ene(self):
        result = parse_bac_date("Ene 22, 2025, 07:45")
        assert result == datetime(2025, 1, 22, 7, 45)

    def test_spanish_april_abr(self):
        result = parse_bac_date("Abr 10, 2025, 14:30")
        assert result == datetime(2025, 4, 10, 14, 30)

    def test_spanish_august_ago(self):
        result = parse_bac_date("Ago 05, 2025, 09:00")
        assert result == datetime(2025, 8, 5, 9, 0)

    def test_spanish_december_dic(self):
        result = parse_bac_date("Dic 25, 2025, 00:00")
        assert result == datetime(2025, 12, 25, 0, 0)

    def test_spanish_all_months(self):
        mapping = [
            ("Ene", 1),
            ("Feb", 2),
            ("Mar", 3),
            ("Abr", 4),
            ("May", 5),
            ("Jun", 6),
            ("Jul", 7),
            ("Ago", 8),
            ("Sep", 9),
            ("Oct", 10),
            ("Nov", 11),
            ("Dic", 12),
        ]
        for abbr, expected_month in mapping:
            result = parse_bac_date(f"{abbr} 15, 2025, 12:00")
            assert result.month == expected_month, f"Failed for Spanish month {abbr}"

    # --- Whitespace edge cases ---

    def test_leading_space(self):
        """BAC fixture has a leading space: ' Mar 16, 2026, 08:27'."""
        result = parse_bac_date(" Mar 16, 2026, 08:27")
        assert result == datetime(2026, 3, 16, 8, 27)

    def test_trailing_space(self):
        result = parse_bac_date("Mar 16, 2026, 08:27 ")
        assert result == datetime(2026, 3, 16, 8, 27)

    def test_leading_and_trailing_spaces(self):
        result = parse_bac_date("  Mar 16, 2026, 08:27  ")
        assert result == datetime(2026, 3, 16, 8, 27)

    # --- Return type ---

    def test_returns_datetime(self):
        result = parse_bac_date("Mar 16, 2026, 08:27")
        assert isinstance(result, datetime)

    def test_fields_are_correct(self):
        result = parse_bac_date("Jun 01, 2025, 15:45")
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 1
        assert result.hour == 15
        assert result.minute == 45

    # --- Error cases ---

    def test_invalid_month_raises(self):
        with pytest.raises(ValueError):
            parse_bac_date("Xyz 16, 2026, 08:27")

    def test_completely_invalid_string_raises(self):
        with pytest.raises(ValueError):
            parse_bac_date("not a date at all")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_bac_date("")

    def test_wrong_format_raises(self):
        with pytest.raises(ValueError):
            parse_bac_date("2026-03-16 08:27:00")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            parse_bac_date("   ")
