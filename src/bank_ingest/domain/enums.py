"""Domain enums for bank_ingest."""

from enum import StrEnum


class Bank(StrEnum):
    """Supported banks. Extensible to additional banks in future phases."""

    BAC = "BAC"


class NotificationType(StrEnum):
    """Types of bank notification emails. Extensible to additional types."""

    TRANSACTION_NOTIFICATION = "TRANSACTION_NOTIFICATION"


class TransactionType(StrEnum):
    """Financial transaction types extracted from bank notifications."""

    PURCHASE = "PURCHASE"
    WITHDRAWAL = "WITHDRAWAL"
    REFUND = "REFUND"
    PAYMENT = "PAYMENT"


class ProcessingResult(StrEnum):
    """Outcome of processing a single source message through the pipeline."""

    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class Currency(StrEnum):
    """Supported currencies for monetary amounts."""

    CRC = "CRC"
    USD = "USD"
