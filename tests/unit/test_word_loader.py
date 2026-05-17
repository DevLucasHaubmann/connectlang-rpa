from __future__ import annotations

import json
from pathlib import Path

import pytest

from connectlang_rpa.models.word_entry import WordEntry
from connectlang_rpa.services.word_loader import load_word_entries


def _write_json(tmp_path: Path, data: object) -> Path:
    file = tmp_path / "words.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    return file


def test_loads_valid_entries(tmp_path: Path) -> None:
    path = _write_json(
        tmp_path,
        [
            {"text": "der Termin", "entry_type": "word"},
            {"text": "Ich lerne Deutsch.", "entry_type": "sentence"},
        ],
    )
    entries = load_word_entries(path)
    assert entries == [
        WordEntry(text="der Termin", entry_type="word"),
        WordEntry(text="Ich lerne Deutsch.", entry_type="sentence"),
    ]


def test_applies_default_entry_type(tmp_path: Path) -> None:
    path = _write_json(tmp_path, [{"text": "die Zusammenarbeit"}])
    entries = load_word_entries(path)
    assert entries[0].entry_type == "word"


def test_returns_list_of_word_entry(tmp_path: Path) -> None:
    path = _write_json(tmp_path, [{"text": "hello"}])
    entries = load_word_entries(path)
    assert isinstance(entries, list)
    assert all(isinstance(e, WordEntry) for e in entries)


def test_rejects_missing_file() -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        load_word_entries(Path("/nonexistent/words.json"))


def test_rejects_invalid_json(tmp_path: Path) -> None:
    file = tmp_path / "words.json"
    file.write_text("not json {{{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_word_entries(file)


def test_rejects_root_not_list(tmp_path: Path) -> None:
    path = _write_json(tmp_path, {"text": "hello"})
    with pytest.raises(ValueError, match="JSON array"):
        load_word_entries(path)


def test_rejects_item_not_object(tmp_path: Path) -> None:
    path = _write_json(tmp_path, ["just a string"])
    with pytest.raises(ValueError, match="index 0"):
        load_word_entries(path)


def test_rejects_item_missing_text(tmp_path: Path) -> None:
    path = _write_json(tmp_path, [{"entry_type": "word"}])
    with pytest.raises(ValueError, match="index 0"):
        load_word_entries(path)


def test_rejects_empty_text(tmp_path: Path) -> None:
    path = _write_json(tmp_path, [{"text": "   "}])
    with pytest.raises(ValueError, match="index 0"):
        load_word_entries(path)


def test_rejects_invalid_entry_type(tmp_path: Path) -> None:
    path = _write_json(tmp_path, [{"text": "hello", "entry_type": "phrase"}])
    with pytest.raises(ValueError, match="index 0"):
        load_word_entries(path)
