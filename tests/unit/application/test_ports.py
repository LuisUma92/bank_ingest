"""Tests for new domain ports: ClassifierPort and ParserPort."""

import pytest

from bank_ingest.domain.entities import (
    ClassificationResult,
    FinancialEvent,
    SourceMessage,
)
from bank_ingest.domain.enums import Bank, NotificationType
from bank_ingest.domain.exceptions import ParsingError
from bank_ingest.domain.ports.classifier import ClassifierPort
from bank_ingest.domain.ports.parser import ParserPort


class ConcreteClassifier(ClassifierPort):
    def classify(self, message: SourceMessage) -> ClassificationResult | None:
        return ClassificationResult(
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )


class NullClassifier(ClassifierPort):
    def classify(self, message: SourceMessage) -> ClassificationResult | None:
        return None


class ConcreteParser(ParserPort):
    @property
    def bank(self) -> Bank:
        return Bank.BAC

    @property
    def notification_type(self) -> NotificationType:
        return NotificationType.TRANSACTION_NOTIFICATION

    def parse(self, message: SourceMessage) -> FinancialEvent:
        raise ParsingError(message.id.value, "not implemented in stub")


class TestClassifierPort:
    def test_concrete_classifier_can_be_instantiated(
        self, source_message: SourceMessage
    ) -> None:
        classifier = ConcreteClassifier()
        result = classifier.classify(source_message)
        assert result is not None
        assert result.bank == Bank.BAC

    def test_null_classifier_returns_none(self, source_message: SourceMessage) -> None:
        classifier = NullClassifier()
        result = classifier.classify(source_message)
        assert result is None

    def test_classifier_port_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            ClassifierPort()  # type: ignore[abstract]


class TestParserPort:
    def test_concrete_parser_exposes_bank_and_type(self) -> None:
        parser = ConcreteParser()
        assert parser.bank == Bank.BAC
        assert parser.notification_type == NotificationType.TRANSACTION_NOTIFICATION

    def test_parser_port_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            ParserPort()  # type: ignore[abstract]

    def test_parser_raises_parsing_error(self, source_message: SourceMessage) -> None:
        parser = ConcreteParser()
        with pytest.raises(ParsingError):
            parser.parse(source_message)
