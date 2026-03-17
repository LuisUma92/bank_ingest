"""StoragePolicy — controls which artifacts are persisted during processing."""

from pydantic import BaseModel, ConfigDict


class StoragePolicy(BaseModel):
    """Flags controlling which storage operations are performed per message."""

    model_config = ConfigDict(frozen=True)

    store_raw: bool = True
    store_rendered: bool = True
    store_parsed: bool = True
    store_errors: bool = True

    @classmethod
    def default(cls) -> "StoragePolicy":
        """All storage operations enabled (same as zero-arg construction)."""
        return cls()

    @classmethod
    def minimal(cls) -> "StoragePolicy":
        """Only error artifacts are stored; all other storage is skipped."""
        return cls(
            store_raw=False,
            store_rendered=False,
            store_parsed=False,
            store_errors=True,
        )
