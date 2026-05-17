from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedLogLine:
    raw: str
    event: str | None
    level: str | None
    word: str | None
    message: str
    is_json: bool
    is_error: bool
    total: int | None = None
    path: str | None = None


def _parse_json(raw: str) -> ParsedLogLine:
    data: dict[str, object] = json.loads(raw)
    event = data.get("event")
    event_str = str(event) if event is not None else None
    level = data.get("level")
    level_str = str(level) if level is not None else None
    word = data.get("word")
    word_str = str(word) if word is not None else None
    path = data.get("screenshot_path") or data.get("path")
    path_str = str(path) if path is not None else None
    total = data.get("total")
    total_int = int(total) if isinstance(total, (int, float)) else None
    message = event_str or str(data.get("message", raw))
    is_error = level_str == "error"
    return ParsedLogLine(
        raw=raw,
        event=event_str,
        level=level_str,
        word=word_str,
        message=message,
        is_json=True,
        is_error=is_error,
        total=total_int,
        path=path_str,
    )


def _parse_raw(raw: str) -> ParsedLogLine:
    stripped = raw.strip()
    is_error = stripped.upper().startswith("ERROR") or "[ERROR]" in stripped.upper()
    return ParsedLogLine(
        raw=raw,
        event=None,
        level="error" if is_error else None,
        word=None,
        message=stripped or raw,
        is_json=False,
        is_error=is_error,
    )


_EVENT_FORMATS: dict[str, str] = {
    "execution_started": "Execução iniciada",
    "execution_finished": "Execução finalizada",
    "session_expired": "Sessão expirada",
    "startup_failed": "Falha na inicialização",
}


def _format_json_line(parsed: ParsedLogLine) -> str:
    event = parsed.event
    word = parsed.word

    if event == "word_processing_started":
        return f"→ Processando: {word}" if word else "→ Processando palavra..."
    if event == "word_added_successfully":
        return f"[OK] Adicionada com sucesso: {word}" if word else "[OK] Palavra adicionada."
    if event == "word_failed":
        return f"[ERRO] Falha ao processar: {word}" if word else "[ERRO] Falha ao processar."
    if event == "screenshot_saved":
        if parsed.path:
            return f"[INFO] Screenshot salvo: {parsed.path}"
        return "[INFO] Screenshot salvo."
    if event in _EVENT_FORMATS:
        return _EVENT_FORMATS[event]

    # Unknown JSON event: show event name + message if distinct
    if event and event != parsed.message:
        return f"[{event}] {parsed.message}"
    return parsed.message


@dataclass
class _RunState:
    total: int = 0
    processed: int = 0

    def reset(self) -> None:
        self.total = 0
        self.processed = 0


class LogStreamer:
    """Parses JSONL lines from the bot process and dispatches formatted messages to the UI.

    All callbacks are invoked synchronously from the caller's thread.
    The UI layer is responsible for marshaling to the main thread.
    """

    def __init__(
        self,
        on_line: Callable[[str], None],
        on_word_update: Callable[[str], None] | None = None,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> None:
        self._on_line = on_line
        self._on_word_update = on_word_update
        self._on_progress = on_progress
        self._state = _RunState()

    def reset(self) -> None:
        self._state.reset()

    def process_line(self, raw: str) -> None:
        if not raw.strip():
            return
        parsed = self.parse_line(raw)
        self._dispatch_side_effects(parsed)
        self._on_line(self.format_line(parsed))

    def parse_line(self, raw: str) -> ParsedLogLine:
        try:
            return _parse_json(raw)
        except (json.JSONDecodeError, ValueError, KeyError):
            return _parse_raw(raw)

    def format_line(self, parsed: ParsedLogLine) -> str:
        if not parsed.is_json:
            prefix = "[ERROR] " if parsed.is_error else ""
            return f"{prefix}{parsed.message}"
        return _format_json_line(parsed)

    def _dispatch_side_effects(self, parsed: ParsedLogLine) -> None:
        event = parsed.event

        if event == "execution_started":
            if parsed.total is not None:
                self._state.total = parsed.total

        elif event == "word_processing_started":
            if parsed.word and self._on_word_update:
                self._on_word_update(parsed.word)

        elif event in ("word_added_successfully", "word_failed"):
            self._state.processed += 1
            if self._on_progress and self._state.total > 0:
                self._on_progress(self._state.processed, self._state.total)
