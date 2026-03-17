"""Tests for application policies."""

import pytest
from pydantic import ValidationError

from bank_ingest.application.policies.error_policy import ErrorPolicy
from bank_ingest.application.policies.storage_policy import StoragePolicy


class TestStoragePolicy:
    def test_default_has_all_flags_true(self) -> None:
        policy = StoragePolicy.default()
        assert policy.store_raw is True
        assert policy.store_rendered is True
        assert policy.store_parsed is True
        assert policy.store_errors is True

    def test_minimal_only_enables_errors(self) -> None:
        policy = StoragePolicy.minimal()
        assert policy.store_raw is False
        assert policy.store_rendered is False
        assert policy.store_parsed is False
        assert policy.store_errors is True

    def test_custom_flags(self) -> None:
        policy = StoragePolicy(
            store_raw=True,
            store_rendered=False,
            store_parsed=True,
            store_errors=False,
        )
        assert policy.store_raw is True
        assert policy.store_rendered is False
        assert policy.store_parsed is True
        assert policy.store_errors is False

    def test_is_frozen(self) -> None:
        policy = StoragePolicy.default()
        with pytest.raises(ValidationError):
            policy.store_raw = False


class TestErrorPolicy:
    def test_default_continues_on_error(self) -> None:
        policy = ErrorPolicy.default()
        assert policy.continue_on_error is True
        assert policy.store_error_artifacts is True

    def test_strict_stops_on_error(self) -> None:
        policy = ErrorPolicy.strict()
        assert policy.continue_on_error is False
        assert policy.store_error_artifacts is True

    def test_custom_flags(self) -> None:
        policy = ErrorPolicy(continue_on_error=False, store_error_artifacts=False)
        assert policy.continue_on_error is False
        assert policy.store_error_artifacts is False

    def test_is_frozen(self) -> None:
        policy = ErrorPolicy.default()
        with pytest.raises(ValidationError):
            policy.continue_on_error = False
