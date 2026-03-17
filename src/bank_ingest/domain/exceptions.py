"""Domain exceptions for bank_ingest.

All exceptions inherit from BankIngestError, which is the base for all
domain-level errors in this system.
"""


class BankIngestError(Exception):
    """Base exception for all bank_ingest domain errors."""


class ParsingError(BankIngestError):
    """Raised when a parser fails to extract structured data from a message.

    Args:
        message_id: The ID of the source message that could not be parsed.
        reason: A human-readable description of why parsing failed.
    """

    def __init__(self, message_id: str, reason: str) -> None:
        self.message_id = message_id
        self.reason = reason
        super().__init__(f"ParsingError [message_id={message_id}]: {reason}")


class ClassificationError(BankIngestError):
    """Raised when a message cannot be classified to a known bank/notification type.

    Args:
        message_id: The ID of the source message that could not be classified.
        reason: A human-readable description of why classification failed.
    """

    def __init__(self, message_id: str, reason: str) -> None:
        self.message_id = message_id
        self.reason = reason
        super().__init__(f"ClassificationError [message_id={message_id}]: {reason}")


class StorageError(BankIngestError):
    """Raised when a storage operation (filesystem or database) fails."""


class MessageSourceError(BankIngestError):
    """Raised when fetching messages from the mail source fails."""
