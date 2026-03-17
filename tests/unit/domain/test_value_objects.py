"""Tests for domain value objects."""

import re

import pytest
from pydantic import ValidationError

from bank_ingest.domain.enums import Currency
from bank_ingest.domain.value_objects import CardInfo, EventId, MessageId, Money


class TestMoney:
    def test_create_valid_money(self):
        m = Money(amount=1000, currency=Currency.USD)
        assert m.amount == 1000
        assert m.currency == Currency.USD

    def test_amount_zero_is_valid(self):
        m = Money(amount=0, currency=Currency.CRC)
        assert m.amount == 0

    def test_amount_in_cents(self):
        m = Money(amount=9999, currency=Currency.USD)
        assert m.amount == 9999

    def test_money_is_immutable(self):
        m = Money(amount=500, currency=Currency.USD)
        with pytest.raises(ValidationError):
            m.amount = 999  # type: ignore[misc]

    def test_negative_amount_raises(self):
        with pytest.raises(ValidationError):
            Money(amount=-1, currency=Currency.USD)

    def test_none_currency_raises(self):
        with pytest.raises(ValidationError):
            Money(amount=100, currency=None)  # type: ignore[arg-type]

    def test_invalid_currency_string_raises(self):
        with pytest.raises(ValidationError):
            Money(amount=100, currency="EUR")  # type: ignore[arg-type]

    def test_non_integer_amount_raises(self):
        with pytest.raises(ValidationError):
            Money(amount=10.5, currency=Currency.USD)  # type: ignore[arg-type]

    def test_equality_same_values(self):
        m1 = Money(amount=100, currency=Currency.USD)
        m2 = Money(amount=100, currency=Currency.USD)
        assert m1 == m2

    def test_equality_different_amount(self):
        m1 = Money(amount=100, currency=Currency.USD)
        m2 = Money(amount=200, currency=Currency.USD)
        assert m1 != m2

    def test_equality_different_currency(self):
        m1 = Money(amount=100, currency=Currency.USD)
        m2 = Money(amount=100, currency=Currency.CRC)
        assert m1 != m2

    def test_large_amount(self):
        m = Money(amount=9_999_999_999, currency=Currency.CRC)
        assert m.amount == 9_999_999_999


class TestCardInfo:
    def test_create_valid_card_info(self):
        c = CardInfo(brand="VISA", last4="1234")
        assert c.brand == "VISA"
        assert c.last4 == "1234"

    def test_card_info_is_immutable(self):
        c = CardInfo(brand="VISA", last4="1234")
        with pytest.raises(ValidationError):
            c.brand = "AMEX"  # type: ignore[misc]

    def test_last4_must_be_four_digits(self):
        with pytest.raises(ValidationError):
            CardInfo(brand="VISA", last4="123")

    def test_last4_five_digits_raises(self):
        with pytest.raises(ValidationError):
            CardInfo(brand="VISA", last4="12345")

    def test_last4_non_digits_raises(self):
        with pytest.raises(ValidationError):
            CardInfo(brand="VISA", last4="12ab")

    def test_last4_empty_raises(self):
        with pytest.raises(ValidationError):
            CardInfo(brand="VISA", last4="")

    def test_empty_brand_raises(self):
        with pytest.raises(ValidationError):
            CardInfo(brand="", last4="1234")

    def test_none_brand_raises(self):
        with pytest.raises(ValidationError):
            CardInfo(brand=None, last4="1234")  # type: ignore[arg-type]

    def test_none_last4_raises(self):
        with pytest.raises(ValidationError):
            CardInfo(brand="VISA", last4=None)  # type: ignore[arg-type]

    def test_equality_same_values(self):
        c1 = CardInfo(brand="AMEX", last4="9999")
        c2 = CardInfo(brand="AMEX", last4="9999")
        assert c1 == c2

    def test_equality_different_brand(self):
        c1 = CardInfo(brand="VISA", last4="1234")
        c2 = CardInfo(brand="AMEX", last4="1234")
        assert c1 != c2

    def test_all_zeros_last4_is_valid(self):
        c = CardInfo(brand="VISA", last4="0000")
        assert c.last4 == "0000"


class TestMessageId:
    def test_create_valid_message_id(self):
        mid = MessageId(value="msg-abc-123")
        assert mid.value == "msg-abc-123"

    def test_message_id_is_immutable(self):
        mid = MessageId(value="msg-abc-123")
        with pytest.raises(ValidationError):
            mid.value = "other"  # type: ignore[misc]

    def test_empty_value_raises(self):
        with pytest.raises(ValidationError):
            MessageId(value="")

    def test_none_value_raises(self):
        with pytest.raises(ValidationError):
            MessageId(value=None)  # type: ignore[arg-type]

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            MessageId(value="   ")

    def test_equality_same_value(self):
        m1 = MessageId(value="abc")
        m2 = MessageId(value="abc")
        assert m1 == m2

    def test_equality_different_value(self):
        m1 = MessageId(value="abc")
        m2 = MessageId(value="xyz")
        assert m1 != m2

    def test_safe_special_characters_allowed(self):
        mid = MessageId(value="msg-abc+xyz=")
        assert mid.value == "msg-abc+xyz="

    def test_path_separator_rejected(self):
        with pytest.raises(ValidationError):
            MessageId(value="msg/abc")

    def test_backslash_rejected(self):
        with pytest.raises(ValidationError):
            MessageId(value="msg\\abc")

    def test_exceeds_max_length_rejected(self):
        with pytest.raises(ValidationError):
            MessageId(value="a" * 257)


class TestEventId:
    def test_create_with_explicit_value(self):
        eid = EventId(value="evt-123")
        assert eid.value == "evt-123"

    def test_default_value_is_generated(self):
        eid = EventId()
        assert eid.value is not None
        assert len(eid.value) > 0

    def test_default_value_looks_like_uuid(self):
        eid = EventId()
        uuid_pattern = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )
        assert re.match(uuid_pattern, eid.value)

    def test_two_defaults_are_unique(self):
        eid1 = EventId()
        eid2 = EventId()
        assert eid1.value != eid2.value

    def test_event_id_is_immutable(self):
        eid = EventId(value="evt-123")
        with pytest.raises(ValidationError):
            eid.value = "other"  # type: ignore[misc]

    def test_empty_value_raises(self):
        with pytest.raises(ValidationError):
            EventId(value="")

    def test_none_value_raises(self):
        with pytest.raises(ValidationError):
            EventId(value=None)  # type: ignore[arg-type]

    def test_equality_same_value(self):
        e1 = EventId(value="same")
        e2 = EventId(value="same")
        assert e1 == e2

    def test_equality_different_value(self):
        e1 = EventId(value="a")
        e2 = EventId(value="b")
        assert e1 != e2
