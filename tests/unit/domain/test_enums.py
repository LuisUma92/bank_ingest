"""Tests for domain enums."""

import pytest

from bank_ingest.domain.enums import (
    Bank,
    Currency,
    NotificationType,
    ProcessingResult,
    TransactionType,
)


class TestBank:
    def test_bac_member_exists(self):
        assert Bank.BAC is not None

    def test_bac_value_is_string(self):
        assert isinstance(Bank.BAC.value, str)

    def test_bank_has_exactly_one_member(self):
        assert len(Bank) == 1

    def test_bank_from_value(self):
        assert Bank("BAC") == Bank.BAC

    def test_invalid_bank_raises(self):
        with pytest.raises(ValueError):
            Bank("UNKNOWN_BANK")


class TestNotificationType:
    def test_transaction_notification_exists(self):
        assert NotificationType.TRANSACTION_NOTIFICATION is not None

    def test_value_is_string(self):
        assert isinstance(NotificationType.TRANSACTION_NOTIFICATION.value, str)

    def test_from_value(self):
        assert NotificationType("TRANSACTION_NOTIFICATION") == NotificationType.TRANSACTION_NOTIFICATION

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            NotificationType("NO_SUCH_TYPE")


class TestTransactionType:
    def test_all_members_exist(self):
        assert TransactionType.PURCHASE is not None
        assert TransactionType.WITHDRAWAL is not None
        assert TransactionType.REFUND is not None
        assert TransactionType.PAYMENT is not None

    def test_has_exactly_four_members(self):
        assert len(TransactionType) == 4

    def test_values_are_strings(self):
        for member in TransactionType:
            assert isinstance(member.value, str)

    def test_from_value_purchase(self):
        assert TransactionType("PURCHASE") == TransactionType.PURCHASE

    def test_from_value_withdrawal(self):
        assert TransactionType("WITHDRAWAL") == TransactionType.WITHDRAWAL

    def test_from_value_refund(self):
        assert TransactionType("REFUND") == TransactionType.REFUND

    def test_from_value_payment(self):
        assert TransactionType("PAYMENT") == TransactionType.PAYMENT

    def test_invalid_transaction_type_raises(self):
        with pytest.raises(ValueError):
            TransactionType("INVALID")


class TestProcessingResult:
    def test_all_members_exist(self):
        assert ProcessingResult.PROCESSED is not None
        assert ProcessingResult.FAILED is not None
        assert ProcessingResult.SKIPPED is not None

    def test_has_exactly_three_members(self):
        assert len(ProcessingResult) == 3

    def test_values_are_strings(self):
        for member in ProcessingResult:
            assert isinstance(member.value, str)

    def test_from_value_processed(self):
        assert ProcessingResult("PROCESSED") == ProcessingResult.PROCESSED

    def test_from_value_failed(self):
        assert ProcessingResult("FAILED") == ProcessingResult.FAILED

    def test_from_value_skipped(self):
        assert ProcessingResult("SKIPPED") == ProcessingResult.SKIPPED


class TestCurrency:
    def test_crc_exists(self):
        assert Currency.CRC is not None

    def test_usd_exists(self):
        assert Currency.USD is not None

    def test_has_exactly_two_members(self):
        assert len(Currency) == 2

    def test_values_are_strings(self):
        for member in Currency:
            assert isinstance(member.value, str)

    def test_from_value_crc(self):
        assert Currency("CRC") == Currency.CRC

    def test_from_value_usd(self):
        assert Currency("USD") == Currency.USD

    def test_invalid_currency_raises(self):
        with pytest.raises(ValueError):
            Currency("EUR")
