from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class WordEntry:
    text: str
    entry_type: Literal["word", "sentence"] = field(default="word")

    def __post_init__(self) -> None:
        stripped = self.text.strip()
        if not stripped:
            raise ValueError("text must not be empty or whitespace")
        object.__setattr__(self, "text", stripped)
        if self.entry_type not in ("word", "sentence"):
            raise ValueError("entry_type must be 'word' or 'sentence'")
