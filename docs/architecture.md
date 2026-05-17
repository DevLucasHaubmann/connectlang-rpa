# Architecture

## Overview

ConnectLang RPA Bot is a single-workflow automation bot built in layers. Each layer has one
responsibility: configuration, browser lifecycle, business flow, page locators, reusable
browser actions, utilities, and data models. Layers communicate downward; none of them reach
back up.

This is a focused MVP, not a generic RPA framework. It automates one flow on one platform
and is intentionally scoped to that.

---

## Architectural goals

- Keep the codebase small and auditable — every file has an obvious role.
- Decouple the business flow from raw browser interaction details.
- Isolate failures per word so a single bad entry does not abort the batch.
- Centralize locators so a UI change requires editing one file.
- Record every outcome in a structured, machine-readable log.
- Avoid automating login, captcha, or any authentication bypass.
- Keep tests on pure logic — no browser required to run the test suite.

---

## High-level flow

```
main() → configure_logging()
       → load_word_entries()        # validates all entries before touching the browser
       → BrowserManager.__enter__() # opens persistent context
       → VocabularyService.ensure_session_active()  # aborts if not logged in
       → for each WordEntry:
             VocabularyService.add_word()            # executes the full add-word flow
             capture_failure_screenshot() if failed  # diagnostic artifact on error
       → BrowserManager.__exit__()  # closes context
       → _print_execution_report()  # terminal summary + log file path
```

Word loading and session validation happen before the batch loop. A configuration error or
expired session exits immediately with a clear message rather than failing mid-run.

---

## Layer responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | Orchestrator. Wires all dependencies, drives the batch loop, builds the execution summary. |
| `config/settings.py` | Typed configuration via `pydantic-settings`. All settings come from environment variables. Validation fails at startup, not mid-run. |
| `core/browser.py` | `BrowserManager` context manager. Opens and closes the persistent Playwright context. |
| `core/profile.py` | Validates that the browser profile directory exists and is writable before the browser starts. |
| `services/vocabulary_service.py` | `VocabularyService`. Orchestrates the add-word flow for a single entry. The only module that knows the steps of the vocabulary workflow. |
| `services/word_loader.py` | Loads and validates the word list from JSON. Returns typed `WordEntry` objects. |
| `locators/vocabulary_locators.py` | All page locators in one place. Returns `Locator` objects; does not perform any actions. |
| `actions/browser_actions.py` | Low-level, reusable browser interactions (`safe_click`, `safe_fill`, `safe_select_combobox`, `wait_until_has_value`, `wait_until_visible`). Raises `BrowserActionError` on failure. |
| `utils/retry.py` | `transient_retry` decorator built on Tenacity. Applied to methods that raise `BrowserActionError`. |
| `utils/logger.py` | Configures `structlog` with JSON output. Builds the per-run `.jsonl` log file path. |
| `utils/screenshots.py` | Captures and names failure screenshots. Never raises; a screenshot failure must not hide the original error. |
| `models/word_entry.py` | `WordEntry` dataclass. Pure data — no methods, no browser references. |
| `exceptions.py` | Domain exceptions: `SessionExpiredError` and any other errors that carry RPA-specific meaning. |

---

## Service Layer

`VocabularyService` owns the vocabulary workflow. Each public method corresponds to one
observable step: navigate, open form, fill entry, select languages, trigger AI fill, wait
for AI, submit.

`add_word()` sequences those steps. `main.py` calls `add_word()` per entry and does not
need to know how the form works.

`browser_actions.py` sits below the service and handles the mechanical part: wait for an
element, act on it, raise `BrowserActionError` if it fails. Services stay readable; retry
logic is applied once at the action boundary, not scattered across flow code.

`VocabularyLocators` sits between the service and the DOM. The service asks for a locator
by name (e.g., `self._locators.new_word_button`); the locator file decides the selector
strategy. The service never contains a raw selector string.

---

## Why not classic Page Object Model

A classic POM wraps each page in a class that exposes high-level methods and owns both
locators and actions. For a single-page, single-flow bot this creates more abstraction than
the problem requires.

The chosen structure separates concerns more granularly:

- `VocabularyLocators` — what to find on the page.
- `browser_actions.py` — how to interact with any element safely.
- `VocabularyService` — when and in what order to do each step.

This is lighter than POM for one workflow. If the project grows to cover multiple distinct
pages or flows, consolidating locators and actions into page objects would be worth
reconsidering.

---

## Semantic locators

Locators follow this priority order:

1. `get_by_role()` with accessible name — tied to semantics, not layout.
2. `get_by_label()` — stable as long as the label text is stable.
3. `get_by_placeholder()` — useful for unlabeled inputs.
4. `get_by_text()` — for visible text that identifies an element uniquely.
5. `locator("css=...")` with a stable, semantic attribute (`id`, `name`, `data-testid`) — used
   as a fallback when none of the above work, always documented with a comment.

Prohibited: absolute XPath, layout utility classes (`.mt-4`, `.flex`), index-based selectors
without a stable anchor.

