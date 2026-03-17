"""Port definition for the financial event repository (outbound adapter interface)."""

from abc import ABC, abstractmethod

from bank_ingest.domain.entities import FinancialEvent
from bank_ingest.domain.value_objects import EventId, MessageId


class EventRepositoryPort(ABC):
    """Abstract port for persisting and querying financial events.

    Implementations handle the actual storage mechanism (e.g. SQLite via
    SQLAlchemy). The domain depends only on this interface.
    """

    @abstractmethod
    def save(self, event: FinancialEvent) -> None:
        """Persist a financial event.

        Args:
            event: The FinancialEvent to store.
        """

    @abstractmethod
    def find_by_id(self, event_id: EventId) -> FinancialEvent | None:
        """Retrieve a financial event by its unique identifier.

        Args:
            event_id: The EventId to look up.

        Returns:
            The matching FinancialEvent, or None if not found.
        """

    @abstractmethod
    def find_by_message_id(self, message_id: MessageId) -> list[FinancialEvent]:
        """Retrieve all financial events derived from a specific source message.

        Args:
            message_id: The originating MessageId.

        Returns:
            A list of matching FinancialEvent objects. Empty list if none found.
        """

    @abstractmethod
    def exists(self, event_id: EventId) -> bool:
        """Check whether a financial event with the given ID exists.

        Args:
            event_id: The EventId to check.

        Returns:
            True if an event with that ID exists, False otherwise.
        """
