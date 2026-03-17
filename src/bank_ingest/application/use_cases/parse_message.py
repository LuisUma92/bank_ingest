"""ParseMessage use case — extracts a FinancialEvent from a classified message."""

from bank_ingest.domain.entities import (
    ClassificationResult,
    FinancialEvent,
    SourceMessage,
)
from bank_ingest.domain.enums import Bank, NotificationType
from bank_ingest.domain.exceptions import ParsingError
from bank_ingest.domain.ports.logger import LoggerPort
from bank_ingest.domain.ports.parser import ParserPort


class ParseMessage:
    """Looks up the appropriate parser and delegates extraction.

    Uses a (Bank, NotificationType) key to find the registered parser.
    Raises ParsingError when no parser is registered for the classification,
    or when the parser itself fails.
    """

    def __init__(
        self,
        parsers: dict[tuple[Bank, NotificationType], ParserPort],
        logger: LoggerPort,
    ) -> None:
        self._parsers = parsers
        self._logger = logger

    def execute(
        self,
        message: SourceMessage,
        classification: ClassificationResult,
    ) -> FinancialEvent:
        """Parse the message using the parser registered for its classification.

        Args:
            message: The raw source message.
            classification: The bank and notification type determined by
                ClassifyMessage.

        Returns:
            A structured FinancialEvent.

        Raises:
            ParsingError: If no parser is registered or the parser fails.
        """
        key = (classification.bank, classification.notification_type)
        parser = self._parsers.get(key)

        if parser is None:
            reason = (
                f"No parser registered for {classification.bank}/"
                f"{classification.notification_type}"
            )
            self._logger.debug(
                "No parser found",
                message_id=message.id.value,
                bank=classification.bank,
                notification_type=classification.notification_type,
            )
            raise ParsingError(message_id=message.id.value, reason=reason)

        event = parser.parse(message)

        self._logger.debug(
            "Message parsed successfully",
            message_id=message.id.value,
            event_id=event.id.value,
        )
        return event
