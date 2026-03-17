"""ParserPort — abstract interface for bank notification parsers."""

from abc import ABC, abstractmethod

from bank_ingest.domain.entities import FinancialEvent, SourceMessage
from bank_ingest.domain.enums import Bank, NotificationType


class ParserPort(ABC):
    """Parses a bank notification message into a structured FinancialEvent.

    Each concrete parser handles one (Bank, NotificationType) combination.
    Raises ParsingError when the message cannot be parsed.
    """

    @property
    @abstractmethod
    def bank(self) -> Bank:
        """The bank this parser handles."""

    @property
    @abstractmethod
    def notification_type(self) -> NotificationType:
        """The notification type this parser handles."""

    @abstractmethod
    def parse(self, message: SourceMessage) -> FinancialEvent:
        """Parse the message into a FinancialEvent.

        Args:
            message: The raw source message to parse.

        Returns:
            A fully populated FinancialEvent.

        Raises:
            ParsingError: If structured data cannot be extracted.
        """
