"""Unit tests for FilesystemMessageStore."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from bank_ingest.adapters.outbound.storage.filesystem_store import (
    FilesystemMessageStore,
)
from bank_ingest.domain.entities import SourceMessage
from bank_ingest.domain.exceptions import StorageError
from bank_ingest.domain.value_objects import MessageId


def _make_source_message(
    msg_id: str = "msg-001",
    received_at: datetime | None = None,
) -> SourceMessage:
    return SourceMessage(
        id=MessageId(value=msg_id),
        sender="bank@example.com",
        subject="Transaction Notification",
        body_html="<p>Hello</p>",
        received_at=received_at or datetime(2025, 3, 15, 14, 30, 0),
    )


@pytest.fixture
def store(tmp_path: Path) -> FilesystemMessageStore:
    return FilesystemMessageStore(base_path=tmp_path)


class TestStoreRaw:
    def test_writes_json_file(
        self, store: FilesystemMessageStore, tmp_path: Path
    ) -> None:
        msg = _make_source_message()
        store.store_raw(msg)

        files = list(tmp_path.rglob("*.json"))
        assert len(files) == 1
        content = json.loads(files[0].read_text())
        assert content["sender"] == "bank@example.com"
        assert content["subject"] == "Transaction Notification"

    def test_uses_model_dump_json_format(
        self, store: FilesystemMessageStore, tmp_path: Path
    ) -> None:
        msg = _make_source_message()
        store.store_raw(msg)

        files = list(tmp_path.rglob("*.json"))
        content = json.loads(files[0].read_text())
        assert content["id"]["value"] == "msg-001"
        assert "received_at" in content

    def test_date_partitioned_path(
        self, store: FilesystemMessageStore, tmp_path: Path
    ) -> None:
        msg = _make_source_message()
        with patch(
            "bank_ingest.adapters.outbound.storage.filesystem_store._now",
            return_value=datetime(2025, 3, 15),
        ):
            store.store_raw(msg)

        expected = tmp_path / "raw_messages" / "2025" / "03" / "15" / "msg-001.json"
        assert expected.exists()


class TestStoreRendered:
    def test_writes_txt_file(
        self, store: FilesystemMessageStore, tmp_path: Path
    ) -> None:
        mid = MessageId(value="msg-002")
        with patch(
            "bank_ingest.adapters.outbound.storage.filesystem_store._now",
            return_value=datetime(2025, 6, 1),
        ):
            store.store_rendered(mid, "Plain text content")

        expected = tmp_path / "rendered" / "2025" / "06" / "01" / "msg-002.txt"
        assert expected.exists()
        assert expected.read_text() == "Plain text content"


class TestStoreParsed:
    def test_writes_json_file(
        self, store: FilesystemMessageStore, tmp_path: Path
    ) -> None:
        mid = MessageId(value="msg-003")
        data: dict[str, object] = {"merchant": "AMAZON", "amount": 150000}
        with patch(
            "bank_ingest.adapters.outbound.storage.filesystem_store._now",
            return_value=datetime(2025, 1, 20),
        ):
            store.store_parsed(mid, data)

        expected = tmp_path / "parsed" / "2025" / "01" / "20" / "msg-003.json"
        assert expected.exists()
        content = json.loads(expected.read_text())
        assert content["merchant"] == "AMAZON"
        assert content["amount"] == 150000

    def test_handles_nested_data(
        self, store: FilesystemMessageStore, tmp_path: Path
    ) -> None:
        mid = MessageId(value="msg-004")
        data: dict[str, object] = {"nested": {"key": "value"}, "list": [1, 2]}
        store.store_parsed(mid, data)

        files = list(tmp_path.rglob("*.json"))
        content = json.loads(files[0].read_text())
        assert content["nested"]["key"] == "value"
        assert content["list"] == [1, 2]


class TestStoreError:
    def test_writes_error_json(
        self, store: FilesystemMessageStore, tmp_path: Path
    ) -> None:
        mid = MessageId(value="msg-005")
        with patch(
            "bank_ingest.adapters.outbound.storage.filesystem_store._now",
            return_value=datetime(2025, 12, 31),
        ):
            store.store_error(mid, "Parser failed: unknown format")

        expected = tmp_path / "errors" / "2025" / "12" / "31" / "msg-005.json"
        assert expected.exists()
        content = json.loads(expected.read_text())
        assert content["message_id"] == "msg-005"
        assert content["error"] == "Parser failed: unknown format"


class TestStorageErrorHandling:
    def test_raises_storage_error_on_io_failure(self, tmp_path: Path) -> None:
        store = FilesystemMessageStore(base_path=tmp_path / "nonexistent")
        mid = MessageId(value="msg-006")
        with (
            patch(
                "bank_ingest.adapters.outbound.storage.filesystem_store._now",
                return_value=datetime(2025, 1, 1),
            ),
            patch("pathlib.Path.mkdir", side_effect=PermissionError("denied")),
            pytest.raises(StorageError),
        ):
            store.store_rendered(mid, "content")


class TestIdempotentOverwrite:
    def test_overwrite_same_message_id(
        self, store: FilesystemMessageStore, tmp_path: Path
    ) -> None:
        mid = MessageId(value="msg-007")
        with patch(
            "bank_ingest.adapters.outbound.storage.filesystem_store._now",
            return_value=datetime(2025, 5, 10),
        ):
            store.store_rendered(mid, "first version")
            store.store_rendered(mid, "second version")

        expected = tmp_path / "rendered" / "2025" / "05" / "10" / "msg-007.txt"
        assert expected.read_text() == "second version"
