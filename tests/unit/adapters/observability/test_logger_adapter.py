"""Unit tests for StructuredLoggerAdapter."""

import logging

import pytest

from bank_ingest.adapters.outbound.observability.logger_adapter import (
    StructuredLoggerAdapter,
)
from bank_ingest.domain.ports.logger import LoggerPort


class TestLogLevels:
    def test_info(self, caplog: pytest.LogCaptureFixture) -> None:
        adapter = StructuredLoggerAdapter(name="test")
        with caplog.at_level(logging.INFO, logger="test"):
            adapter.info("hello")
        assert "hello" in caplog.text

    def test_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        adapter = StructuredLoggerAdapter(name="test")
        with caplog.at_level(logging.WARNING, logger="test"):
            adapter.warning("watch out")
        assert "watch out" in caplog.text

    def test_error(self, caplog: pytest.LogCaptureFixture) -> None:
        adapter = StructuredLoggerAdapter(name="test")
        with caplog.at_level(logging.ERROR, logger="test"):
            adapter.error("boom")
        assert "boom" in caplog.text

    def test_debug(self, caplog: pytest.LogCaptureFixture) -> None:
        adapter = StructuredLoggerAdapter(name="test")
        with caplog.at_level(logging.DEBUG, logger="test"):
            adapter.debug("trace")
        assert "trace" in caplog.text


class TestStructuredContext:
    def test_kwargs_appended(self, caplog: pytest.LogCaptureFixture) -> None:
        adapter = StructuredLoggerAdapter(name="test")
        with caplog.at_level(logging.INFO, logger="test"):
            adapter.info("processed", message_id="msg-001", bank="BAC")
        assert "message_id=msg-001" in caplog.text
        assert "bank=BAC" in caplog.text

    def test_no_kwargs_plain_message(self, caplog: pytest.LogCaptureFixture) -> None:
        adapter = StructuredLoggerAdapter(name="test")
        with caplog.at_level(logging.INFO, logger="test"):
            adapter.info("simple message")
        assert "simple message" in caplog.text
        assert "|" not in caplog.text


class TestLoggerName:
    def test_default_name(self) -> None:
        adapter = StructuredLoggerAdapter()
        assert adapter._logger.name == "bank_ingest"

    def test_custom_name(self) -> None:
        adapter = StructuredLoggerAdapter(name="custom")
        assert adapter._logger.name == "custom"


class TestImplementsPort:
    def test_is_logger_port(self) -> None:
        adapter = StructuredLoggerAdapter()
        assert isinstance(adapter, LoggerPort)
