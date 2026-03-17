"""Tests for domain exceptions."""

import pytest

from bank_ingest.domain.exceptions import (
    BankIngestError,
    ClassificationError,
    MessageSourceError,
    ParsingError,
    StorageError,
)


class TestBankIngestError:
    def test_is_exception(self):
        err = BankIngestError("something failed")
        assert isinstance(err, Exception)

    def test_message_preserved(self):
        err = BankIngestError("base error")
        assert "base error" in str(err)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(BankIngestError):
            raise BankIngestError("test")

    def test_caught_as_exception(self):
        with pytest.raises(Exception):
            raise BankIngestError("test")


class TestParsingError:
    def test_is_bank_ingest_error(self):
        err = ParsingError(message_id="msg-001", reason="bad HTML")
        assert isinstance(err, BankIngestError)

    def test_stores_message_id(self):
        err = ParsingError(message_id="msg-001", reason="bad HTML")
        assert err.message_id == "msg-001"

    def test_stores_reason(self):
        err = ParsingError(message_id="msg-001", reason="could not find amount")
        assert err.reason == "could not find amount"

    def test_str_contains_message_id(self):
        err = ParsingError(message_id="msg-xyz", reason="parse failed")
        assert "msg-xyz" in str(err)

    def test_str_contains_reason(self):
        err = ParsingError(message_id="msg-xyz", reason="parse failed")
        assert "parse failed" in str(err)

    def test_can_be_raised_and_caught_as_parsing_error(self):
        with pytest.raises(ParsingError):
            raise ParsingError(message_id="m", reason="r")

    def test_can_be_caught_as_bank_ingest_error(self):
        with pytest.raises(BankIngestError):
            raise ParsingError(message_id="m", reason="r")

    def test_empty_message_id_allowed(self):
        # Domain errors should not restrict their own constructor
        err = ParsingError(message_id="", reason="reason")
        assert err.message_id == ""

    def test_empty_reason_allowed(self):
        err = ParsingError(message_id="msg-001", reason="")
        assert err.reason == ""


class TestClassificationError:
    def test_is_bank_ingest_error(self):
        err = ClassificationError(message_id="msg-001", reason="unknown bank")
        assert isinstance(err, BankIngestError)

    def test_stores_message_id(self):
        err = ClassificationError(message_id="msg-abc", reason="no match")
        assert err.message_id == "msg-abc"

    def test_stores_reason(self):
        err = ClassificationError(message_id="msg-abc", reason="no match")
        assert err.reason == "no match"

    def test_str_contains_message_id(self):
        err = ClassificationError(message_id="msg-abc", reason="no match")
        assert "msg-abc" in str(err)

    def test_str_contains_reason(self):
        err = ClassificationError(message_id="msg-abc", reason="no match")
        assert "no match" in str(err)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(ClassificationError):
            raise ClassificationError(message_id="m", reason="r")

    def test_can_be_caught_as_bank_ingest_error(self):
        with pytest.raises(BankIngestError):
            raise ClassificationError(message_id="m", reason="r")


class TestStorageError:
    def test_is_bank_ingest_error(self):
        err = StorageError("disk full")
        assert isinstance(err, BankIngestError)

    def test_message_preserved(self):
        err = StorageError("disk full")
        assert "disk full" in str(err)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(StorageError):
            raise StorageError("write failed")

    def test_can_be_caught_as_bank_ingest_error(self):
        with pytest.raises(BankIngestError):
            raise StorageError("write failed")

    def test_can_be_caught_as_exception(self):
        with pytest.raises(Exception):
            raise StorageError("write failed")


class TestMessageSourceError:
    def test_is_bank_ingest_error(self):
        err = MessageSourceError("connection refused")
        assert isinstance(err, BankIngestError)

    def test_message_preserved(self):
        err = MessageSourceError("gmail API down")
        assert "gmail API down" in str(err)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(MessageSourceError):
            raise MessageSourceError("fetch failed")

    def test_can_be_caught_as_bank_ingest_error(self):
        with pytest.raises(BankIngestError):
            raise MessageSourceError("fetch failed")

    def test_can_be_caught_as_exception(self):
        with pytest.raises(Exception):
            raise MessageSourceError("fetch failed")


class TestExceptionHierarchy:
    def test_parsing_error_not_classification_error(self):
        err = ParsingError(message_id="m", reason="r")
        assert not isinstance(err, ClassificationError)

    def test_classification_error_not_parsing_error(self):
        err = ClassificationError(message_id="m", reason="r")
        assert not isinstance(err, ParsingError)

    def test_storage_error_not_message_source_error(self):
        err = StorageError("s")
        assert not isinstance(err, MessageSourceError)

    def test_message_source_error_not_storage_error(self):
        err = MessageSourceError("s")
        assert not isinstance(err, StorageError)
