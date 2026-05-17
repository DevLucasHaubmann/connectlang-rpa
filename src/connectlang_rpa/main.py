from __future__ import annotations

import sys
from dataclasses import dataclass

import structlog

from connectlang_rpa.config.settings import get_settings
from connectlang_rpa.core.browser import BrowserManager
from connectlang_rpa.models.word_entry import WordEntry
from connectlang_rpa.services.vocabulary_service import VocabularyService
from connectlang_rpa.services.word_loader import load_word_entries

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class WordResult:
    word: str
    success: bool
    error: str | None = None


def _process_word(service: VocabularyService, entry: WordEntry) -> WordResult:
    try:
        service.add_word(entry)
        log.info("word_processed", word=entry.text, status="success")
        return WordResult(word=entry.text, success=True)
    except Exception as exc:
        log.error("word_failed", word=entry.text, error=str(exc), exc_info=True)
        return WordResult(word=entry.text, success=False, error=str(exc))


def _print_summary(results: list[WordResult]) -> None:
    total = len(results)
    successes = sum(1 for r in results if r.success)
    failures = total - successes

    print("\n--- Run Summary ---")
    print(f"Total:    {total}")
    print(f"Success:  {successes}")
    print(f"Failures: {failures}")

    if failures:
        print("\nFailed words:")
        for r in results:
            if not r.success:
                print(f"  - {r.word}: {r.error}")


def run() -> list[WordResult]:
    settings = get_settings()

    try:
        entries = load_word_entries(settings.words_file)
    except (FileNotFoundError, ValueError) as exc:
        log.error("startup_failed", reason=str(exc))
        sys.exit(f"[ERROR] Could not load word list: {exc}")

    log.info("batch_started", total=len(entries))

    results: list[WordResult] = []

    with BrowserManager(settings) as browser:
        service = VocabularyService(browser.page, settings)
        for entry in entries:
            result = _process_word(service, entry)
            results.append(result)

    return results


def main() -> None:
    results = run()
    _print_summary(results)


if __name__ == "__main__":
    main()
