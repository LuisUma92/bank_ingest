"""Tests for domain ports (ABCs).

Verifies:
- Ports cannot be instantiated directly.
- Concrete subclasses must implement all abstract methods.
- Correctly implemented subclasses can be instantiated.
"""

from datetime import UTC, datetime

import pytest

from bank_ingest.domain.entities import FinancialEvent, SourceMessage
from bank_ingest.domain.enums import Bank, Currency, NotificationType, TransactionType
from bank_ingest.domain.ports.event_repository import EventRepositoryPort
from bank_ingest.domain.ports.logger import LoggerPort
from bank_ingest.domain.ports.message_source import MessageSourcePort
from bank_ingest.domain.ports.message_store import MessageStorePort
from bank_ingest.domain.ports.processing_state import ProcessingStatePort
from bank_ingest.domain.value_objects import CardInfo, EventId, MessageId, Money

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_source_message() -> SourceMessage:
    return SourceMessage(
        id=MessageId(value="msg-test"),
        sender="bank@bac.cr",
        subject="Alert",
        body_html="<p>body</p>",
        received_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


def _make_financial_event() -> FinancialEvent:
    return FinancialEvent(
        id=EventId(value="evt-test"),
        message_id=MessageId(value="msg-test"),
        bank=Bank.BAC,
        event_type=NotificationType.TRANSACTION_NOTIFICATION,
        merchant="Shop",
        transaction_date=datetime(2024, 1, 1, tzinfo=UTC),
        card=CardInfo(brand="VISA", last4="0001"),
        authorization_code="CODE01",
        transaction_type=TransactionType.PURCHASE,
        amount=Money(amount=1000, currency=Currency.USD),
        raw_data={},
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


# ---------------------------------------------------------------------------
# MessageSourcePort
# ---------------------------------------------------------------------------


class TestMessageSourcePort:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            MessageSourcePort()  # type: ignore[abstract]

    def test_incomplete_subclass_cannot_instantiate(self):
        class Incomplete(MessageSourcePort):
            pass

        with pytest.raises(TypeError):
            Incomplete()

    def test_complete_subclass_can_instantiate(self):
        class ConcreteSource(MessageSourcePort):
            def fetch_messages(self, label: str) -> list[SourceMessage]:
                return []

        source = ConcreteSource()
        assert source.fetch_messages("Transacciones") == []

    def test_fetch_messages_returns_list(self):
        msg = _make_source_message()

        class OneMessageSource(MessageSourcePort):
            def fetch_messages(self, label: str) -> list[SourceMessage]:
                return [msg]

        source = OneMessageSource()
        result = source.fetch_messages("Transacciones")
        assert len(result) == 1
        assert result[0] == msg


# ---------------------------------------------------------------------------
# MessageStorePort
# ---------------------------------------------------------------------------


class TestMessageStorePort:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            MessageStorePort()  # type: ignore[abstract]

    def test_incomplete_subclass_missing_store_raw(self):
        class Incomplete(MessageStorePort):
            def store_rendered(self, message_id: MessageId, content: str) -> None:
                pass

            def store_parsed(self, message_id: MessageId, data: dict) -> None:
                pass

            def store_error(self, message_id: MessageId, error: str) -> None:
                pass

        with pytest.raises(TypeError):
            Incomplete()

    def test_complete_subclass_can_instantiate(self):
        class ConcreteStore(MessageStorePort):
            def store_raw(self, message: SourceMessage) -> None:
                pass

            def store_rendered(self, message_id: MessageId, content: str) -> None:
                pass

            def store_parsed(self, message_id: MessageId, data: dict) -> None:
                pass

            def store_error(self, message_id: MessageId, error: str) -> None:
                pass

        store = ConcreteStore()
        # All methods callable without error
        mid = MessageId(value="m")
        store.store_raw(_make_source_message())
        store.store_rendered(mid, "html")
        store.store_parsed(mid, {"k": "v"})
        store.store_error(mid, "some error")


# ---------------------------------------------------------------------------
# EventRepositoryPort
# ---------------------------------------------------------------------------


class TestEventRepositoryPort:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            EventRepositoryPort()  # type: ignore[abstract]

    def test_incomplete_subclass_cannot_instantiate(self):
        class Incomplete(EventRepositoryPort):
            def save(self, event: FinancialEvent) -> None:
                pass

        with pytest.raises(TypeError):
            Incomplete()

    def test_complete_subclass_can_instantiate(self):
        event = _make_financial_event()

        class ConcreteRepo(EventRepositoryPort):
            def __init__(self):
                self._store: dict = {}

            def save(self, ev: FinancialEvent) -> None:
                self._store[ev.id.value] = ev

            def find_by_id(self, event_id: EventId) -> FinancialEvent | None:
                return self._store.get(event_id.value)

            def find_by_message_id(self, message_id: MessageId) -> list[FinancialEvent]:
                return [e for e in self._store.values() if e.message_id == message_id]

            def exists(self, event_id: EventId) -> bool:
                return event_id.value in self._store

        repo = ConcreteRepo()
        repo.save(event)

        found = repo.find_by_id(EventId(value="evt-test"))
        assert found == event

        assert repo.exists(EventId(value="evt-test")) is True
        assert repo.exists(EventId(value="missing")) is False

        by_msg = repo.find_by_message_id(MessageId(value="msg-test"))
        assert len(by_msg) == 1

    def test_find_by_id_returns_none_when_missing(self):
        class ConcreteRepo(EventRepositoryPort):
            def save(self, ev: FinancialEvent) -> None:
                pass

            def find_by_id(self, event_id: EventId) -> FinancialEvent | None:
                return None

            def find_by_message_id(self, message_id: MessageId) -> list[FinancialEvent]:
                return []

            def exists(self, event_id: EventId) -> bool:
                return False

        repo = ConcreteRepo()
        assert repo.find_by_id(EventId(value="x")) is None


# ---------------------------------------------------------------------------
# ProcessingStatePort
# ---------------------------------------------------------------------------


class TestProcessingStatePort:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            ProcessingStatePort()  # type: ignore[abstract]

    def test_incomplete_subclass_cannot_instantiate(self):
        class Incomplete(ProcessingStatePort):
            def mark_processed(self, message_id: MessageId) -> None:
                pass

        with pytest.raises(TypeError):
            Incomplete()

    def test_complete_subclass_can_instantiate(self):
        class ConcreteState(ProcessingStatePort):
            def mark_processed(self, message_id: MessageId) -> None:
                pass

            def mark_failed(self, message_id: MessageId, reason: str) -> None:
                pass

            def mark_skipped(
                self, message_id: MessageId, reason: str | None = None
            ) -> None:
                pass

        state = ConcreteState()
        mid = MessageId(value="m")
        state.mark_processed(mid)
        state.mark_failed(mid, "something broke")
        state.mark_skipped(mid)
        state.mark_skipped(mid, reason="duplicate")

    def test_mark_skipped_default_reason_is_none(self):
        calls = []

        class ConcreteState(ProcessingStatePort):
            def mark_processed(self, message_id: MessageId) -> None:
                pass

            def mark_failed(self, message_id: MessageId, reason: str) -> None:
                pass

            def mark_skipped(
                self, message_id: MessageId, reason: str | None = None
            ) -> None:
                calls.append(reason)

        state = ConcreteState()
        state.mark_skipped(MessageId(value="m"))
        assert calls == [None]


# ---------------------------------------------------------------------------
# LoggerPort
# ---------------------------------------------------------------------------


class TestLoggerPort:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            LoggerPort()  # type: ignore[abstract]

    def test_incomplete_subclass_cannot_instantiate(self):
        class Incomplete(LoggerPort):
            def info(self, message: str, **kwargs) -> None:
                pass

        with pytest.raises(TypeError):
            Incomplete()

    def test_complete_subclass_can_instantiate(self):
        class ConcreteLogger(LoggerPort):
            def __init__(self):
                self.log: list = []

            def info(self, message: str, **kwargs) -> None:
                self.log.append(("INFO", message, kwargs))

            def warning(self, message: str, **kwargs) -> None:
                self.log.append(("WARNING", message, kwargs))

            def error(self, message: str, **kwargs) -> None:
                self.log.append(("ERROR", message, kwargs))

            def debug(self, message: str, **kwargs) -> None:
                self.log.append(("DEBUG", message, kwargs))

        logger = ConcreteLogger()
        logger.info("started")
        logger.warning("watch out", detail="x")
        logger.error("crash")
        logger.debug("trace", step=1)

        assert logger.log[0] == ("INFO", "started", {})
        assert logger.log[1] == ("WARNING", "watch out", {"detail": "x"})
        assert logger.log[2] == ("ERROR", "crash", {})
        assert logger.log[3] == ("DEBUG", "trace", {"step": 1})

    def test_kwargs_passed_through(self):
        received_kwargs = {}

        class ConcreteLogger(LoggerPort):
            def info(self, message: str, **kwargs) -> None:
                received_kwargs.update(kwargs)

            def warning(self, message: str, **kwargs) -> None:
                pass

            def error(self, message: str, **kwargs) -> None:
                pass

            def debug(self, message: str, **kwargs) -> None:
                pass

        logger = ConcreteLogger()
        logger.info("msg", user="alice", action="login")
        assert received_kwargs == {"user": "alice", "action": "login"}
