"""Tests for BACTransactionNotificationParser."""

from datetime import datetime
from pathlib import Path

import pytest

from bank_ingest.adapters.parsers.bac.transaction_notification import (
    BACTransactionNotificationParser,
)
from bank_ingest.domain.entities import SourceMessage
from bank_ingest.domain.enums import (
    Bank,
    Currency,
    NotificationType,
    TransactionType,
)
from bank_ingest.domain.exceptions import ParsingError
from bank_ingest.domain.value_objects import MessageId

FIXTURE_PATH = (
    Path(__file__).resolve().parents[4]
    / "fixtures"
    / "bac_transaction_notification.html"
)


@pytest.fixture
def parser() -> BACTransactionNotificationParser:
    return BACTransactionNotificationParser()


@pytest.fixture
def fixture_html() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture
def source_message(fixture_html: str) -> SourceMessage:
    return SourceMessage(
        id=MessageId(value="msg-fixture-001"),
        sender="alertasynotificaciones@notificacionesbac.com",
        subject="Notificacion de transaccion",
        body_html=fixture_html,
        received_at=datetime(2026, 3, 16, 9, 0),
    )


class TestParserIdentity:
    """Verify parser declares correct bank and notification type."""

    def test_bank_is_bac(self, parser: BACTransactionNotificationParser) -> None:
        assert parser.bank == Bank.BAC

    def test_notification_type_is_transaction(
        self, parser: BACTransactionNotificationParser
    ) -> None:
        assert parser.notification_type == NotificationType.TRANSACTION_NOTIFICATION


class TestParseFixture:
    """Verify parser extracts all fields from the BAC fixture HTML."""

    def test_extracts_merchant(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.merchant == "CLINICA VETERINARIA GU"

    def test_extracts_transaction_date(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.transaction_date == datetime(2026, 3, 16, 8, 27)

    def test_extracts_card_brand(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.card.brand == "AMEX"

    def test_extracts_card_last4(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.card.last4 == "0000"

    def test_extracts_authorization_code(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.authorization_code == "000000"

    def test_extracts_transaction_type_purchase(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.transaction_type == TransactionType.PURCHASE

    def test_extracts_amount_in_cents(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.amount.amount == 1000000

    def test_extracts_currency(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.amount.currency == Currency.CRC

    def test_preserves_message_id(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.message_id.value == "msg-fixture-001"

    def test_sets_bank_to_bac(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.bank == Bank.BAC

    def test_sets_event_type(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.event_type == NotificationType.TRANSACTION_NOTIFICATION

    def test_generates_event_id(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert event.id.value  # non-empty UUID

    def test_raw_data_contains_extracted_rows(
        self,
        parser: BACTransactionNotificationParser,
        source_message: SourceMessage,
    ) -> None:
        event = parser.parse(source_message)
        assert isinstance(event.raw_data, dict)
        assert "Comercio:" in event.raw_data


class TestParserErrors:
    """Verify parser raises ParsingError for malformed input."""

    def test_raises_on_empty_table(
        self, parser: BACTransactionNotificationParser
    ) -> None:
        message = SourceMessage(
            id=MessageId(value="msg-empty"),
            sender="test@bac.com",
            subject="test",
            body_html="<html><body><p>No table here</p></body></html>",
            received_at=datetime(2026, 1, 1),
        )
        with pytest.raises(ParsingError):
            parser.parse(message)

    def test_raises_on_missing_merchant(
        self, parser: BACTransactionNotificationParser
    ) -> None:
        html = """<table>
        <tr><td>Fecha:</td><td>Mar 16, 2026, 08:27</td></tr>
        <tr><td>AMEX</td><td>***********0000</td></tr>
        <tr><td>Autorización:</td><td>123456</td></tr>
        <tr><td>Tipo de Transacción:</td><td>COMPRA</td></tr>
        <tr><td>Monto:</td><td>CRC 10,000.00</td></tr>
        </table>"""
        message = SourceMessage(
            id=MessageId(value="msg-no-merchant"),
            sender="test@bac.com",
            subject="test",
            body_html=html,
            received_at=datetime(2026, 1, 1),
        )
        with pytest.raises(ParsingError):
            parser.parse(message)

    def test_raises_on_missing_amount(
        self, parser: BACTransactionNotificationParser
    ) -> None:
        html = """<table>
        <tr><td>Comercio:</td><td>STORE</td></tr>
        <tr><td>Fecha:</td><td>Mar 16, 2026, 08:27</td></tr>
        <tr><td>AMEX</td><td>***********0000</td></tr>
        <tr><td>Autorización:</td><td>123456</td></tr>
        <tr><td>Tipo de Transacción:</td><td>COMPRA</td></tr>
        </table>"""
        message = SourceMessage(
            id=MessageId(value="msg-no-amount"),
            sender="test@bac.com",
            subject="test",
            body_html=html,
            received_at=datetime(2026, 1, 1),
        )
        with pytest.raises(ParsingError):
            parser.parse(message)
