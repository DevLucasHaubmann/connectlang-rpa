from __future__ import annotations

import inspect
import json

import connectlang_rpa.desktop.services.log_streamer as ls_module
from connectlang_rpa.desktop.services.log_streamer import LogStreamer, ParsedLogLine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _streamer(
    lines: list[str] | None = None,
    words: list[str] | None = None,
    progress: list[tuple[int, int]] | None = None,
) -> LogStreamer:
    return LogStreamer(
        on_line=lambda line: lines.append(line) if lines is not None else None,
        on_word_update=lambda w: words.append(w) if words is not None else None,
        on_progress=lambda c, t: progress.append((c, t)) if progress is not None else None,
    )


def _json_line(**kwargs: object) -> str:
    return json.dumps(kwargs)


# ---------------------------------------------------------------------------
# parse_line — JSON paths
# ---------------------------------------------------------------------------


def test_parse_line_valid_json_with_event() -> None:
    raw = _json_line(event="execution_started", level="info", total=3)
    parsed = LogStreamer(on_line=lambda _: None).parse_line(raw)

    assert parsed.is_json is True
    assert parsed.event == "execution_started"
    assert parsed.level == "info"
    assert parsed.total == 3
    assert parsed.is_error is False


def test_parse_line_json_with_word() -> None:
    raw = _json_line(event="word_processing_started", level="info", word="Apfel")
    parsed = LogStreamer(on_line=lambda _: None).parse_line(raw)

    assert parsed.word == "Apfel"
    assert parsed.event == "word_processing_started"


def test_parse_line_json_without_event() -> None:
    raw = _json_line(level="info", message="some message")
    parsed = LogStreamer(on_line=lambda _: None).parse_line(raw)

    assert parsed.is_json is True
    assert parsed.event is None
    assert "some message" in parsed.message


def test_parse_line_detects_error_level() -> None:
    raw = _json_line(event="word_failed", level="error", word="Baum")
    parsed = LogStreamer(on_line=lambda _: None).parse_line(raw)

    assert parsed.is_error is True
    assert parsed.level == "error"


# ---------------------------------------------------------------------------
# parse_line — raw fallback paths
# ---------------------------------------------------------------------------


def test_parse_line_fallback_for_plain_text() -> None:
    raw = "some plain text output"
    parsed = LogStreamer(on_line=lambda _: None).parse_line(raw)

    assert parsed.is_json is False
    assert parsed.raw == raw
    assert parsed.event is None


def test_parse_line_fallback_for_invalid_json() -> None:
    raw = "{not valid json"
    parsed = LogStreamer(on_line=lambda _: None).parse_line(raw)

    assert parsed.is_json is False


def test_parse_line_detects_error_in_raw_line() -> None:
    raw = "[ERROR] something went wrong"
    parsed = LogStreamer(on_line=lambda _: None).parse_line(raw)

    assert parsed.is_json is False
    assert parsed.is_error is True


def test_parse_line_empty_string_does_not_crash() -> None:
    parsed = LogStreamer(on_line=lambda _: None).parse_line("")
    assert isinstance(parsed, ParsedLogLine)


# ---------------------------------------------------------------------------
# format_line
# ---------------------------------------------------------------------------


def test_format_word_processing_started() -> None:
    streamer = LogStreamer(on_line=lambda _: None)
    raw = _json_line(event="word_processing_started", level="info", word="Hund")
    parsed = streamer.parse_line(raw)

    assert streamer.format_line(parsed) == "→ Processando: Hund"


def test_format_word_added_successfully() -> None:
    streamer = LogStreamer(on_line=lambda _: None)
    raw = _json_line(event="word_added_successfully", level="info", word="Katze")
    parsed = streamer.parse_line(raw)

    assert streamer.format_line(parsed) == "[OK] Adicionada com sucesso: Katze"


def test_format_word_failed() -> None:
    streamer = LogStreamer(on_line=lambda _: None)
    raw = _json_line(event="word_failed", level="error", word="Maus")
    parsed = streamer.parse_line(raw)

    assert "Falha ao processar: Maus" in streamer.format_line(parsed)


def test_format_screenshot_saved_with_path() -> None:
    streamer = LogStreamer(on_line=lambda _: None)
    raw = _json_line(event="screenshot_saved", level="info", path="screenshots/foo.png")
    parsed = streamer.parse_line(raw)

    assert "screenshots/foo.png" in streamer.format_line(parsed)


def test_format_raw_error_line_has_error_prefix() -> None:
    streamer = LogStreamer(on_line=lambda _: None)
    parsed = streamer.parse_line("[ERROR] boom")

    result = streamer.format_line(parsed)
    assert result.startswith("[ERROR]")


# ---------------------------------------------------------------------------
# process_line — side effects
# ---------------------------------------------------------------------------


def test_process_line_word_update_callback_fires_on_word_processing_started() -> None:
    words: list[str] = []
    streamer = _streamer(words=words)
    streamer.process_line(_json_line(event="word_processing_started", level="info", word="Vogel"))

    assert words == ["Vogel"]


def test_process_line_progress_callback_fires_after_word_result() -> None:
    progress: list[tuple[int, int]] = []
    streamer = _streamer(progress=progress)
    streamer.process_line(_json_line(event="execution_started", level="info", total=2))
    streamer.process_line(_json_line(event="word_added_successfully", level="info", word="A"))
    streamer.process_line(_json_line(event="word_failed", level="error", word="B"))

    assert progress == [(1, 2), (2, 2)]


def test_process_line_empty_line_is_ignored() -> None:
    lines: list[str] = []
    streamer = _streamer(lines=lines)
    streamer.process_line("")
    streamer.process_line("   ")

    assert lines == []


def test_process_line_no_progress_without_total() -> None:
    progress: list[tuple[int, int]] = []
    streamer = _streamer(progress=progress)
    streamer.process_line(_json_line(event="word_added_successfully", level="info", word="A"))

    assert progress == []


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------


def test_reset_clears_progress_state() -> None:
    progress: list[tuple[int, int]] = []
    streamer = _streamer(progress=progress)
    streamer.process_line(_json_line(event="execution_started", level="info", total=3))
    streamer.process_line(_json_line(event="word_added_successfully", level="info", word="A"))
    assert progress == [(1, 3)]

    streamer.reset()
    streamer.process_line(_json_line(event="execution_started", level="info", total=2))
    streamer.process_line(_json_line(event="word_added_successfully", level="info", word="B"))
    assert progress[-1] == (1, 2)


# ---------------------------------------------------------------------------
# No Playwright dependency
# ---------------------------------------------------------------------------


def test_log_streamer_does_not_import_playwright() -> None:
    source = inspect.getsource(ls_module)
    assert "playwright" not in source, "log_streamer must not import Playwright."
