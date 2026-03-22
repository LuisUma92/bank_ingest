"""Filesystem implementation of MessageStorePort."""

import json
from datetime import UTC, datetime
from pathlib import Path

from bank_ingest.domain.entities import SourceMessage
from bank_ingest.domain.exceptions import StorageError
from bank_ingest.domain.ports.message_store import MessageStorePort
from bank_ingest.domain.value_objects import MessageId


def _now() -> datetime:
    """Return current UTC datetime. Patchable for testing."""
    return datetime.now(UTC)


class FilesystemMessageStore(MessageStorePort):
    """Stores message artifacts as files in date-partitioned directories.

    Directory structure: {base_path}/{subdirectory}/{YYYY}/{MM}/{DD}/{message_id}.{ext}
    """

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path.resolve()

    def store_raw(self, message: SourceMessage) -> None:
        path = self._build_path("raw_messages", message.id, "json")
        data = message.model_dump(mode="json")
        self._write_json(path, data)

    def store_rendered(self, message_id: MessageId, content: str) -> None:
        path = self._build_path("rendered", message_id, "txt")
        self._write_text(path, content)

    def store_parsed(self, message_id: MessageId, data: dict[str, object]) -> None:
        path = self._build_path("parsed", message_id, "json")
        self._write_json(path, data)

    def store_error(self, message_id: MessageId, error: str) -> None:
        path = self._build_path("errors", message_id, "json")
        payload = {"message_id": message_id.value, "error": error}
        self._write_json(path, payload)

    def _build_path(
        self, subdirectory: str, message_id: MessageId, extension: str
    ) -> Path:
        now = _now()
        return (
            self._base_path
            / subdirectory
            / f"{now.year:04d}"
            / f"{now.month:02d}"
            / f"{now.day:02d}"
            / f"{message_id.value}.{extension}"
        )

    def _write_json(self, path: Path, data: object) -> None:
        self._ensure_parent(path)
        try:
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except OSError as exc:
            raise StorageError(f"Failed to write {path}: {exc}") from exc

    def _write_text(self, path: Path, content: str) -> None:
        self._ensure_parent(path)
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to write {path}: {exc}") from exc

    def _ensure_parent(self, path: Path) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError(
                f"Failed to create directory {path.parent}: {exc}"
            ) from exc
