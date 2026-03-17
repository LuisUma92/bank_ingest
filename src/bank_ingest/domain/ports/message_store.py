"""Port definition for the message artifact store (outbound adapter interface)."""

from abc import ABC, abstractmethod

from bank_ingest.domain.entities import SourceMessage
from bank_ingest.domain.value_objects import MessageId


class MessageStorePort(ABC):
    """Abstract port for persisting message artifacts at each pipeline stage.

    Implementations write artifacts to a durable storage backend (e.g.
    filesystem, object storage). The store is append-only and supports
    auditing and debugging.
    """

    @abstractmethod
    def store_raw(self, message: SourceMessage) -> None:
        """Persist the raw source message as received from the mail provider.

        Args:
            message: The SourceMessage retrieved from the mail source.
        """

    @abstractmethod
    def store_rendered(self, message_id: MessageId, content: str) -> None:
        """Persist a rendered (text/plain) representation of a message body.

        Args:
            message_id: The identifier of the originating source message.
            content: The rendered content string (e.g. stripped HTML).
        """

    @abstractmethod
    def store_parsed(self, message_id: MessageId, data: dict) -> None:
        """Persist the structured data extracted from a message.

        Args:
            message_id: The identifier of the originating source message.
            data: The structured extraction result as a plain dictionary.
        """

    @abstractmethod
    def store_error(self, message_id: MessageId, error: str) -> None:
        """Persist an error description for a message that failed processing.

        Args:
            message_id: The identifier of the originating source message.
            error: A human-readable error description.
        """
