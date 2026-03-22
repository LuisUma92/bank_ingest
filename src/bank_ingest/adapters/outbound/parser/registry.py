"""Parser registry for resolving parsers by bank and notification type."""

from bank_ingest.adapters.parsers.bac.transaction_notification import (
    BACTransactionNotificationParser,
)
from bank_ingest.domain.enums import Bank, NotificationType
from bank_ingest.domain.ports.parser import ParserPort


class ParserRegistry:
    """Explicit registry mapping (Bank, NotificationType) to parser instances.

    Per ADR-0006: parsers are registered at bootstrap time, not auto-discovered.
    """

    def __init__(self) -> None:
        self._parsers: dict[tuple[Bank, NotificationType], ParserPort] = {}

    def register_parser(self, parser: ParserPort) -> None:
        """Register a parser for its (bank, notification_type) key.

        Raises ValueError if a parser is already registered for that key.
        """
        key = (parser.bank, parser.notification_type)
        if key in self._parsers:
            raise ValueError(f"Parser already registered for {key}")
        self._parsers[key] = parser

    def resolve(
        self, bank: Bank, notification_type: NotificationType
    ) -> ParserPort | None:
        """Look up the parser for a given bank and notification type."""
        return self._parsers.get((bank, notification_type))

    @property
    def parsers(self) -> dict[tuple[Bank, NotificationType], ParserPort]:
        """Return a defensive copy of the internal parser dict."""
        return dict(self._parsers)


def build_parser_registry() -> ParserRegistry:
    """Build the default parser registry with all known parsers."""
    registry = ParserRegistry()
    registry.register_parser(BACTransactionNotificationParser())
    return registry
