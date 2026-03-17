"""Tests for domain entities."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from bank_ingest.domain.entities import (
    ClassificationResult,
    FinancialEvent,
    SourceMessage,
)
from bank_ingest.domain.enums import Bank, Currency, NotificationType, TransactionType
from bank_ingest.domain.value_objects import CardInfo, EventId, MessageId, Money


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def make_message_id(value: str = "msg-001") -> MessageId:
    return MessageId(value=value)


def make_money(amount: int = 5000, currency: Currency = Currency.USD) -> Money:
    return Money(amount=amount, currency=currency)


def make_card(brand: str = "VISA", last4: str = "1234") -> CardInfo:
    return CardInfo(brand=brand, last4=last4)


def make_now() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# SourceMessage
# ---------------------------------------------------------------------------


class TestSourceMessage:
    def _make(self, **overrides):
        defaults = dict(
            id=make_message_id(),
            sender="bank@bac.cr",
            subject="Transaction Alert",
            body_html="<p>Hello</p>",
            received_at=make_now(),
        )
        defaults.update(overrides)
        return SourceMessage(**defaults)

    def test_create_valid(self):
        msg = self._make()
        assert msg.sender == "bank@bac.cr"
        assert msg.subject == "Transaction Alert"
        assert msg.body_html == "<p>Hello</p>"

    def test_is_immutable(self):
        msg = self._make()
        with pytest.raises(ValidationError):
            msg.sender = "other@bac.cr"  # type: ignore[misc]

    def test_id_is_message_id(self):
        mid = make_message_id("my-id")
        msg = self._make(id=mid)
        assert msg.id == mid

    def test_received_at_is_datetime(self):
        msg = self._make()
        assert isinstance(msg.received_at, datetime)

    def test_empty_sender_raises(self):
        with pytest.raises(ValidationError):
            self._make(sender="")

    def test_empty_subject_raises(self):
        with pytest.raises(ValidationError):
            self._make(subject="")

    def test_empty_body_html_raises(self):
        with pytest.raises(ValidationError):
            self._make(body_html="")

    def test_none_received_at_raises(self):
        with pytest.raises(ValidationError):
            self._make(received_at=None)  # type: ignore[arg-type]

    def test_none_id_raises(self):
        with pytest.raises(ValidationError):
            self._make(id=None)  # type: ignore[arg-type]

    def test_equality_same_id(self):
        mid = make_message_id("same")
        msg1 = self._make(id=mid)
        msg2 = self._make(id=mid)
        assert msg1 == msg2


# ---------------------------------------------------------------------------
# ClassificationResult
# ---------------------------------------------------------------------------


class TestClassificationResult:
    def test_create_valid(self):
        result = ClassificationResult(
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        assert result.bank == Bank.BAC
        assert result.notification_type == NotificationType.TRANSACTION_NOTIFICATION

    def test_is_immutable(self):
        result = ClassificationResult(
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        with pytest.raises(ValidationError):
            result.bank = Bank.BAC  # type: ignore[misc]

    def test_none_bank_raises(self):
        with pytest.raises(ValidationError):
            ClassificationResult(
                bank=None, notification_type=NotificationType.TRANSACTION_NOTIFICATION
            )  # type: ignore[arg-type]

    def test_none_notification_type_raises(self):
        with pytest.raises(ValidationError):
            ClassificationResult(bank=Bank.BAC, notification_type=None)  # type: ignore[arg-type]

    def test_invalid_bank_raises(self):
        with pytest.raises(ValidationError):
            ClassificationResult(
                bank="NOT_A_BANK",
                notification_type=NotificationType.TRANSACTION_NOTIFICATION,
            )  # type: ignore[arg-type]

    def test_equality(self):
        r1 = ClassificationResult(
            bank=Bank.BAC, notification_type=NotificationType.TRANSACTION_NOTIFICATION
        )
        r2 = ClassificationResult(
            bank=Bank.BAC, notification_type=NotificationType.TRANSACTION_NOTIFICATION
        )
        assert r1 == r2


# ---------------------------------------------------------------------------
# FinancialEvent
# ---------------------------------------------------------------------------


class TestFinancialEvent:
    def _make(self, **overrides):
        defaults = dict(
            id=EventId(value="evt-001"),
            message_id=make_message_id(),
            bank=Bank.BAC,
            event_type=NotificationType.TRANSACTION_NOTIFICATION,
            merchant="Starbucks",
            transaction_date=make_now(),
            card=make_card(),
            authorization_code="AUTH123",
            transaction_type=TransactionType.PURCHASE,
            amount=make_money(),
            raw_data={"original": "data"},
            created_at=make_now(),
        )
        defaults.update(overrides)
        return FinancialEvent(**defaults)

    def test_create_valid(self):
        event = self._make()
        assert event.merchant == "Starbucks"
        assert event.authorization_code == "AUTH123"

    def test_is_immutable(self):
        event = self._make()
        with pytest.raises(ValidationError):
            event.merchant = "Other"  # type: ignore[misc]

    def test_id_is_event_id(self):
        eid = EventId(value="evt-999")
        event = self._make(id=eid)
        assert event.id == eid

    def test_message_id_is_message_id_type(self):
        mid = make_message_id("link-id")
        event = self._make(message_id=mid)
        assert event.message_id == mid

    def test_bank_must_be_bank_enum(self):
        with pytest.raises(ValidationError):
            self._make(bank="BAC")

    def test_event_type_must_be_notification_type_enum(self):
        with pytest.raises(ValidationError):
            self._make(event_type="TRANSACTION_NOTIFICATION")

    def test_transaction_type_must_be_enum(self):
        with pytest.raises(ValidationError):
            self._make(transaction_type="PURCHASE")

    def test_amount_must_be_money_type(self):
        with pytest.raises(ValidationError):
            self._make(amount=5000)

    def test_card_must_be_card_info_type(self):
        with pytest.raises(ValidationError):
            self._make(card={"brand": "VISA", "last4": "1234"})

    def test_raw_data_is_dict(self):
        event = self._make(raw_data={"key": "val", "nested": {"a": 1}})
        assert event.raw_data == {"key": "val", "nested": {"a": 1}}

    def test_empty_merchant_raises(self):
        with pytest.raises(ValidationError):
            self._make(merchant="")

    def test_empty_authorization_code_raises(self):
        with pytest.raises(ValidationError):
            self._make(authorization_code="")

    def test_none_transaction_date_raises(self):
        with pytest.raises(ValidationError):
            self._make(transaction_date=None)  # type: ignore[arg-type]

    def test_none_created_at_raises(self):
        with pytest.raises(ValidationError):
            self._make(created_at=None)  # type: ignore[arg-type]

    def test_equality_same_id(self):
        eid = EventId(value="evt-eq")
        e1 = self._make(id=eid)
        e2 = self._make(id=eid)
        assert e1 == e2

    def test_withdrawal_transaction_type(self):
        event = self._make(transaction_type=TransactionType.WITHDRAWAL)
        assert event.transaction_type == TransactionType.WITHDRAWAL

    def test_refund_transaction_type(self):
        event = self._make(transaction_type=TransactionType.REFUND)
        assert event.transaction_type == TransactionType.REFUND

    def test_payment_transaction_type(self):
        event = self._make(transaction_type=TransactionType.PAYMENT)
        assert event.transaction_type == TransactionType.PAYMENT

    def test_crc_currency(self):
        money = Money(amount=250000, currency=Currency.CRC)
        event = self._make(amount=money)
        assert event.amount.currency == Currency.CRC
