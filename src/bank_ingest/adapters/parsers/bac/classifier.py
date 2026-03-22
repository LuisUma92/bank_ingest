"""BAC bank notification classifier."""

import unicodedata

from bank_ingest.domain.entities import ClassificationResult, SourceMessage
from bank_ingest.domain.enums import Bank, NotificationType
from bank_ingest.domain.ports.classifier import ClassifierPort

_BAC_SENDER_DOMAINS = ("notificacionesbac.com", "baccredomatic.com")

_TRANSACTION_SUBJECT_KEYWORDS = ("notificacion de transaccion",)


def _strip_accents(text: str) -> str:
    """Remove diacritical marks from text for accent-insensitive matching."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class BACClassifier(ClassifierPort):
    """Classifies messages from BAC Credomatic bank.

    Matches when both conditions hold:
    - sender domain is a known BAC domain
    - subject contains transaction notification keywords
    """

    def classify(self, message: SourceMessage) -> ClassificationResult | None:
        if not self._is_bac_sender(message.sender):
            return None

        if not self._is_transaction_notification(message.subject):
            return None

        return ClassificationResult(
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )

    def _is_bac_sender(self, sender: str) -> bool:
        sender_lower = sender.lower()
        return any(domain in sender_lower for domain in _BAC_SENDER_DOMAINS)

    def _is_transaction_notification(self, subject: str) -> bool:
        normalized = _strip_accents(subject).lower()
        return any(kw in normalized for kw in _TRANSACTION_SUBJECT_KEYWORDS)
