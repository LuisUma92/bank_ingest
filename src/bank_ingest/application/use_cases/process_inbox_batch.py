"""ProcessInboxBatch use case — orchestrates the full message processing pipeline."""

from bank_ingest.application.dtos import BatchProcessingResult, MessageProcessingResult
from bank_ingest.application.policies.error_policy import ErrorPolicy
from bank_ingest.application.policies.storage_policy import StoragePolicy
from bank_ingest.application.use_cases.classify_message import ClassifyMessage
from bank_ingest.application.use_cases.fetch_labeled_messages import (
    FetchLabeledMessages,
)
from bank_ingest.application.use_cases.parse_message import ParseMessage
from bank_ingest.application.use_cases.persist_event import PersistEvent
from bank_ingest.domain.entities import SourceMessage
from bank_ingest.domain.enums import ProcessingResult
from bank_ingest.domain.exceptions import (
    ClassificationError,
    ParsingError,
    StorageError,
)
from bank_ingest.domain.ports.logger import LoggerPort
from bank_ingest.domain.ports.message_store import MessageStorePort
from bank_ingest.domain.ports.processing_state import ProcessingStatePort


class ProcessInboxBatch:
    """Orchestrates the end-to-end processing pipeline for a batch of messages.

    Pipeline per message:
    1. Optionally store raw artifact
    2. Classify → skip on ClassificationError
    3. Parse → fail on ParsingError
    4. Optionally store parsed artifact
    5. Persist event
    6. Mark processed / failed / skipped in processing state
    """

    def __init__(
        self,
        fetch: FetchLabeledMessages,
        classify: ClassifyMessage,
        parse: ParseMessage,
        persist: PersistEvent,
        message_store: MessageStorePort,
        processing_state: ProcessingStatePort,
        logger: LoggerPort,
        storage_policy: StoragePolicy,
        error_policy: ErrorPolicy,
    ) -> None:
        self._fetch = fetch
        self._classify = classify
        self._parse = parse
        self._persist = persist
        self._message_store = message_store
        self._processing_state = processing_state
        self._logger = logger
        self._storage_policy = storage_policy
        self._error_policy = error_policy

    def execute(self, label: str) -> BatchProcessingResult:
        """Process all messages with the given label.

        Args:
            label: The mail label to fetch and process.

        Returns:
            A BatchProcessingResult with counts and per-message results.
        """
        messages = self._fetch.execute(label)
        total = len(messages)

        results: list[MessageProcessingResult] = []
        processed = 0
        failed = 0
        skipped = 0

        for message in messages:
            result = self._process_single(message)
            results.append(result)

            if result.status == ProcessingResult.PROCESSED:
                processed += 1
            elif result.status == ProcessingResult.FAILED:
                failed += 1
                if not self._error_policy.continue_on_error:
                    break
            else:
                skipped += 1

        return BatchProcessingResult(
            total=total,
            processed=processed,
            failed=failed,
            skipped=skipped,
            results=results,
        )

    def _process_single(
        self,
        message: SourceMessage,
    ) -> MessageProcessingResult:
        """Process a single message through the pipeline."""
        # Step 1: optionally store raw artifact
        if self._storage_policy.store_raw:
            try:
                self._message_store.store_raw(message)
            except StorageError:
                self._logger.warning(
                    "Failed to store raw artifact, continuing",
                    message_id=message.id.value,
                )

        # Step 2: classify
        try:
            classification = self._classify.execute(message)
        except ClassificationError as exc:
            self._processing_state.mark_skipped(message.id, exc.reason)
            return MessageProcessingResult(
                message_id=message.id,
                status=ProcessingResult.SKIPPED,
                event_id=None,
                error=None,
            )

        # Step 3: parse
        try:
            event = self._parse.execute(message, classification)
        except ParsingError as exc:
            reason = exc.reason[:500]  # Truncate to prevent PII leakage
            self._logger.error(
                "Parsing failed",
                message_id=message.id.value,
            )
            self._processing_state.mark_failed(message.id, reason)
            if self._error_policy.store_error_artifacts:
                try:
                    self._message_store.store_error(message.id, reason)
                except StorageError:
                    self._logger.warning(
                        "Failed to store error artifact",
                        message_id=message.id.value,
                    )
            return MessageProcessingResult(
                message_id=message.id,
                status=ProcessingResult.FAILED,
                event_id=None,
                error=reason,
            )

        # Step 4: optionally store parsed artifact
        if self._storage_policy.store_parsed:
            try:
                self._message_store.store_parsed(message.id, event.raw_data)
            except StorageError:
                self._logger.warning(
                    "Failed to store parsed artifact, continuing",
                    message_id=message.id.value,
                )

        # Step 5: persist event
        self._persist.execute(event)

        # Step 6: mark processed
        self._processing_state.mark_processed(message.id)
        return MessageProcessingResult(
            message_id=message.id,
            status=ProcessingResult.PROCESSED,
            event_id=event.id,
            error=None,
        )
