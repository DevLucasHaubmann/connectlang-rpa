from __future__ import annotations

import json
from pathlib import Path

from connectlang_rpa.models.word_entry import WordEntry


def load_word_entries(path: Path) -> list[WordEntry]:
    raw = _read_json_list(path)
    return [_parse_entry(item, index) for index, item in enumerate(raw)]


def _read_json_list(path: Path) -> list[object]:
    if not path.exists():
        raise FileNotFoundError(f"Word list file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array at root in {path}, got {type(data).__name__}")
    return data


def _parse_entry(item: object, index: int) -> WordEntry:
    if not isinstance(item, dict):
        raise ValueError(f"Item at index {index} must be an object, got {type(item).__name__}")
    if "text" not in item:
        raise ValueError(f"Item at index {index} is missing required field 'text'")
    try:
        return WordEntry(**{k: v for k, v in item.items() if k in ("text", "entry_type")})
    except ValueError as exc:
        raise ValueError(f"Item at index {index} is invalid: {exc}") from exc
