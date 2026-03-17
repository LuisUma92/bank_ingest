"""Tests for ClassifyMessage use case."""

import pytest

from bank_ingest.application.use_cases.classify_message import ClassifyMessage
from bank_ingest.domain.entities import ClassificationResult, SourceMessage
from bank_ingest.domain.enums import Bank, NotificationType
from bank_ingest.domain.exceptions import ClassificationError
from unit.application.fakes import (
    FakeLogger,
    MatchingClassifier,
    NonMatchingClassifier,
)


class TestClassifyMessage:
    def test_returns_result_from_first_matching_classifier(
        self, source_message: SourceMessage, classification: ClassificationResult
    ) -> None:
        use_case = ClassifyMessage(
            classifiers=[MatchingClassifier(classification)],
            logger=FakeLogger(),
        )

        result = use_case.execute(source_message)

        assert result.bank == Bank.BAC
        assert result.notification_type == NotificationType.TRANSACTION_NOTIFICATION

    def test_skips_non_matching_classifiers(
        self, source_message: SourceMessage, classification: ClassificationResult
    ) -> None:
        use_case = ClassifyMessage(
            classifiers=[NonMatchingClassifier(), MatchingClassifier(classification)],
            logger=FakeLogger(),
        )

        result = use_case.execute(source_message)

        assert result.bank == Bank.BAC

    def test_raises_classification_error_when_no_classifier_matches(
        self, source_message: SourceMessage
    ) -> None:
        use_case = ClassifyMessage(
            classifiers=[NonMatchingClassifier(), NonMatchingClassifier()],
            logger=FakeLogger(),
        )

        with pytest.raises(ClassificationError) as exc_info:
            use_case.execute(source_message)

        assert exc_info.value.message_id == source_message.id.value

    def test_raises_classification_error_with_empty_classifier_list(
        self, source_message: SourceMessage
    ) -> None:
        use_case = ClassifyMessage(classifiers=[], logger=FakeLogger())

        with pytest.raises(ClassificationError):
            use_case.execute(source_message)

    def test_stops_at_first_matching_classifier(
        self, source_message: SourceMessage
    ) -> None:
        first_classification = ClassificationResult(
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        second_classification = ClassificationResult(
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        use_case = ClassifyMessage(
            classifiers=[
                MatchingClassifier(first_classification),
                MatchingClassifier(second_classification),
            ],
            logger=FakeLogger(),
        )

        result = use_case.execute(source_message)

        assert result is first_classification

    def test_logs_successful_classification(
        self, source_message: SourceMessage, classification: ClassificationResult
    ) -> None:
        logger = FakeLogger()
        use_case = ClassifyMessage(
            classifiers=[MatchingClassifier(classification)],
            logger=logger,
        )

        use_case.execute(source_message)

        assert len(logger.infos) > 0 or len(logger.debugs) > 0
