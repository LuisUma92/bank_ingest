"""FetchLabeledMessages use case — retrieves labeled messages from the mail source."""

from bank_ingest.domain.entities import SourceMessage
from bank_ingest.domain.exceptions import MessageSourceError
from bank_ingest.domain.ports.logger import LoggerPort
from bank_ingest.domain.ports.message_source import MessageSourcePort


class FetchLabeledMessages:
    """Fetches messages with a given label from the mail source.

    Wraps the MessageSourcePort, logs the count of retrieved messages,
    and re-raises MessageSourceError after logging.
    """

    def __init__(self, source: MessageSourcePort, logger: LoggerPort) -> None:
        self._source = source
        self._logger = logger

    def execute(self, label: str) -> list[SourceMessage]:
        """Fetch all messages tagged with the given label.

        Args:
            label: The mail label to filter by (e.g. "Transacciones").

        Returns:
            List of SourceMessage instances.

        Raises:
            MessageSourceError: If the mail source cannot be reached.
        """
        try:
            messages = self._source.fetch_messages(label)
        except MessageSourceError as exc:
            self._logger.error(
                "Failed to fetch messages from source",
                label=label,
                error=str(exc),
            )
            raise

        count = len(messages)
        self._logger.info(
            "Fetched messages from source",
            label=label,
            count=count,
        )
        return messages
