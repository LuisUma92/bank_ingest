"""Domain ports package — abstract interfaces for all external adapters."""

from bank_ingest.domain.ports.classifier import ClassifierPort
from bank_ingest.domain.ports.event_repository import EventRepositoryPort
from bank_ingest.domain.ports.logger import LoggerPort
from bank_ingest.domain.ports.message_source import MessageSourcePort
from bank_ingest.domain.ports.message_store import MessageStorePort
from bank_ingest.domain.ports.parser import ParserPort
from bank_ingest.domain.ports.processing_state import ProcessingStatePort

__all__ = [
    "ClassifierPort",
    "EventRepositoryPort",
    "LoggerPort",
    "MessageSourcePort",
    "MessageStorePort",
    "ParserPort",
    "ProcessingStatePort",
]
