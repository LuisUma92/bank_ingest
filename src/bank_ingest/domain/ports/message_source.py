"""Port definition for the message source (inbound adapter interface)."""

from abc import ABC, abstractmethod

from bank_ingest.domain.entities import SourceMessage


class MessageSourcePort(ABC):
    """Abstract port for retrieving source messages from a mail provider.

    Implementations are responsible for authentication, network I/O, and
    converting provider-specific message formats into SourceMessage objects.
    """

    @abstractmethod
    def fetch_messages(self, label: str) -> list[SourceMessage]:
        """Fetch all unprocessed messages that carry the given label.

        Args:
            label: The mail label/folder to query (e.g. "Transacciones").

        Returns:
            A list of SourceMessage objects. Returns an empty list when no
            matching messages are found.
        """
