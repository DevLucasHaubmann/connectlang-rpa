from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import structlog
from playwright.sync_api import Page

from connectlang_rpa.config.settings import get_settings
from connectlang_rpa.core.browser import BrowserManager
from connectlang_rpa.exceptions import SessionExpiredError
from connectlang_rpa.models.word_entry import WordEntry
from connectlang_rpa.services.vocabulary_service import VocabularyService
from connectlang_rpa.services.word_loader import load_word_entries
from connectlang_rpa.utils.logger import configure_logging
from connectlang_rpa.utils.screenshots import capture_failure_screenshot

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class WordResult:
    word: str
    success: bool
    error: str | None = None
    screenshot_path: Path | None = None


@dataclass(frozen=True)
class ExecutionSummary:
    total: int
    successes: int
    failures: int
    elapsed_seconds: float
    failed_results: list[WordResult] = field(default_factory=list)


def _process_word(service: VocabularyService, entry: WordEntry, page: Page) -> WordResult:
    log.info("word_processing_started", word=entry.text)
    try:
        service.add_word(entry)
        log.info("word_added_successfully", word=entry.text)
        return WordResult(word=entry.text, success=True)
    except Exception as exc:
        screenshot = capture_failure_screenshot(page, entry.text)
        log.error(
            "word_failed",
            word=entry.text,
            error=str(exc),
            screenshot_path=str(screenshot) if screenshot else None,
            exc_info=True,
        )
        return WordResult(
            word=entry.text, success=False, error=str(exc), screenshot_path=screenshot
        )


def _build_summary(results: list[WordResult], elapsed: float) -> ExecutionSummary:
    successes = 0
    failed: list[WordResult] = []
    for r in results:
        if r.success:
            successes += 1
        else:
            failed.append(r)
    return ExecutionSummary(
        total=len(results),
        successes=successes,
        failures=len(failed),
        elapsed_seconds=elapsed,
        failed_results=failed,
    )


def _print_execution_report(summary: ExecutionSummary) -> None:
    print("\nExecution completed")
    print(f"Total:    {summary.total}")
    print(f"Successes: {summary.successes}")
    print(f"Failures: {summary.failures}")
    print(f"Elapsed:  {summary.elapsed_seconds:.2f}s")

    if summary.failed_results:
        print("\nFailures:")
        for r in summary.failed_results:
            screenshot_info = f" [screenshot: {r.screenshot_path}]" if r.screenshot_path else ""
            print(f"  - {r.word}: {r.error}{screenshot_info}")


def run() -> list[WordResult]:
    settings = get_settings()

    try:
        entries = load_word_entries(settings.words_file)
    except (FileNotFoundError, ValueError) as exc:
        log.error("startup_failed", reason=str(exc))
        sys.exit(f"[ERROR] Could not load word list: {exc}")

    log.info("execution_started", total=len(entries))

    results: list[WordResult] = []

    with BrowserManager(settings) as browser:
        service = VocabularyService(browser.page, settings)
        try:
            service.ensure_session_active()
        except SessionExpiredError as exc:
            log.error("session_expired", reason=str(exc))
            sys.exit(f"[ERROR] Session expired or not authenticated: {exc}")
        for entry in entries:
            result = _process_word(service, entry, browser.page)
            results.append(result)

    return results


def main() -> None:
    configure_logging()
    start = time.perf_counter()
    results = run()
    elapsed = time.perf_counter() - start
    summary = _build_summary(results, elapsed)
    log.info(
        "execution_finished",
        total=summary.total,
        successes=summary.successes,
        failures=summary.failures,
        elapsed_seconds=round(summary.elapsed_seconds, 2),
    )
    _print_execution_report(summary)


if __name__ == "__main__":
    main()
