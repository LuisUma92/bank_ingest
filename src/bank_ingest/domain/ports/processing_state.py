"""Port definition for updating the processing state of source messages."""

from abc import ABC, abstractmethod

from bank_ingest.domain.value_objects import MessageId


class ProcessingStatePort(ABC):
    """Abstract port for marking the processing outcome of a source message.

    Implementations apply state changes to the mail provider (e.g. Gmail labels)
    or any other external system that tracks processing status.
    """

    @abstractmethod
    def mark_processed(self, message_id: MessageId) -> None:
        """Mark a message as successfully processed.

        Args:
            message_id: The identifier of the message to mark.
        """

    @abstractmethod
    def mark_failed(self, message_id: MessageId, reason: str) -> None:
        """Mark a message as failed during processing.

        Args:
            message_id: The identifier of the message to mark.
            reason: A human-readable description of the failure.
        """

    @abstractmethod
    def mark_skipped(self, message_id: MessageId, reason: str | None = None) -> None:
        """Mark a message as skipped (not applicable for processing).

        Args:
            message_id: The identifier of the message to mark.
            reason: An optional human-readable description of why it was skipped.
        """
