import pytest

from connectlang_rpa.models import WordEntry


def test_word_entry_valid_word() -> None:
    entry = WordEntry(text="hello")
    assert entry.text == "hello"
    assert entry.entry_type == "word"


def test_word_entry_valid_sentence() -> None:
    entry = WordEntry(text="how are you", entry_type="sentence")
    assert entry.entry_type == "sentence"


def test_word_entry_strips_whitespace() -> None:
    entry = WordEntry(text="  hello  ")
    assert entry.text == "hello"


def test_word_entry_rejects_empty_text() -> None:
    with pytest.raises(ValueError, match="empty"):
        WordEntry(text="")


def test_word_entry_rejects_whitespace_only_text() -> None:
    with pytest.raises(ValueError, match="empty"):
        WordEntry(text="   ")


def test_word_entry_rejects_invalid_entry_type() -> None:
    with pytest.raises((ValueError, TypeError)):
        WordEntry(text="hello", entry_type="phrase")  # type: ignore[arg-type]


def test_word_entry_is_frozen() -> None:
    entry = WordEntry(text="hello")
    with pytest.raises((AttributeError, TypeError)):
        entry.text = "world"  # type: ignore[misc]
