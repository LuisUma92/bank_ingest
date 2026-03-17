"""Shared pytest fixtures for application layer tests."""

from datetime import UTC, datetime

import pytest

from bank_ingest.domain.entities import (
    ClassificationResult,
    FinancialEvent,
    SourceMessage,
)
from bank_ingest.domain.enums import Bank, Currency, NotificationType, TransactionType
from bank_ingest.domain.value_objects import CardInfo, EventId, MessageId, Money


@pytest.fixture()
def message_id() -> MessageId:
    return MessageId(value="msg-001")


@pytest.fixture()
def event_id() -> EventId:
    return EventId(value="evt-001")


@pytest.fixture()
def source_message(message_id: MessageId) -> SourceMessage:
    return SourceMessage(
        id=message_id,
        sender="banco@bac.cr",
        subject="Notificacion de transaccion",
        body_html="<html><body>Transaction body</body></html>",
        received_at=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
    )


@pytest.fixture()
def classification() -> ClassificationResult:
    return ClassificationResult(
        bank=Bank.BAC,
        notification_type=NotificationType.TRANSACTION_NOTIFICATION,
    )


@pytest.fixture()
def financial_event(message_id: MessageId, event_id: EventId) -> FinancialEvent:
    return FinancialEvent(
        id=event_id,
        message_id=message_id,
        bank=Bank.BAC,
        event_type=NotificationType.TRANSACTION_NOTIFICATION,
        merchant="SUPER MAS",
        transaction_date=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
        card=CardInfo(brand="VISA", last4="1234"),
        authorization_code="AUTH123",
        transaction_type=TransactionType.PURCHASE,
        amount=Money(amount=5000, currency=Currency.CRC),
        raw_data={"merchant": "SUPER MAS"},
        created_at=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
    )