Semantic locators are more resilient to DOM refactors that do not change visible text or
ARIA roles. They are still fragile to copy changes (e.g., a button renamed from
"Neues Wort" to "Neuen Eintrag erstellen") or structural rewrites. See
[Technical limitations](#technical-limitations).

---

## Persistent session strategy

The bot uses `launch_persistent_context()` with a local `browser-profile/` directory. This
tells Chromium to store cookies, local storage, and session data on disk across runs.

**Login is manual.** On the first run the browser opens and the user logs in. Subsequent
runs reuse the saved session. The bot does not implement Google OAuth, password submission,
or any authentication bypass — both by design and because ConnectLang uses Google login,
which cannot be automated without violating the platform's terms and Google's policies.

**Profile preflight.** Before opening the browser, `core/profile.py` checks that the profile
directory exists and is writable. A missing or corrupted profile is caught before Playwright
starts, not mid-run.

**Session expiry.** If the saved session has expired, ConnectLang redirects to a login URL.
`ensure_session_active()` detects this redirect and raises `SessionExpiredError`, which
causes `main.py` to exit with a clear message before the batch loop begins. The user logs
in manually and runs again.

`browser-profile/` is gitignored. It contains live session cookies and must never be
committed.

---

## Error handling strategy

Errors are categorized by scope and handled at the appropriate level:

| Error type | Where raised | How handled |
|---|---|---|
| Configuration error | `settings.py` on import | `pydantic-settings` raises before the browser opens. `main.py` exits. |
| Profile not ready | `core/profile.py` | Raised before `sync_playwright()` starts. `main.py` exits. |
| Session expired | `VocabularyService.ensure_session_active()` | `SessionExpiredError` propagates to `main.py`, which exits before the loop. |
| Transient browser error | `browser_actions.py` → `BrowserActionError` | Retried up to 3 times with exponential backoff by `transient_retry`. |
| Per-word failure (after retries exhausted) | `_process_word()` in `main.py` | Logged, screenshot captured, result marked as failure. Loop continues to the next entry. |
| Screenshot failure | `utils/screenshots.py` | Caught internally; never re-raised. The original error remains the reported cause. |

**Submit is not retried blindly.** `submit_word()` does not carry `@transient_retry`. A
failed submit is ambiguous: the entry may have been saved before the success message
appeared, or it may not. A blind retry risks a duplicate entry. The failure is logged and
the word is reported as failed; the operator decides whether to re-run it manually.

---

## Logging and observability

Structured logging is provided by `structlog` with JSON rendering.

Key events logged:

- `execution_started` — total number of entries loaded.
- `word_processing_started` — word text, before any browser action.
- `word_added_successfully` — word text, after successful submit.
- `word_failed` — word text, error type, error message, screenshot path.
- `retry_attempt` — attempt number, max attempts, error message.
- `session_expired` — reason string.
- `execution_finished` — totals, elapsed time.

Each run writes to a dedicated `.jsonl` file under `logs/` with a UTC timestamp in the
filename (e.g., `logs/run_2026-05-17_14-30-00.jsonl`). If a file with the same timestamp
already exists (two runs in the same second), a numeric suffix is appended. The file is
opened with mode `"x"` (exclusive create) to prevent overwriting.

The terminal also receives the same JSON stream, plus a human-readable summary table at
the end of the run.

Failure screenshots are saved under `screenshots/` with the format
`error_YYYY-MM-DD_HH-MM-SS_<sanitized-word>.png`.

Neither logs nor screenshots are committed. Both directories contain only a `.gitkeep`
file. Logs and screenshots may capture visible page content (text, form state) and should
be treated as sensitive local artifacts.

Credentials, cookies, and session tokens are never logged.

---

## Testing strategy

Tests cover pure logic only:

- `models/word_entry.py` — field validation and defaults.
- `config/settings.py` — valid settings, missing required fields.
- `services/word_loader.py` — valid file, empty file, malformed entries, encoding edge cases.
- `utils/` — helpers where logic is non-trivial.

No test opens a real browser. Playwright interactions are validated manually against a live
session (see `tests/manual/` for documented procedures).

The test suite is gated by:

```
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest
```

mypy runs in strict mode. All public signatures are fully annotated.

---

## Technical limitations

These are known, accepted limitations of the current MVP:

- **UI dependency.** The bot drives a real browser. It has no access to a ConnectLang API.
  Any change to button labels, form structure, language option values, or page flow may
  break locators or service logic.
- **Locator fragility.** Even semantic locators depend on visible text and ARIA roles. A
  copy change (e.g., "Neues Wort" → "Neuen Eintrag erstellen") silently breaks the selector.
- **No duplicate detection.** The bot does not check whether a word already exists before
  submitting. Re-running the same list may create duplicate entries.
- **No checkpoint or resume.** If the run is interrupted, there is no mechanism to skip
  already-processed entries on re-run.
- **No dry-run mode.** There is no way to simulate the flow without writing to ConnectLang.
- **No full CLI.** All configuration is via `.env`. The bot does not accept command-line
  flags (`--words-file`, `--headless`, `--dry-run`).
- **No parallelism.** The batch loop is sequential. One word at a time, one browser context.
- **Manual login dependency.** If the session expires, a human must log in again before the
  next run. There is no recovery path that does not require manual intervention.

---

## Future evolution

Not yet implemented. Listed for orientation only:

- **Duplicate detection** — query visible state before submitting to skip existing entries.
- **Checkpoint / resume** — persist a progress file so a re-run skips already-processed words.
- **Dry-run mode** — execute all steps up to submit, then abort without saving.
- **CLI with Typer** — expose `--words-file`, `--headless`, `--dry-run`, and other flags.
- **GitHub Actions** — CI pipeline for linting, type checking, and unit tests on every push.
- **MutationObserver / dynamic wait** — DOM-observer approach for the AI fill step if static
  waits prove unreliable in practice.
- **Page Object Model** — if the project expands to multiple distinct pages or flows, POM
  may be worth introducing to consolidate per-page locators and actions.
