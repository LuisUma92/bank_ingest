"""Tests for ProcessInboxBatch use case — full pipeline orchestration."""

from datetime import UTC, datetime

from bank_ingest.application.policies.error_policy import ErrorPolicy
from bank_ingest.application.policies.storage_policy import StoragePolicy
from bank_ingest.application.use_cases.classify_message import ClassifyMessage
from bank_ingest.application.use_cases.fetch_labeled_messages import (
    FetchLabeledMessages,
)
from bank_ingest.application.use_cases.parse_message import ParseMessage
from bank_ingest.application.use_cases.persist_event import PersistEvent
from bank_ingest.application.use_cases.process_inbox_batch import ProcessInboxBatch
from bank_ingest.domain.entities import (
    ClassificationResult,
    FinancialEvent,
    SourceMessage,
)
from bank_ingest.domain.enums import Bank, NotificationType, ProcessingResult
from bank_ingest.domain.value_objects import MessageId
from unit.application.fakes import (
    FakeEventRepository,
    FakeLogger,
    FakeMessageSource,
    FakeMessageStore,
    FakeParser,
    FakeProcessingState,
    MatchingClassifier,
    NonMatchingClassifier,
)


def _make_batch(
    source_messages: list[SourceMessage],
    financial_event: FinancialEvent,
    classification: ClassificationResult,
    storage_policy: StoragePolicy | None = None,
    error_policy: ErrorPolicy | None = None,
    classifier_matches: bool = True,
) -> tuple[
    ProcessInboxBatch,
    FakeMessageStore,
    FakeProcessingState,
    FakeLogger,
    FakeEventRepository,
]:
    """Build a fully wired ProcessInboxBatch with fakes."""
    logger = FakeLogger()
    store = FakeMessageStore()
    state = FakeProcessingState()
    repo = FakeEventRepository()

    source = FakeMessageSource(messages=source_messages)
    fetch = FetchLabeledMessages(source=source, logger=logger)

    classifier = (
        MatchingClassifier(classification)
        if classifier_matches
        else NonMatchingClassifier()
    )
    classify = ClassifyMessage(classifiers=[classifier], logger=logger)

    parser = FakeParser(
        event=financial_event,
        bank=Bank.BAC,
        notification_type=NotificationType.TRANSACTION_NOTIFICATION,
    )
    parse = ParseMessage(
        parsers={(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): parser},
        logger=logger,
    )

    persist = PersistEvent(repository=repo, logger=logger)

    batch = ProcessInboxBatch(
        fetch=fetch,
        classify=classify,
        parse=parse,
        persist=persist,
        message_store=store,
        processing_state=state,
        logger=logger,
        storage_policy=storage_policy or StoragePolicy.default(),
        error_policy=error_policy or ErrorPolicy.default(),
    )
    return batch, store, state, logger, repo


