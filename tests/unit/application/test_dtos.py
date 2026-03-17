"""Tests for application DTOs."""

import pytest
from pydantic import ValidationError

from bank_ingest.application.dtos import BatchProcessingResult, MessageProcessingResult
from bank_ingest.domain.enums import ProcessingResult
from bank_ingest.domain.value_objects import EventId, MessageId


class TestMessageProcessingResult:
    def test_processed_status(self) -> None:
        result = MessageProcessingResult(
            message_id=MessageId(value="msg-1"),
            status=ProcessingResult.PROCESSED,
            event_id=EventId(value="evt-1"),
            error=None,
        )
        assert result.status == ProcessingResult.PROCESSED
        assert result.event_id is not None
        assert result.error is None

    def test_failed_status(self) -> None:
        result = MessageProcessingResult(
            message_id=MessageId(value="msg-2"),
            status=ProcessingResult.FAILED,
            event_id=None,
            error="Parsing failed",
        )
        assert result.status == ProcessingResult.FAILED
        assert result.event_id is None
        assert result.error == "Parsing failed"

    def test_skipped_status(self) -> None:
        result = MessageProcessingResult(
            message_id=MessageId(value="msg-3"),
            status=ProcessingResult.SKIPPED,
            event_id=None,
            error=None,
        )
        assert result.status == ProcessingResult.SKIPPED

    def test_is_frozen(self) -> None:
        result = MessageProcessingResult(
            message_id=MessageId(value="msg-1"),
            status=ProcessingResult.PROCESSED,
            event_id=None,
            error=None,
        )
        with pytest.raises(ValidationError):
            result.status = ProcessingResult.FAILED


class TestBatchProcessingResult:
    def test_basic_counts(self) -> None:
        results = [
            MessageProcessingResult(
                message_id=MessageId(value="msg-1"),
                status=ProcessingResult.PROCESSED,
                event_id=EventId(value="evt-1"),
                error=None,
            ),
            MessageProcessingResult(
                message_id=MessageId(value="msg-2"),
                status=ProcessingResult.FAILED,
                event_id=None,
                error="error",
            ),
            MessageProcessingResult(
                message_id=MessageId(value="msg-3"),
                status=ProcessingResult.SKIPPED,
                event_id=None,
                error=None,
            ),
        ]
        batch = BatchProcessingResult(
            total=3,
            processed=1,
            failed=1,
            skipped=1,
            results=results,
        )
        assert batch.total == 3
        assert batch.processed == 1
        assert batch.failed == 1
        assert batch.skipped == 1
        assert len(batch.results) == 3

    def test_empty_batch(self) -> None:
        batch = BatchProcessingResult(
            total=0,
            processed=0,
            failed=0,
            skipped=0,
            results=[],
        )
        assert batch.total == 0
        assert batch.results == []

    def test_is_frozen(self) -> None:
        batch = BatchProcessingResult(
            total=0,
            processed=0,
            failed=0,
            skipped=0,
            results=[],
        )
        with pytest.raises(ValidationError):
            batch.total = 5
