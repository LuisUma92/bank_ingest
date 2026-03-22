"""Structured logger adapter implementing LoggerPort."""

import logging
from typing import Any

from bank_ingest.domain.ports.logger import LoggerPort


class StructuredLoggerAdapter(LoggerPort):
    """Logger that wraps Python's standard logging with structured context.

    Keyword arguments are formatted as "message | key1=val1 key2=val2".
    """

    def __init__(self, name: str = "bank_ingest") -> None:
        self._logger = logging.getLogger(name)

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(self._format(message, kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(self._format(message, kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        self._logger.error(self._format(message, kwargs))

    def debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(self._format(message, kwargs))

    def _format(self, message: str, context: dict[str, Any]) -> str:
        if not context:
            return message
        pairs = " ".join(f"{k}={self._sanitize(v)}" for k, v in context.items())
        return f"{message} | {pairs}"

    @staticmethod
    def _sanitize(value: object) -> str:
        """Escape newlines to prevent log injection."""
        return str(value).replace("\n", "\\n").replace("\r", "\\r")
