"""Domain entities for bank_ingest.

All entities are immutable (frozen pydantic models).
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from bank_ingest.domain.enums import Bank, NotificationType, TransactionType
from bank_ingest.domain.value_objects import CardInfo, EventId, MessageId, Money


class SourceMessage(BaseModel):
    """A raw email message retrieved from the mail source.

    Represents an unprocessed notification from a bank. The body_html field
    contains the original HTML content that parsers will later extract data from.
    """

    model_config = ConfigDict(frozen=True)

    id: MessageId
    sender: str
    subject: str
    body_html: str
    received_at: datetime

    @field_validator("sender")
    @classmethod
    def sender_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("sender must not be empty")
        return v

    @field_validator("subject")
    @classmethod
    def subject_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("subject must not be empty")
        return v

    @field_validator("body_html")
    @classmethod
    def body_html_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("body_html must not be empty")
        return v


class ClassificationResult(BaseModel):
    """The result of classifying a source message by bank and notification type."""

    model_config = ConfigDict(frozen=True)

    bank: Annotated[Bank, Field(strict=True)]
    notification_type: Annotated[NotificationType, Field(strict=True)]


class FinancialEvent(BaseModel):
    """A structured financial event extracted from a bank notification email.

    Maintains a reference to the originating source message for traceability.
    """

    model_config = ConfigDict(frozen=True)

    id: EventId
    message_id: MessageId
    bank: Annotated[Bank, Field(strict=True)]
    event_type: Annotated[NotificationType, Field(strict=True)]
    merchant: str
    transaction_date: datetime
    card: CardInfo
    authorization_code: str
    transaction_type: Annotated[TransactionType, Field(strict=True)]
    amount: Money
    raw_data: dict[str, object]
    created_at: datetime

    @field_validator("card", mode="before")
    @classmethod
    def card_must_be_card_info_instance(cls, v: object) -> object:
        """Reject dict coercion — require an actual CardInfo instance."""
        if not isinstance(v, CardInfo):
            raise ValueError(
                "card must be a CardInfo instance, not a plain dict or other type"
            )
        return v

    @field_validator("merchant")
    @classmethod
    def merchant_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("merchant must not be empty")
        return v

    @field_validator("authorization_code")
    @classmethod
    def authorization_code_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("authorization_code must not be empty")
        return v
