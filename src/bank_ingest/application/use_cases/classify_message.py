"""ClassifyMessage use case — determines bank and notification type for a message."""

from bank_ingest.domain.entities import ClassificationResult, SourceMessage
from bank_ingest.domain.exceptions import ClassificationError
from bank_ingest.domain.ports.classifier import ClassifierPort
from bank_ingest.domain.ports.logger import LoggerPort


class ClassifyMessage:
    """Classifies a source message by iterating registered classifiers.

    The first classifier that returns a non-None result wins.
    Raises ClassificationError if no classifier matches.
    """

    def __init__(
        self,
        classifiers: list[ClassifierPort],
        logger: LoggerPort,
    ) -> None:
        self._classifiers = classifiers
        self._logger = logger

    def execute(self, message: SourceMessage) -> ClassificationResult:
        """Classify the message against all registered classifiers.

        Args:
            message: The source message to classify.

        Returns:
            The first matching ClassificationResult.

        Raises:
            ClassificationError: If no classifier matches the message.
        """
        for classifier in self._classifiers:
            result = classifier.classify(message)
            if result is not None:
                self._logger.debug(
                    "Message classified",
                    message_id=message.id.value,
                    bank=result.bank,
                    notification_type=result.notification_type,
                )
                return result

        reason = "No classifier matched the message"
        self._logger.debug(
            "Classification failed",
            message_id=message.id.value,
            reason=reason,
        )
        raise ClassificationError(message_id=message.id.value, reason=reason)
