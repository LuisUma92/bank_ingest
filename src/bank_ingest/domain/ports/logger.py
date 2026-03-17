"""Port definition for the logger (outbound adapter interface)."""

from abc import ABC, abstractmethod
from typing import Any


class LoggerPort(ABC):
    """Abstract port for structured logging.

    Implementations bridge this interface to a concrete logging backend
    (e.g. Python's standard logging, structlog, etc.).
    """

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log an informational message.

        Args:
            message: The log message text.
            **kwargs: Optional structured key-value context.
        """

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message.

        Args:
            message: The log message text.
            **kwargs: Optional structured key-value context.
        """

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message.

        Args:
            message: The log message text.
            **kwargs: Optional structured key-value context.
        """

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message.

        Args:
            message: The log message text.
            **kwargs: Optional structured key-value context.
        """
