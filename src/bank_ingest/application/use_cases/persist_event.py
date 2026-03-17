"""PersistEvent use case — saves a FinancialEvent to the repository."""

from bank_ingest.domain.entities import FinancialEvent
from bank_ingest.domain.ports.event_repository import EventRepositoryPort
from bank_ingest.domain.ports.logger import LoggerPort


class PersistEvent:
    """Saves a FinancialEvent to the repository, skipping duplicates.

    Checks for existence before saving to prevent duplicate entries.
    Logs a warning when a duplicate is detected and skips the save.
    """

    def __init__(self, repository: EventRepositoryPort, logger: LoggerPort) -> None:
        self._repository = repository
        self._logger = logger

    def execute(self, event: FinancialEvent) -> None:
        """Save the event if it does not already exist.

        Args:
            event: The FinancialEvent to persist.
        """
        if self._repository.exists(event.id):
            self._logger.warning(
                "Duplicate event detected — skipping save",
                event_id=event.id.value,
                message_id=event.message_id.value,
            )
            return

        self._repository.save(event)
        self._logger.debug(
            "Event persisted",
            event_id=event.id.value,
            message_id=event.message_id.value,
        )
