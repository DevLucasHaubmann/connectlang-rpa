from __future__ import annotations

import json
from pathlib import Path
from typing import Final

WORDS_FILE: Final[Path] = Path("data/words.json")


class EmptyWordListError(ValueError):
    pass


def parse_lines(raw_text: str) -> list[str]:
    """Normalise raw textarea input into a deduplicated list of non-empty lines."""
    seen: set[str] = set()
    result: list[str] = []
    for line in raw_text.splitlines():
        word = line.strip()
        if not word or word in seen:
            continue
        seen.add(word)
        result.append(word)
    return result


def build_payload(words: list[str]) -> list[dict[str, str]]:
    return [{"text": w, "entry_type": "word"} for w in words]


def save_words(words: list[str], path: Path = WORDS_FILE) -> None:
    if not words:
        raise EmptyWordListError("A lista de palavras está vazia.")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload(words)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_words(path: Path = WORDS_FILE) -> list[str]:
    """Return saved words or empty list if file is missing / invalid."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [entry["text"] for entry in data if isinstance(entry, dict) and "text" in entry]
    except (json.JSONDecodeError, KeyError):
        return []
