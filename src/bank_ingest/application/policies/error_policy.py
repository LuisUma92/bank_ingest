"""ErrorPolicy — controls how the pipeline responds to processing errors."""

from pydantic import BaseModel, ConfigDict


class ErrorPolicy(BaseModel):
    """Flags controlling error handling behavior during batch processing."""

    model_config = ConfigDict(frozen=True)

    continue_on_error: bool = True
    store_error_artifacts: bool = True

    @classmethod
    def default(cls) -> "ErrorPolicy":
        """Continue processing and store error artifacts on failure."""
        return cls()

    @classmethod
    def strict(cls) -> "ErrorPolicy":
        """Stop batch immediately on first error; still store error artifacts."""
        return cls(continue_on_error=False, store_error_artifacts=True)
