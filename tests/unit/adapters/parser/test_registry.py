"""Unit tests for ParserRegistry."""

import pytest

from bank_ingest.adapters.outbound.parser.registry import (
    ParserRegistry,
    build_parser_registry,
)
from bank_ingest.domain.enums import Bank, NotificationType
from bank_ingest.domain.ports.parser import ParserPort


class FakeParser(ParserPort):
    """Minimal parser stub for registry tests."""

    def __init__(self, bank: Bank, notification_type: NotificationType) -> None:
        self._bank = bank
        self._notification_type = notification_type

    @property
    def bank(self) -> Bank:
        return self._bank

    @property
    def notification_type(self) -> NotificationType:
        return self._notification_type

    def parse(self, message: object) -> object:
        raise NotImplementedError


class TestRegisterParser:
    def test_register_and_resolve(self) -> None:
        registry = ParserRegistry()
        parser = FakeParser(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        registry.register_parser(parser)

        result = registry.resolve(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        assert result is parser

    def test_duplicate_registration_raises(self) -> None:
        registry = ParserRegistry()
        parser1 = FakeParser(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        parser2 = FakeParser(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        registry.register_parser(parser1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register_parser(parser2)


class TestResolve:
    def test_resolve_returns_none_for_unknown_key(self) -> None:
        registry = ParserRegistry()
        result = registry.resolve(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        assert result is None

    def test_resolve_correct_parser_among_multiple(self) -> None:
        registry = ParserRegistry()
        parser = FakeParser(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        registry.register_parser(parser)

        result = registry.resolve(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        assert result is parser


class TestParsersProperty:
    def test_parsers_returns_copy(self) -> None:
        registry = ParserRegistry()
        parser = FakeParser(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        registry.register_parser(parser)

        parsers = registry.parsers
        parsers.clear()

        assert (
            registry.resolve(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
            is parser
        )

    def test_parsers_contains_registered_entries(self) -> None:
        registry = ParserRegistry()
        parser = FakeParser(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        registry.register_parser(parser)

        assert len(registry.parsers) == 1
        key = (Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        assert registry.parsers[key] is parser


class TestBuildParserRegistry:
    def test_build_registers_bac_transaction_parser(self) -> None:
        registry = build_parser_registry()
        result = registry.resolve(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION)
        assert result is not None
        assert result.bank == Bank.BAC
        assert result.notification_type == NotificationType.TRANSACTION_NOTIFICATION

    def test_build_returns_parser_registry_instance(self) -> None:
        registry = build_parser_registry()
        assert isinstance(registry, ParserRegistry)
