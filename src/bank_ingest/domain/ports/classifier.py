"""ClassifierPort — abstract interface for bank notification classifiers."""

from abc import ABC, abstractmethod

from bank_ingest.domain.entities import ClassificationResult, SourceMessage


class ClassifierPort(ABC):
    """Classifies a source message to a known bank and notification type.

    Concrete implementations inspect message sender, subject, and body to
    determine which bank and notification type the message belongs to.
    Returns None when the message does not match this classifier.
    """

    @abstractmethod
    def classify(self, message: SourceMessage) -> ClassificationResult | None:
        """Attempt to classify the message.

        Args:
            message: The raw source message to classify.

        Returns:
            A ClassificationResult if the message matches, None otherwise.
        """
