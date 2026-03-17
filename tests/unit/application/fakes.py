"""Concrete test doubles (fakes/stubs) implementing domain ports.

These replace unittest.mock to catch interface mismatches and keep tests readable.
"""

from bank_ingest.domain.entities import (
    ClassificationResult,
    FinancialEvent,
    SourceMessage,
)
from bank_ingest.domain.enums import Bank, NotificationType
from bank_ingest.domain.exceptions import MessageSourceError
from bank_ingest.domain.ports.classifier import ClassifierPort
from bank_ingest.domain.ports.event_repository import EventRepositoryPort
from bank_ingest.domain.ports.logger import LoggerPort
from bank_ingest.domain.ports.message_source import MessageSourcePort
from bank_ingest.domain.ports.message_store import MessageStorePort
from bank_ingest.domain.ports.parser import ParserPort
from bank_ingest.domain.ports.processing_state import ProcessingStatePort
from bank_ingest.domain.value_objects import EventId, MessageId


class FakeMessageSource(MessageSourcePort):
    """Returns a fixed list of messages, or raises MessageSourceError."""

    def __init__(
        self,
        messages: list[SourceMessage] | None = None,
        raise_error: bool = False,
    ) -> None:
        self._messages = messages or []
        self._raise_error = raise_error

    def fetch_messages(self, label: str) -> list[SourceMessage]:
        if self._raise_error:
            raise MessageSourceError("Simulated source failure")
        return list(self._messages)


class FakeMessageStore(MessageStorePort):
    """Records calls to each store method for assertion."""

    def __init__(self) -> None:
        self.raw_stored: list[SourceMessage] = []
        self.rendered_stored: list[tuple[MessageId, str]] = []
        self.parsed_stored: list[tuple[MessageId, dict[str, object]]] = []
        self.errors_stored: list[tuple[MessageId, str]] = []

    def store_raw(self, message: SourceMessage) -> None:
        self.raw_stored.append(message)

    def store_rendered(self, message_id: MessageId, content: str) -> None:
        self.rendered_stored.append((message_id, content))

    def store_parsed(self, message_id: MessageId, data: dict[str, object]) -> None:
        self.parsed_stored.append((message_id, data))

    def store_error(self, message_id: MessageId, error: str) -> None:
        self.errors_stored.append((message_id, error))


class FakeEventRepository(EventRepositoryPort):
    """In-memory event store."""

    def __init__(self, existing_ids: set[str] | None = None) -> None:
        self._events: dict[str, FinancialEvent] = {}
        self._existing_ids: set[str] = set(existing_ids or set())

    def save(self, event: FinancialEvent) -> None:
        self._events[event.id.value] = event

    def find_by_id(self, event_id: EventId) -> FinancialEvent | None:
        return self._events.get(event_id.value)

    def find_by_message_id(self, message_id: MessageId) -> list[FinancialEvent]:
        return [
            e for e in self._events.values() if e.message_id.value == message_id.value
        ]

    def exists(self, event_id: EventId) -> bool:
        return event_id.value in self._existing_ids or event_id.value in self._events


class FakeProcessingState(ProcessingStatePort):
    """Records semantic state transitions."""

    def __init__(self) -> None:
        self.processed: list[MessageId] = []
        self.failed: list[tuple[MessageId, str]] = []
        self.skipped: list[tuple[MessageId, str | None]] = []

    def mark_processed(self, message_id: MessageId) -> None:
        self.processed.append(message_id)

    def mark_failed(self, message_id: MessageId, reason: str) -> None:
        self.failed.append((message_id, reason))

    def mark_skipped(self, message_id: MessageId, reason: str | None = None) -> None:
        self.skipped.append((message_id, reason))


class FakeLogger(LoggerPort):
    """Captures log calls by level."""

    def __init__(self) -> None:
        self.infos: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.debugs: list[str] = []

    def info(self, message: str, **kwargs: object) -> None:
        self.infos.append(message)

    def warning(self, message: str, **kwargs: object) -> None:
        self.warnings.append(message)

    def error(self, message: str, **kwargs: object) -> None:
        self.errors.append(message)

    def debug(self, message: str, **kwargs: object) -> None:
        self.debugs.append(message)


class MatchingClassifier(ClassifierPort):
    """Always returns the given ClassificationResult."""

    def __init__(self, result: ClassificationResult) -> None:
        self._result = result

    def classify(self, message: SourceMessage) -> ClassificationResult | None:
        return self._result


class NonMatchingClassifier(ClassifierPort):
    """Always returns None (no match)."""

    def classify(self, message: SourceMessage) -> ClassificationResult | None:
        return None


class FakeParser(ParserPort):
    """Returns a fixed FinancialEvent or raises ParsingError."""

    def __init__(
        self,
        event: FinancialEvent,
        bank: Bank,
        notification_type: NotificationType,
    ) -> None:
        self._event = event
        self._bank = bank
        self._notification_type = notification_type

    @property
    def bank(self) -> Bank:
        return self._bank

    @property
    def notification_type(self) -> NotificationType:
        return self._notification_type

    def parse(self, message: SourceMessage) -> FinancialEvent:
        return self._event
