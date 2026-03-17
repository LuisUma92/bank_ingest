"""Domain value objects for bank_ingest.

All value objects are immutable (frozen pydantic models).
"""

import re
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from bank_ingest.domain.enums import Currency


class Money(BaseModel):
    """Monetary amount expressed in the smallest currency unit (cents).

    Examples:
        Money(amount=1050, currency=Currency.USD)  # $10.50
        Money(amount=250000, currency=Currency.CRC)  # ₡2500.00
    """

    model_config = ConfigDict(frozen=True)

    amount: int
    currency: Currency

    @field_validator("amount")
    @classmethod
    def amount_must_be_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("amount must be non-negative")
        return v


class CardInfo(BaseModel):
    """Payment card identification information."""

    model_config = ConfigDict(frozen=True)

    brand: str
    last4: str

    @field_validator("brand")
    @classmethod
    def brand_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("brand must not be empty")
        return v

    @field_validator("last4")
    @classmethod
    def last4_must_be_four_digits(cls, v: str) -> str:
        if not re.fullmatch(r"\d{4}", v):
            raise ValueError("last4 must be exactly 4 digits")
        return v


class MessageId(BaseModel):
    """Unique identifier for a source message (email).

    Wraps the external message ID from the mail provider.
    """

    model_config = ConfigDict(frozen=True)

    value: str

    @field_validator("value")
    @classmethod
    def value_must_be_safe_identifier(cls, v: str) -> str:
        """Validate MessageId is non-blank, bounded, and free of path separators."""
        if not v or not v.strip():
            raise ValueError("MessageId value must not be blank")
        if len(v) > 256:
            raise ValueError("MessageId value must not exceed 256 characters")
        if re.search(r"[/\\]", v):
            raise ValueError("MessageId value must not contain path separators")
        return v


def _new_uuid() -> str:
    """Generate a new UUID4 string for EventId default values."""
    return str(uuid4())


class EventId(BaseModel):
    """Unique identifier for a financial event.

    Defaults to a new UUID4 when not provided explicitly.

    Example:
        EventId()                    # auto-generated UUID4
        EventId(value="evt-abc123")  # explicit value
    """

    model_config = ConfigDict(frozen=True)

    value: str = Field(default_factory=_new_uuid)

    @field_validator("value")
    @classmethod
    def value_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("EventId value must not be empty or blank")
        return v
