"""Tests for shared.hashing — SHA-256 content hashing."""

import hashlib

from bank_ingest.shared.hashing import hash_content, hash_message


class TestHashContent:
    """Unit tests for hash_content."""

    def test_returns_string(self):
        result = hash_content("hello")
        assert isinstance(result, str)

    def test_returns_hex_string(self):
        result = hash_content("hello")
        int(result, 16)  # raises ValueError if not hex

    def test_sha256_length(self):
        """SHA-256 produces a 64-character hex digest."""
        result = hash_content("hello")
        assert len(result) == 64

    def test_deterministic(self):
        """Same input always produces same output."""
        assert hash_content("hello") == hash_content("hello")

    def test_different_inputs_different_hashes(self):
        assert hash_content("hello") != hash_content("world")

    def test_empty_string(self):
        """Empty string should produce a valid hash (not raise)."""
        result = hash_content("")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_empty_string_deterministic(self):
        assert hash_content("") == hash_content("")

    def test_whitespace_matters(self):
        """Hashes of strings with different whitespace differ."""
        assert hash_content("hello") != hash_content("hello ")
        assert hash_content("hello") != hash_content(" hello")

    def test_case_sensitive(self):
        assert hash_content("Hello") != hash_content("hello")

    def test_unicode_content(self):
        result = hash_content("Clínica Veterinaria \u00e9\u00e0")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_known_sha256_value(self):
        """Verify against a known SHA-256 value."""
        expected = hashlib.sha256(b"abc").hexdigest()
        assert hash_content("abc") == expected

    def test_large_content(self):
        """Handles large strings without error."""
        large = "x" * 100_000
        result = hash_content(large)
        assert len(result) == 64

    def test_special_characters(self):
        result = hash_content("SELECT * FROM users; DROP TABLE users;--")
        assert isinstance(result, str)
        assert len(result) == 64


class TestHashMessage:
    """Unit tests for hash_message."""

    def test_returns_string(self):
        result = hash_message("sender@bank.com", "Your transaction", "body text")
        assert isinstance(result, str)

    def test_returns_hex_string_64_chars(self):
        result = hash_message("sender@bank.com", "Your transaction", "body text")
        assert len(result) == 64
        int(result, 16)  # raises if not valid hex

    def test_deterministic(self):
        h1 = hash_message("a@b.com", "subj", "body")
        h2 = hash_message("a@b.com", "subj", "body")
        assert h1 == h2

    def test_different_sender_different_hash(self):
        h1 = hash_message("sender1@b.com", "subj", "body")
        h2 = hash_message("sender2@b.com", "subj", "body")
        assert h1 != h2

    def test_different_subject_different_hash(self):
        h1 = hash_message("a@b.com", "subject1", "body")
        h2 = hash_message("a@b.com", "subject2", "body")
        assert h1 != h2

    def test_different_body_different_hash(self):
        h1 = hash_message("a@b.com", "subj", "body1")
        h2 = hash_message("a@b.com", "subj", "body2")
        assert h1 != h2

    def test_empty_fields(self):
        """Empty strings are valid inputs."""
        result = hash_message("", "", "")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_field_separator_prevents_collisions(self):
        """'ab' + 'c' must differ from 'a' + 'bc' to avoid separator collisions."""
        h1 = hash_message("ab", "c", "body")
        h2 = hash_message("a", "bc", "body")
        assert h1 != h2

    def test_unicode_fields(self):
        result = hash_message("banco@bac.cr", "Transacci\u00f3n", "Cuerpo del mensaje")
        assert len(result) == 64
