"""Tests for FetchLabeledMessages use case."""

from datetime import UTC

import pytest

from bank_ingest.application.use_cases.fetch_labeled_messages import (
    FetchLabeledMessages,
)
from bank_ingest.domain.entities import SourceMessage
from bank_ingest.domain.exceptions import MessageSourceError
from unit.application.fakes import FakeLogger, FakeMessageSource


class TestFetchLabeledMessages:
    def test_returns_messages_from_source(self, source_message: SourceMessage) -> None:
        source = FakeMessageSource(messages=[source_message])
        logger = FakeLogger()
        use_case = FetchLabeledMessages(source=source, logger=logger)

        results = use_case.execute(label="Transacciones")

        assert results == [source_message]

    def test_logs_message_count(self, source_message: SourceMessage) -> None:
        source = FakeMessageSource(messages=[source_message])
        logger = FakeLogger()
        use_case = FetchLabeledMessages(source=source, logger=logger)

        use_case.execute(label="Transacciones")

        assert len(logger.infos) >= 1

    def test_returns_empty_list_when_no_messages(self) -> None:
        source = FakeMessageSource(messages=[])
        logger = FakeLogger()
        use_case = FetchLabeledMessages(source=source, logger=logger)

        results = use_case.execute(label="Transacciones")

        assert results == []

    def test_re_raises_message_source_error(self) -> None:
        source = FakeMessageSource(raise_error=True)
        logger = FakeLogger()
        use_case = FetchLabeledMessages(source=source, logger=logger)

        with pytest.raises(MessageSourceError):
            use_case.execute(label="Transacciones")

    def test_logs_error_before_re_raising(self) -> None:
        source = FakeMessageSource(raise_error=True)
        logger = FakeLogger()
        use_case = FetchLabeledMessages(source=source, logger=logger)

        with pytest.raises(MessageSourceError):
            use_case.execute(label="Transacciones")

        assert len(logger.errors) > 0

    def test_multiple_messages_returned(self, source_message: SourceMessage) -> None:
        from datetime import datetime

        from bank_ingest.domain.value_objects import MessageId

        msg2 = SourceMessage(
            id=MessageId(value="msg-002"),
            sender="banco@bac.cr",
            subject="Otra notificacion",
            body_html="<html><body>Other</body></html>",
            received_at=datetime(2024, 1, 16, 9, 0, tzinfo=UTC),
        )
        source = FakeMessageSource(messages=[source_message, msg2])
        logger = FakeLogger()
        use_case = FetchLabeledMessages(source=source, logger=logger)

        results = use_case.execute(label="Transacciones")

        assert len(results) == 2
