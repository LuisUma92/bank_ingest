"""Tests for ParseMessage use case."""

import pytest

from bank_ingest.application.use_cases.parse_message import ParseMessage
from bank_ingest.domain.entities import (
    ClassificationResult,
    FinancialEvent,
    SourceMessage,
)
from bank_ingest.domain.enums import Bank, NotificationType
from bank_ingest.domain.exceptions import ParsingError
from unit.application.fakes import FakeLogger, FakeParser


class TestParseMessage:
    def test_returns_financial_event_for_registered_parser(
        self,
        source_message: SourceMessage,
        classification: ClassificationResult,
        financial_event: FinancialEvent,
    ) -> None:
        parser = FakeParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        use_case = ParseMessage(
            parsers={(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): parser},
            logger=FakeLogger(),
        )

        result = use_case.execute(source_message, classification)

        assert result == financial_event

    def test_raises_parsing_error_when_no_parser_registered(
        self,
        source_message: SourceMessage,
        classification: ClassificationResult,
    ) -> None:
        use_case = ParseMessage(parsers={}, logger=FakeLogger())

        with pytest.raises(ParsingError) as exc_info:
            use_case.execute(source_message, classification)

        assert exc_info.value.message_id == source_message.id.value

    def test_propagates_parsing_error_from_parser(
        self,
        source_message: SourceMessage,
        classification: ClassificationResult,
        financial_event: FinancialEvent,
    ) -> None:
        class FailingParser(FakeParser):
            def parse(self, message: SourceMessage) -> FinancialEvent:
                raise ParsingError(message.id.value, "extraction failed")

        parser = FailingParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        use_case = ParseMessage(
            parsers={(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): parser},
            logger=FakeLogger(),
        )

        with pytest.raises(ParsingError) as exc_info:
            use_case.execute(source_message, classification)

        assert "extraction failed" in exc_info.value.reason

    def test_logs_parsing_success(
        self,
        source_message: SourceMessage,
        classification: ClassificationResult,
        financial_event: FinancialEvent,
    ) -> None:
        parser = FakeParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        logger = FakeLogger()
        use_case = ParseMessage(
            parsers={(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): parser},
            logger=logger,
        )

        use_case.execute(source_message, classification)

        assert len(logger.infos) > 0 or len(logger.debugs) > 0

    def test_uses_correct_parser_by_bank_and_type(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
    ) -> None:
        bac_classification = ClassificationResult(
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        bac_parser = FakeParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        use_case = ParseMessage(
            parsers={(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): bac_parser},
            logger=FakeLogger(),
        )

        result = use_case.execute(source_message, bac_classification)

        assert result == financial_event
