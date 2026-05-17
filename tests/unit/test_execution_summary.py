from __future__ import annotations

import inspect

import connectlang_rpa.desktop.services.execution_summary as es_module
from connectlang_rpa.desktop.services.execution_summary import ExecutionSummary
from connectlang_rpa.desktop.services.log_streamer import LogStreamer, ParsedLogLine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parsed(**kwargs: object) -> ParsedLogLine:
    defaults: dict[str, object] = {
        "raw": "",
        "event": None,
        "level": None,
        "word": None,
        "message": "",
        "is_json": True,
        "is_error": False,
        "total": None,
        "path": None,
    }
    defaults.update(kwargs)
    return ParsedLogLine(**defaults)  # type: ignore[arg-type]


def _summary_from_events(*events: ParsedLogLine) -> ExecutionSummary:
    s = ExecutionSummary()
    for e in events:
        s.handle_event(e)
    return s


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_summary_initial_state_is_zeroed() -> None:
    s = ExecutionSummary()
    assert s.total == 0
    assert s.successes == 0
    assert s.failures == 0
    assert s.exit_code is None
    assert s.screenshots == []
    assert s.is_finalized is False


# ---------------------------------------------------------------------------
# handle_event
# ---------------------------------------------------------------------------


def test_handle_event_execution_started_sets_total() -> None:
    s = _summary_from_events(_parsed(event="execution_started", total=5))
    assert s.total == 5


def test_handle_event_word_added_successfully_increments_successes() -> None:
    s = _summary_from_events(
        _parsed(event="execution_started", total=2),
        _parsed(event="word_added_successfully", word="Apfel"),
        _parsed(event="word_added_successfully", word="Baum"),
    )
    assert s.successes == 2
    assert s.failures == 0


def test_handle_event_word_failed_increments_failures() -> None:
    s = _summary_from_events(
        _parsed(event="execution_started", total=2),
        _parsed(event="word_failed", word="Hund"),
    )
    assert s.failures == 1
    assert s.successes == 0


def test_handle_event_screenshot_saved_appends_path() -> None:
    s = _summary_from_events(
        _parsed(event="screenshot_saved", path="screenshots/foo.png"),
    )
    assert s.screenshots == ["screenshots/foo.png"]


def test_handle_event_screenshot_saved_without_path_is_ignored() -> None:
    s = _summary_from_events(_parsed(event="screenshot_saved", path=None))
    assert s.screenshots == []


def test_handle_event_unknown_event_does_not_alter_counts() -> None:
    s = _summary_from_events(_parsed(event="some_unknown_event"))
    assert s.total == 0
    assert s.successes == 0
    assert s.failures == 0


# ---------------------------------------------------------------------------
# finalize
# ---------------------------------------------------------------------------


def test_finalize_exit_code_zero_sets_success_status() -> None:
    s = ExecutionSummary()
    s.finalize(0)
    assert s.is_finalized is True
    assert s.exit_code == 0
    assert s.status_text == "SUCESSO"


def test_finalize_nonzero_exit_code_sets_error_status() -> None:
    s = ExecutionSummary()
    s.finalize(1)
    assert s.is_finalized is True
    assert s.status_text == "ERRO"


def test_finalize_nonzero_exit_code_2_sets_error_status() -> None:
    s = ExecutionSummary()
    s.finalize(2)
    assert s.status_text == "ERRO"


# ---------------------------------------------------------------------------
# status_text before finalize
# ---------------------------------------------------------------------------


def test_status_text_idle_when_no_events() -> None:
    s = ExecutionSummary()
    assert s.status_text == "AGUARDANDO"


def test_status_text_running_after_execution_started() -> None:
    s = _summary_from_events(_parsed(event="execution_started", total=3))
    assert s.status_text == "EM EXECUÇÃO"


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


def test_reset_clears_all_fields() -> None:
    s = _summary_from_events(
        _parsed(event="execution_started", total=3),
        _parsed(event="word_added_successfully", word="A"),
        _parsed(event="word_failed", word="B"),
        _parsed(event="screenshot_saved", path="s/foo.png"),
    )
    s.finalize(1)
    s.reset()

    assert s.total == 0
    assert s.successes == 0
    assert s.failures == 0
    assert s.exit_code is None
    assert s.screenshots == []
    assert s.is_finalized is False


