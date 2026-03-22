"""Shared fixtures for persistence integration tests."""

from collections.abc import Generator
from datetime import datetime

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from bank_ingest.adapters.outbound.persistence.sqlalchemy.base import Base
from bank_ingest.domain.entities import FinancialEvent
from bank_ingest.domain.enums import (
    Bank,
    Currency,
    NotificationType,
    TransactionType,
)
from bank_ingest.domain.value_objects import CardInfo, EventId, MessageId, Money


@pytest.fixture
def engine() -> Engine:
    """Create an in-memory SQLite engine with all tables."""
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    """Create a session bound to the in-memory engine, rolled back after test."""
    with Session(engine) as sess:
        yield sess


@pytest.fixture
def sample_event() -> FinancialEvent:
    """A complete FinancialEvent for testing persistence."""
    return FinancialEvent(
        id=EventId(value="evt-001"),
        message_id=MessageId(value="msg-abc"),
        bank=Bank.BAC,
        event_type=NotificationType.TRANSACTION_NOTIFICATION,
        merchant="AMAZON",
        transaction_date=datetime(2025, 3, 15, 14, 30, 0),
        card=CardInfo(brand="VISA", last4="1234"),
        authorization_code="AUTH001",
        transaction_type=TransactionType.PURCHASE,
        amount=Money(amount=150000, currency=Currency.CRC),
        raw_data={"original": "test", "nested": {"key": "value"}},
        created_at=datetime(2025, 3, 15, 14, 35, 0),
    )
