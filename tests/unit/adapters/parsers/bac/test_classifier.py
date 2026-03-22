"""Tests for BACClassifier — BAC bank notification classifier."""

from datetime import datetime

import pytest

from bank_ingest.adapters.parsers.bac.classifier import BACClassifier
from bank_ingest.domain.entities import SourceMessage
from bank_ingest.domain.enums import Bank, NotificationType
from bank_ingest.domain.value_objects import MessageId


def _make_message(
    sender: str = "alertasynotificaciones@notificacionesbac.com",
    subject: str = "Notificacion de transaccion",
    body_html: str = "<p>transaction</p>",
) -> SourceMessage:
    return SourceMessage(
        id=MessageId(value="msg-001"),
        sender=sender,
        subject=subject,
        body_html=body_html,
        received_at=datetime(2026, 3, 16, 8, 27),
    )


@pytest.fixture
def classifier() -> BACClassifier:
    return BACClassifier()


class TestBACClassifierMatches:
    """Verify classifier matches BAC transaction notification emails."""

    def test_matches_bac_transaction_notification(
        self, classifier: BACClassifier
    ) -> None:
        message = _make_message()
        result = classifier.classify(message)

        assert result is not None
        assert result.bank == Bank.BAC
        assert result.notification_type == NotificationType.TRANSACTION_NOTIFICATION

    def test_matches_with_baccredomatic_sender(self, classifier: BACClassifier) -> None:
        message = _make_message(sender="alerts@baccredomatic.com")
        result = classifier.classify(message)

        assert result is not None
        assert result.bank == Bank.BAC

    def test_matches_case_insensitive_sender(self, classifier: BACClassifier) -> None:
        message = _make_message(
            sender="Alertas@NotificacionesBAC.com",
        )
        result = classifier.classify(message)

        assert result is not None
        assert result.bank == Bank.BAC

    def test_matches_case_insensitive_subject(self, classifier: BACClassifier) -> None:
        message = _make_message(subject="NOTIFICACION DE TRANSACCION")
        result = classifier.classify(message)

        assert result is not None
        assert result.notification_type == NotificationType.TRANSACTION_NOTIFICATION

    def test_matches_subject_with_accent(self, classifier: BACClassifier) -> None:
        message = _make_message(subject="Notificación de transacción")
        result = classifier.classify(message)

        assert result is not None
        assert result.notification_type == NotificationType.TRANSACTION_NOTIFICATION


class TestBACClassifierRejectsNonMatching:
    """Verify classifier returns None for non-BAC or non-transaction messages."""

    def test_returns_none_for_non_bac_sender(self, classifier: BACClassifier) -> None:
        message = _make_message(sender="noreply@otherbank.com")
        result = classifier.classify(message)

        assert result is None

    def test_returns_none_for_non_transaction_subject(
        self, classifier: BACClassifier
    ) -> None:
        message = _make_message(subject="Estado de cuenta mensual")
        result = classifier.classify(message)

        assert result is None

    def test_returns_none_when_sender_matches_but_subject_does_not(
        self, classifier: BACClassifier
    ) -> None:
        message = _make_message(
            sender="alertasynotificaciones@notificacionesbac.com",
            subject="Bienvenido a BAC",
        )
        result = classifier.classify(message)

        assert result is None

    def test_returns_none_when_subject_matches_but_sender_does_not(
        self, classifier: BACClassifier
    ) -> None:
        message = _make_message(
            sender="noreply@randombank.com",
            subject="Notificacion de transaccion",
        )
        result = classifier.classify(message)

        assert result is None
