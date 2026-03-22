"""Integration tests for SqlAlchemyEventRepository and UnitOfWork."""

from datetime import datetime

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from bank_ingest.adapters.outbound.persistence.sqlalchemy.repository import (
    SqlAlchemyEventRepository,
)
from bank_ingest.adapters.outbound.persistence.sqlalchemy.uow import UnitOfWork
from bank_ingest.domain.entities import FinancialEvent
from bank_ingest.domain.enums import (
    Bank,
    Currency,
    NotificationType,
    TransactionType,
)
from bank_ingest.domain.value_objects import CardInfo, EventId, MessageId, Money


class TestSaveAndFindById:
    def test_save_and_find_by_id(
        self, session: Session, sample_event: FinancialEvent
    ) -> None:
        repo = SqlAlchemyEventRepository(session)
        repo.save(sample_event)
        session.flush()

        found = repo.find_by_id(sample_event.id)
        assert found is not None
        assert found.id.value == sample_event.id.value
        assert found.merchant == "AMAZON"

    def test_find_by_id_returns_none_when_not_found(self, session: Session) -> None:
        repo = SqlAlchemyEventRepository(session)
        result = repo.find_by_id(EventId(value="nonexistent"))
        assert result is None


class TestFindByMessageId:
    def test_find_by_message_id(
        self, session: Session, sample_event: FinancialEvent
    ) -> None:
        repo = SqlAlchemyEventRepository(session)
        repo.save(sample_event)
        session.flush()

        results = repo.find_by_message_id(sample_event.message_id)
        assert len(results) == 1
        assert results[0].message_id.value == "msg-abc"

    def test_find_by_message_id_returns_empty_list(self, session: Session) -> None:
        repo = SqlAlchemyEventRepository(session)
        results = repo.find_by_message_id(MessageId(value="no-such-msg"))
        assert results == []


class TestExists:
    def test_exists_returns_true(
        self, session: Session, sample_event: FinancialEvent
    ) -> None:
        repo = SqlAlchemyEventRepository(session)
        repo.save(sample_event)
        session.flush()

        assert repo.exists(sample_event.id) is True

    def test_exists_returns_false(self, session: Session) -> None:
        repo = SqlAlchemyEventRepository(session)
        assert repo.exists(EventId(value="nonexistent")) is False


class TestIdempotentSave:
    def test_save_idempotent(
        self, session: Session, sample_event: FinancialEvent
    ) -> None:
        repo = SqlAlchemyEventRepository(session)
        repo.save(sample_event)
        session.flush()
        repo.save(sample_event)
        session.flush()

        results = repo.find_by_message_id(sample_event.message_id)
        assert len(results) == 1


class TestRoundTrip:
    def test_round_trip_all_fields(
        self, session: Session, sample_event: FinancialEvent
    ) -> None:
        repo = SqlAlchemyEventRepository(session)
        repo.save(sample_event)
        session.flush()

        found = repo.find_by_id(sample_event.id)
        assert found is not None
        assert found.id.value == sample_event.id.value
        assert found.message_id.value == sample_event.message_id.value
        assert found.bank == Bank.BAC
        assert found.event_type == NotificationType.TRANSACTION_NOTIFICATION
        assert found.merchant == "AMAZON"
        assert found.transaction_date == datetime(2025, 3, 15, 14, 30, 0)
        assert found.card.brand == "VISA"
        assert found.card.last4 == "1234"
        assert found.authorization_code == "AUTH001"
        assert found.transaction_type == TransactionType.PURCHASE
        assert found.amount.amount == 150000
        assert found.amount.currency == Currency.CRC
        assert found.raw_data == {"original": "test", "nested": {"key": "value"}}
        assert found.created_at == datetime(2025, 3, 15, 14, 35, 0)

    def test_round_trip_with_different_currency_and_type(
        self, session: Session
    ) -> None:
        event = FinancialEvent(
            id=EventId(value="evt-usd"),
            message_id=MessageId(value="msg-xyz"),
            bank=Bank.BAC,
            event_type=NotificationType.TRANSACTION_NOTIFICATION,
            merchant="WALMART",
            transaction_date=datetime(2025, 6, 1, 10, 0, 0),
            card=CardInfo(brand="MASTERCARD", last4="5678"),
            authorization_code="AUTH999",
            transaction_type=TransactionType.REFUND,
            amount=Money(amount=2550, currency=Currency.USD),
            raw_data={},
            created_at=datetime(2025, 6, 1, 10, 5, 0),
        )
        repo = SqlAlchemyEventRepository(session)
        repo.save(event)
        session.flush()

        found = repo.find_by_id(event.id)
        assert found is not None
        assert found.amount.amount == 2550
        assert found.amount.currency == Currency.USD
        assert found.transaction_type == TransactionType.REFUND
        assert found.card.brand == "MASTERCARD"
        assert found.raw_data == {}


class TestUnitOfWork:
    def test_uow_commits_on_success(
        self, engine: Engine, sample_event: FinancialEvent
    ) -> None:
        with UnitOfWork(engine) as session:
            repo = SqlAlchemyEventRepository(session)
            repo.save(sample_event)

        # Verify persisted in a new session
        with UnitOfWork(engine) as session:
            repo = SqlAlchemyEventRepository(session)
            found = repo.find_by_id(sample_event.id)
            assert found is not None
            assert found.merchant == "AMAZON"

    def test_uow_rolls_back_on_exception(
        self, engine: Engine, sample_event: FinancialEvent
    ) -> None:
        with pytest.raises(RuntimeError, match="boom"), UnitOfWork(engine) as session:
            repo = SqlAlchemyEventRepository(session)
            repo.save(sample_event)
            raise RuntimeError("boom")

        # Verify nothing was persisted
        with UnitOfWork(engine) as session:
            repo = SqlAlchemyEventRepository(session)
            assert repo.exists(sample_event.id) is False