def test_reset_allows_clean_second_run() -> None:
    s = ExecutionSummary()
    s.handle_event(_parsed(event="execution_started", total=2))
    s.handle_event(_parsed(event="word_added_successfully", word="A"))
    s.finalize(0)

    s.reset()
    s.handle_event(_parsed(event="execution_started", total=1))
    s.handle_event(_parsed(event="word_failed", word="X"))
    s.finalize(1)

    assert s.total == 1
    assert s.successes == 0
    assert s.failures == 1
    assert s.status_text == "ERRO"


# ---------------------------------------------------------------------------
# to_display_lines
# ---------------------------------------------------------------------------


def test_to_display_lines_empty_before_finalize() -> None:
    s = ExecutionSummary()
    assert s.to_display_lines() == []


def test_to_display_lines_contains_key_fields_after_success() -> None:
    s = _summary_from_events(
        _parsed(event="execution_started", total=3),
        _parsed(event="word_added_successfully", word="A"),
        _parsed(event="word_added_successfully", word="B"),
        _parsed(event="word_failed", word="C"),
    )
    s.finalize(0)
    lines = "\n".join(s.to_display_lines())

    assert "SUCESSO" in lines
    assert "3" in lines
    assert "2" in lines
    assert "1" in lines
    assert "0" in lines  # exit code


def test_to_display_lines_shows_failure_hint_when_failures_exist() -> None:
    s = _summary_from_events(_parsed(event="word_failed", word="X"))
    s.finalize(1)
    combined = "\n".join(s.to_display_lines()).lower()
    assert "logs" in combined or "falhas" in combined or "detalhes" in combined


def test_to_display_lines_shows_screenshot_path() -> None:
    s = _summary_from_events(_parsed(event="screenshot_saved", path="screenshots/err.png"))
    s.finalize(1)
    combined = "\n".join(s.to_display_lines())
    assert "screenshots/err.png" in combined


def test_to_display_lines_no_screenshot_section_when_none() -> None:
    s = ExecutionSummary()
    s.finalize(0)
    combined = "\n".join(s.to_display_lines())
    assert "screenshots" not in combined.lower()


# ---------------------------------------------------------------------------
# Integration: LogStreamer → ExecutionSummary via on_event
# ---------------------------------------------------------------------------


def _streamer_with_summary(summary: ExecutionSummary) -> LogStreamer:
    lines: list[str] = []
    return LogStreamer(
        on_line=lines.append,
        on_event=summary.handle_event,
    )


def test_log_streamer_on_event_feeds_execution_started() -> None:
    import json

    summary = ExecutionSummary()
    streamer = _streamer_with_summary(summary)
    line = json.dumps({"event": "execution_started", "total": 4, "level": "info"})
    streamer.process_line(line)

    assert summary.total == 4


def test_log_streamer_on_event_feeds_word_results() -> None:
    import json

    summary = ExecutionSummary()
    streamer = _streamer_with_summary(summary)
    streamer.process_line(json.dumps({"event": "execution_started", "total": 2, "level": "info"}))
    line_ok = json.dumps({"event": "word_added_successfully", "word": "A", "level": "info"})
    line_fail = json.dumps({"event": "word_failed", "word": "B", "level": "error"})
    streamer.process_line(line_ok)
    streamer.process_line(line_fail)

    assert summary.successes == 1
    assert summary.failures == 1


def test_log_streamer_on_event_feeds_screenshot() -> None:
    import json

    summary = ExecutionSummary()
    streamer = _streamer_with_summary(summary)
    line = json.dumps({"event": "screenshot_saved", "path": "s/x.png", "level": "info"})
    streamer.process_line(line)

    assert "s/x.png" in summary.screenshots


# ---------------------------------------------------------------------------
# No Playwright dependency
# ---------------------------------------------------------------------------


def test_execution_summary_does_not_import_playwright() -> None:
    source = inspect.getsource(es_module)
    assert "playwright" not in source
