"""Domain layer for bank_ingest — the innermost layer with no external dependencies."""

from bank_ingest.domain.entities import (
    ClassificationResult,
    FinancialEvent,
    SourceMessage,
)
from bank_ingest.domain.enums import (
    Bank,
    Currency,
    NotificationType,
    ProcessingResult,
    TransactionType,
)
from bank_ingest.domain.exceptions import (
    BankIngestError,
    ClassificationError,
    MessageSourceError,
    ParsingError,
    StorageError,
)
from bank_ingest.domain.value_objects import CardInfo, EventId, MessageId, Money

__all__ = [  # noqa: RUF022
    # Entities
    "ClassificationResult",
    "FinancialEvent",
    "SourceMessage",
    # Enums
    "Bank",
    "Currency",
    "NotificationType",
    "ProcessingResult",
    "TransactionType",
    # Exceptions
    "BankIngestError",
    "ClassificationError",
    "MessageSourceError",
    "ParsingError",
    "StorageError",
    # Value objects
    "CardInfo",
    "EventId",
    "MessageId",
    "Money",
]
