"""Content hashing utilities for deduplication."""
import hashlib

# Separator used to prevent hash collisions between concatenated fields
_FIELD_SEPARATOR = "\x00"


def hash_content(content: str) -> str:
    """Generate a SHA-256 hex digest of the given content.

    Used for deduplication of messages and artifact storage.

    Args:
        content: Any string content to hash.

    Returns:
        64-character lowercase hexadecimal SHA-256 digest.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def hash_message(sender: str, subject: str, body: str) -> str:
    """Generate a deterministic hash from message fields.

    Combines sender, subject, and body with a null-byte separator to produce
    a unique hash for deduplication purposes. The separator prevents collisions
    between inputs where field content bleeds into adjacent fields.

    Args:
        sender: Email sender address.
        subject: Email subject line.
        body: Email body content.

    Returns:
        64-character lowercase hexadecimal SHA-256 digest.
    """
    combined = _FIELD_SEPARATOR.join([sender, subject, body])
    return hash_content(combined)
