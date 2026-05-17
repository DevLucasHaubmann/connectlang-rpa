from __future__ import annotations

import json
from pathlib import Path

import pytest

from connectlang_rpa.desktop.services.desktop_word_service import (
    EmptyWordListError,
    build_payload,
    load_words,
    parse_lines,
    save_words,
)


class TestParseLines:
    def test_basic_words_are_returned(self) -> None:
        result = parse_lines("der Fahrplan\ndie Haltestelle")
        assert result == ["der Fahrplan", "die Haltestelle"]

    def test_empty_lines_are_removed(self) -> None:
        result = parse_lines("der Fahrplan\n\ndie Haltestelle\n")
        assert result == ["der Fahrplan", "die Haltestelle"]

    def test_duplicates_are_removed(self) -> None:
        result = parse_lines("der Fahrplan\nder Fahrplan\ndie Haltestelle")
        assert result == ["der Fahrplan", "die Haltestelle"]

    def test_whitespace_only_lines_are_removed(self) -> None:
        result = parse_lines("der Fahrplan\n   \ndie Haltestelle")
        assert result == ["der Fahrplan", "die Haltestelle"]

    def test_strips_leading_trailing_whitespace_per_line(self) -> None:
        result = parse_lines("  der Fahrplan  \n  die Haltestelle  ")
        assert result == ["der Fahrplan", "die Haltestelle"]

    def test_empty_input_returns_empty_list(self) -> None:
        assert parse_lines("") == []
        assert parse_lines("   \n\n   ") == []

    def test_phrases_are_preserved(self) -> None:
        result = parse_lines("Ich lerne Deutsch.\nDas ist schön.")
        assert result == ["Ich lerne Deutsch.", "Das ist schön."]

    def test_order_is_preserved_with_dedup(self) -> None:
        result = parse_lines("c\nb\na\nb\nc")
        assert result == ["c", "b", "a"]


class TestBuildPayload:
    def test_generates_correct_json_format(self) -> None:
        result = build_payload(["der Fahrplan", "die Haltestelle"])
        assert result == [
            {"text": "der Fahrplan", "entry_type": "word"},
            {"text": "die Haltestelle", "entry_type": "word"},
        ]

    def test_empty_list_generates_empty_payload(self) -> None:
        assert build_payload([]) == []


class TestSaveWords:
    def test_saves_valid_words_to_file(self, tmp_path: Path) -> None:
        dest = tmp_path / "words.json"
        save_words(["der Fahrplan", "die Haltestelle"], dest)
        data = json.loads(dest.read_text(encoding="utf-8"))
        assert data == [
            {"text": "der Fahrplan", "entry_type": "word"},
            {"text": "die Haltestelle", "entry_type": "word"},
        ]

    def test_raises_on_empty_list(self, tmp_path: Path) -> None:
        dest = tmp_path / "words.json"
        with pytest.raises(EmptyWordListError):
            save_words([], dest)

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        dest = tmp_path / "nested" / "dir" / "words.json"
        save_words(["das Wort"], dest)
        assert dest.exists()

    def test_file_is_utf8_encoded(self, tmp_path: Path) -> None:
        dest = tmp_path / "words.json"
        save_words(["Straße", "Müller"], dest)
        raw = dest.read_bytes()
        decoded = raw.decode("utf-8")
        assert "Straße" in decoded
        assert "Müller" in decoded


class TestLoadWords:
    def test_loads_existing_file(self, tmp_path: Path) -> None:
        dest = tmp_path / "words.json"
        dest.write_text(
            json.dumps([{"text": "das Wort", "entry_type": "word"}]),
            encoding="utf-8",
        )
        assert load_words(dest) == ["das Wort"]

    def test_returns_empty_list_when_file_missing(self, tmp_path: Path) -> None:
        assert load_words(tmp_path / "nonexistent.json") == []

    def test_returns_empty_list_on_invalid_json(self, tmp_path: Path) -> None:
        dest = tmp_path / "words.json"
        dest.write_text("not valid json", encoding="utf-8")
        assert load_words(dest) == []

    def test_skips_entries_without_text_key(self, tmp_path: Path) -> None:
        dest = tmp_path / "words.json"
        dest.write_text(
            json.dumps([{"entry_type": "word"}, {"text": "das Wort", "entry_type": "word"}]),
            encoding="utf-8",
        )
        assert load_words(dest) == ["das Wort"]