class TestProcessInboxBatchHappyPath:
    def test_empty_inbox_returns_zero_counts(
        self, financial_event: FinancialEvent, classification: ClassificationResult
    ) -> None:
        batch, _store, _state, _logger, _repo = _make_batch(
            [], financial_event, classification
        )

        result = batch.execute(label="Transacciones")

        assert result.total == 0
        assert result.processed == 0
        assert result.failed == 0
        assert result.skipped == 0
        assert result.results == []

    def test_single_message_processed_successfully(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        batch, _store, _state, _logger, _repo = _make_batch(
            [source_message], financial_event, classification
        )

        result = batch.execute(label="Transacciones")

        assert result.total == 1
        assert result.processed == 1
        assert result.failed == 0
        assert result.skipped == 0

    def test_processed_result_contains_event_id(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        batch, _store, _state, _logger, _repo = _make_batch(
            [source_message], financial_event, classification
        )

        result = batch.execute(label="Transacciones")

        assert result.results[0].status == ProcessingResult.PROCESSED
        assert result.results[0].event_id == financial_event.id

    def test_mark_processed_called_on_success(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        batch, _store, state, _logger, _repo = _make_batch(
            [source_message], financial_event, classification
        )

        batch.execute(label="Transacciones")

        assert source_message.id in state.processed

    def test_store_raw_called_when_policy_enabled(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        policy = StoragePolicy(
            store_raw=True, store_rendered=True, store_parsed=True, store_errors=True
        )
        batch, store, _state, _logger, _repo = _make_batch(
            [source_message], financial_event, classification, storage_policy=policy
        )

        batch.execute(label="Transacciones")

        assert source_message in store.raw_stored

    def test_store_parsed_called_when_policy_enabled(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        policy = StoragePolicy(
            store_raw=True, store_rendered=True, store_parsed=True, store_errors=True
        )
        batch, store, _state, _logger, _repo = _make_batch(
            [source_message], financial_event, classification, storage_policy=policy
        )

        batch.execute(label="Transacciones")

        assert len(store.parsed_stored) == 1
        assert store.parsed_stored[0][0] == source_message.id

    def test_multiple_messages_all_processed(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        from bank_ingest.domain.enums import Currency, TransactionType
        from bank_ingest.domain.value_objects import CardInfo, EventId, Money

        msg2 = SourceMessage(
            id=MessageId(value="msg-002"),
            sender="banco@bac.cr",
            subject="Another notification",
            body_html="<html><body>Other</body></html>",
            received_at=datetime(2024, 1, 16, tzinfo=UTC),
        )
        # Use a parser that generates unique events per message
        logger = FakeLogger()
        store = FakeMessageStore()
        state = FakeProcessingState()
        repo = FakeEventRepository()

        events_by_message = {
            source_message.id.value: financial_event,
        }
        event2 = FinancialEvent(
            id=EventId(value="evt-002"),
            message_id=MessageId(value="msg-002"),
            bank=Bank.BAC,
            event_type=NotificationType.TRANSACTION_NOTIFICATION,
            merchant="WALMART",
            transaction_date=datetime(2024, 1, 16, tzinfo=UTC),
            card=CardInfo(brand="VISA", last4="5678"),
            authorization_code="AUTH456",
            transaction_type=TransactionType.PURCHASE,
            amount=Money(amount=10000, currency=Currency.CRC),
            raw_data={},
            created_at=datetime(2024, 1, 16, tzinfo=UTC),
        )
        events_by_message["msg-002"] = event2

        class MultiParser(FakeParser):
            def parse(self, message: SourceMessage) -> FinancialEvent:
                return events_by_message[message.id.value]

        multi_parser = MultiParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )

        source = FakeMessageSource(messages=[source_message, msg2])
        fetch = FetchLabeledMessages(source=source, logger=logger)
        classify = ClassifyMessage(
            classifiers=[MatchingClassifier(classification)], logger=logger
        )
        parse = ParseMessage(
            parsers={
                (Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): multi_parser
            },
            logger=logger,
        )
        persist = PersistEvent(repository=repo, logger=logger)

        batch = ProcessInboxBatch(
            fetch=fetch,
            classify=classify,
            parse=parse,
            persist=persist,
            message_store=store,
            processing_state=state,
            logger=logger,
            storage_policy=StoragePolicy.default(),
            error_policy=ErrorPolicy.default(),
        )

        result = batch.execute(label="Transacciones")

        assert result.total == 2
        assert result.processed == 2
        assert result.failed == 0


class TestProcessInboxBatchClassificationFailure:
    def test_unclassifiable_message_is_skipped(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        batch, _store, _state, _logger, _repo = _make_batch(
            [source_message], financial_event, classification, classifier_matches=False
        )

        result = batch.execute(label="Transacciones")

        assert result.total == 1
        assert result.skipped == 1
        assert result.processed == 0
        assert result.failed == 0

    def test_mark_skipped_called_on_classification_failure(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        batch, _store, state, _logger, _repo = _make_batch(
            [source_message], financial_event, classification, classifier_matches=False
        )

        batch.execute(label="Transacciones")

        assert len(state.skipped) == 1
        assert state.skipped[0][0] == source_message.id

    def test_skipped_result_has_no_event_id(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        batch, _store, _state, _logger, _repo = _make_batch(
            [source_message], financial_event, classification, classifier_matches=False
        )

        result = batch.execute(label="Transacciones")

        assert result.results[0].status == ProcessingResult.SKIPPED
        assert result.results[0].event_id is None


class TestProcessInboxBatchParsingFailure:
    def test_parsing_failure_marks_message_as_failed(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        from bank_ingest.domain.exceptions import ParsingError

        logger = FakeLogger()
        store = FakeMessageStore()
        state = FakeProcessingState()
        repo = FakeEventRepository()

        class FailingParser(FakeParser):
            def parse(self, msg: SourceMessage) -> FinancialEvent:
                raise ParsingError(msg.id.value, "bad HTML")

        source = FakeMessageSource(messages=[source_message])
        fetch = FetchLabeledMessages(source=source, logger=logger)
        classify = ClassifyMessage(
            classifiers=[MatchingClassifier(classification)], logger=logger
        )
        failing_parser = FailingParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        parse = ParseMessage(
            parsers={
                (Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): failing_parser
            },
            logger=logger,
        )
        persist = PersistEvent(repository=repo, logger=logger)

        batch = ProcessInboxBatch(
            fetch=fetch,
            classify=classify,
            parse=parse,
            persist=persist,
            message_store=store,
            processing_state=state,
            logger=logger,
            storage_policy=StoragePolicy.default(),
            error_policy=ErrorPolicy.default(),
        )

        result = batch.execute(label="Transacciones")

        assert result.total == 1
        assert result.failed == 1
        assert result.results[0].status == ProcessingResult.FAILED
        assert state.failed[0][0] == source_message.id

    def test_error_artifact_stored_when_policy_enabled(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        from bank_ingest.domain.exceptions import ParsingError

        logger = FakeLogger()
        store = FakeMessageStore()
        state = FakeProcessingState()
        repo = FakeEventRepository()

        class FailingParser(FakeParser):
            def parse(self, msg: SourceMessage) -> FinancialEvent:
                raise ParsingError(msg.id.value, "bad HTML")

        source = FakeMessageSource(messages=[source_message])
        fetch = FetchLabeledMessages(source=source, logger=logger)
        classify = ClassifyMessage(
            classifiers=[MatchingClassifier(classification)], logger=logger
        )
        failing_parser = FailingParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        parse = ParseMessage(
            parsers={
                (Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): failing_parser
            },
            logger=logger,
        )
        persist = PersistEvent(repository=repo, logger=logger)

        error_policy = ErrorPolicy(continue_on_error=True, store_error_artifacts=True)
        batch = ProcessInboxBatch(
            fetch=fetch,
            classify=classify,
            parse=parse,
            persist=persist,
            message_store=store,
            processing_state=state,
            logger=logger,
            storage_policy=StoragePolicy.default(),
            error_policy=error_policy,
        )

        batch.execute(label="Transacciones")

        assert len(store.errors_stored) == 1
        assert store.errors_stored[0][0] == source_message.id

    def test_error_artifact_not_stored_when_policy_disabled(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        from bank_ingest.domain.exceptions import ParsingError

        logger = FakeLogger()
        store = FakeMessageStore()
        state = FakeProcessingState()
        repo = FakeEventRepository()

        class FailingParser(FakeParser):
            def parse(self, msg: SourceMessage) -> FinancialEvent:
                raise ParsingError(msg.id.value, "bad HTML")

        source = FakeMessageSource(messages=[source_message])
        fetch = FetchLabeledMessages(source=source, logger=logger)
        classify = ClassifyMessage(
            classifiers=[MatchingClassifier(classification)], logger=logger
        )
        failing_parser = FailingParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        parse = ParseMessage(
            parsers={
                (Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): failing_parser
            },
            logger=logger,
        )
        persist = PersistEvent(repository=repo, logger=logger)

        error_policy = ErrorPolicy(continue_on_error=True, store_error_artifacts=False)
        batch = ProcessInboxBatch(
            fetch=fetch,
            classify=classify,
            parse=parse,
            persist=persist,
            message_store=store,
            processing_state=state,
            logger=logger,
            storage_policy=StoragePolicy.default(),
            error_policy=error_policy,
        )

        batch.execute(label="Transacciones")

        assert len(store.errors_stored) == 0

    def test_batch_continues_after_error_when_policy_allows(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        from bank_ingest.domain.exceptions import ParsingError

        msg2 = SourceMessage(
            id=MessageId(value="msg-002"),
            sender="banco@bac.cr",
            subject="Second notification",
            body_html="<html><body>Second</body></html>",
            received_at=datetime(2024, 1, 16, tzinfo=UTC),
        )

        logger = FakeLogger()
        store = FakeMessageStore()
        state = FakeProcessingState()
        repo = FakeEventRepository()

        call_count = {"n": 0}

        class ConditionalFailParser(FakeParser):
            def parse(self, msg: SourceMessage) -> FinancialEvent:
                call_count["n"] += 1
                if call_count["n"] == 1:
                    raise ParsingError(msg.id.value, "first fails")
                return financial_event

        source = FakeMessageSource(messages=[source_message, msg2])
        fetch = FetchLabeledMessages(source=source, logger=logger)
        classify = ClassifyMessage(
            classifiers=[MatchingClassifier(classification)], logger=logger
        )
        parser = ConditionalFailParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        parse = ParseMessage(
            parsers={(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): parser},
            logger=logger,
        )
        persist = PersistEvent(repository=repo, logger=logger)

        batch = ProcessInboxBatch(
            fetch=fetch,
            classify=classify,
            parse=parse,
            persist=persist,
            message_store=store,
            processing_state=state,
            logger=logger,
            storage_policy=StoragePolicy.default(),
            error_policy=ErrorPolicy(
                continue_on_error=True, store_error_artifacts=True
            ),
        )

        result = batch.execute(label="Transacciones")

        assert result.total == 2
        assert result.failed == 1
        assert result.processed == 1

    def test_batch_stops_on_first_error_when_strict_policy(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        from bank_ingest.domain.exceptions import ParsingError

        msg2 = SourceMessage(
            id=MessageId(value="msg-002"),
            sender="banco@bac.cr",
            subject="Second notification",
            body_html="<html><body>Second</body></html>",
            received_at=datetime(2024, 1, 16, tzinfo=UTC),
        )

        logger = FakeLogger()
        store = FakeMessageStore()
        state = FakeProcessingState()
        repo = FakeEventRepository()

        class AlwaysFailParser(FakeParser):
            def parse(self, msg: SourceMessage) -> FinancialEvent:
                raise ParsingError(msg.id.value, "always fails")

        source = FakeMessageSource(messages=[source_message, msg2])
        fetch = FetchLabeledMessages(source=source, logger=logger)
        classify = ClassifyMessage(
            classifiers=[MatchingClassifier(classification)], logger=logger
        )
        parser = AlwaysFailParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        parse = ParseMessage(
            parsers={(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): parser},
            logger=logger,
        )
        persist = PersistEvent(repository=repo, logger=logger)

        batch = ProcessInboxBatch(
            fetch=fetch,
            classify=classify,
            parse=parse,
            persist=persist,
            message_store=store,
            processing_state=state,
            logger=logger,
            storage_policy=StoragePolicy.default(),
            error_policy=ErrorPolicy.strict(),
        )

        result = batch.execute(label="Transacciones")

        # Both messages fetched, but only first processed (failed), second never attempted
        assert result.total == 2
        assert result.failed == 1
        assert result.processed == 0
        assert len(result.results) == 1  # Loop broke after first failure


class TestProcessInboxBatchStoragePolicy:
    def test_store_raw_not_called_when_policy_disabled(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        policy = StoragePolicy(
            store_raw=False,
            store_rendered=False,
            store_parsed=False,
            store_errors=False,
        )
        batch, store, _state, _logger, _repo = _make_batch(
            [source_message], financial_event, classification, storage_policy=policy
        )

        batch.execute(label="Transacciones")

        assert len(store.raw_stored) == 0

    def test_store_parsed_not_called_when_policy_disabled(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        policy = StoragePolicy(
            store_raw=False,
            store_rendered=False,
            store_parsed=False,
            store_errors=False,
        )
        batch, store, _state, _logger, _repo = _make_batch(
            [source_message], financial_event, classification, storage_policy=policy
        )

        batch.execute(label="Transacciones")

        assert len(store.parsed_stored) == 0


class TestProcessInboxBatchDuplicateEvent:
    def test_duplicate_event_not_saved_twice(
        self,
        source_message: SourceMessage,
        financial_event: FinancialEvent,
        classification: ClassificationResult,
    ) -> None:
        logger = FakeLogger()
        store = FakeMessageStore()
        state = FakeProcessingState()
        # Pre-seed the repo with the event already existing
        repo = FakeEventRepository(existing_ids={financial_event.id.value})

        source = FakeMessageSource(messages=[source_message])
        fetch = FetchLabeledMessages(source=source, logger=logger)
        classify = ClassifyMessage(
            classifiers=[MatchingClassifier(classification)], logger=logger
        )
        parser = FakeParser(
            event=financial_event,
            bank=Bank.BAC,
            notification_type=NotificationType.TRANSACTION_NOTIFICATION,
        )
        parse = ParseMessage(
            parsers={(Bank.BAC, NotificationType.TRANSACTION_NOTIFICATION): parser},
            logger=logger,
        )
        persist = PersistEvent(repository=repo, logger=logger)

        batch = ProcessInboxBatch(
            fetch=fetch,
            classify=classify,
            parse=parse,
            persist=persist,
            message_store=store,
            processing_state=state,
            logger=logger,
            storage_policy=StoragePolicy.default(),
            error_policy=ErrorPolicy.default(),
        )

        result = batch.execute(label="Transacciones")

        # Duplicate is still counted as processed (event already existed)
        assert result.total == 1
        # The event is NOT in the events dict since it was skipped by PersistEvent
        assert repo.find_by_id(financial_event.id) is None
        assert any(
            "duplicate" in w.lower() or "exists" in w.lower() for w in logger.warnings
        )
