"""Application layer DTOs — frozen pydantic models for use case results."""

from pydantic import BaseModel, ConfigDict

from bank_ingest.domain.enums import ProcessingResult
from bank_ingest.domain.value_objects import EventId, MessageId


class MessageProcessingResult(BaseModel):
    """Result of processing a single source message through the pipeline."""

    model_config = ConfigDict(frozen=True)

    message_id: MessageId
    status: ProcessingResult
    event_id: EventId | None
    error: str | None


class BatchProcessingResult(BaseModel):
    """Aggregate result of processing a batch of messages."""

    model_config = ConfigDict(frozen=True)

    total: int
    processed: int
    failed: int
    skipped: int
    results: list[MessageProcessingResult]
