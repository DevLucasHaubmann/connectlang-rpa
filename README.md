# ConnectLang RPA Bot

Automates vocabulary entry on the ConnectLang platform using a real browser and a persistent session.

---

## Objective

The bot receives a list of German words or phrases and, for each item, navigates to the ConnectLang vocabulary page, opens the new-word form, fills in the text, selects the source and translation languages, triggers the AI auto-fill, waits for completion, and saves the entry — without requiring human interaction after setup.

It does **not** automate login, bypass captcha, or circumvent any site-level security. Authentication is done manually once; the session is then reused via a local browser profile.

---

## Flow demonstration

For each entry in the word list, the bot executes the following steps:

1. Open the browser with the persistent session profile.
2. Navigate to the vocabulary page (`TARGET_URL`).
3. Verify the session is active; abort with a clear message if it is not.
4. Click **Neues Wort**.
5. Fill in the word or phrase.
6. Select **Deutsch** as the source language and **English** as the translation language.
7. Click **Mit KI ausfüllen** and wait for the AI to complete the form.
8. Click **Zu meinen Wörtern hinzufügen** to save the entry.
9. Log the outcome (success or failure) and move to the next item.

At the end of the run, a summary is printed to the terminal and written to a structured log file.

---

## Technologies used

| Tool | Role |
|---|---|
| Python 3.12+ | Language |
| Playwright | Browser automation |
| uv | Package and environment manager |
| pydantic-settings | Configuration and validation via environment variables |
| structlog | Structured JSON logging |
| tenacity | Controlled retry with exponential backoff |
| pytest | Unit and integration tests |
| Ruff | Linting and formatting |
| mypy (strict) | Static type checking |

---

## Architecture

```
main.py                  ← orchestrator: loads config, starts browser, runs the batch loop
core/browser.py          ← BrowserManager: opens/closes the persistent browser context
core/profile.py          ← resolves and validates the browser profile directory
services/vocabulary_service.py  ← VocabularyService: executes the add-word flow per entry
services/word_loader.py  ← loads and validates the word list from JSON
locators/vocabulary_locators.py ← all page locators in one place, separated from flow logic
actions/browser_actions.py      ← low-level, reusable browser interactions (click, fill, wait)
models/word_entry.py     ← WordEntry dataclass: pure data, no business logic
utils/logger.py          ← configures structlog, builds per-run log file paths
utils/retry.py           ← tenacity retry decorators shared across actions
utils/screenshots.py     ← captures and names failure screenshots
config/settings.py       ← Settings model: all configuration loaded from environment
exceptions.py            ← domain exceptions (e.g., SessionExpiredError)
```

Key design decisions:

- **`main.py` as the thin orchestrator.** It wires dependencies and drives the batch loop. Business logic lives in services.
- **Locators are constants, not strings scattered in service code.** Any selector change requires editing one file.
- **Actions are reusable.** `browser_actions.py` contains wrapped interactions (click, fill, wait) so services stay readable and retries are applied consistently.
- **Session failure is a hard stop.** If the session has expired before the run starts, the bot exits with a clear message rather than attempting to re-authenticate.
- **Error isolation per item.** A failure on one word is logged and the bot continues to the next, unless the error is unrecoverable (session lost, page crash).

---

## Why Playwright instead of Selenium

Playwright was chosen for the following reasons:

- **Auto-waiting built in.** Playwright waits for elements to be actionable before interacting; Selenium requires explicit waits at every step.
- **Semantic locators.** `get_by_role`, `get_by_label`, and `get_by_text` make selectors more resilient to minor DOM changes.
- **Persistent context support.** `launch_persistent_context()` provides a clean, first-class API for reusing a browser profile across runs.
- **Modern ergonomics.** The synchronous API is straightforward, the type stubs are complete, and mypy integration works well.

Selenium is a solid tool, but Playwright's approach fits this project's requirements more naturally.

---

## Folder structure

```
connectlang-rpa/
├── src/
│   └── connectlang_rpa/
│       ├── actions/          # low-level browser interactions
│       ├── config/           # settings (pydantic-settings)
│       ├── core/             # browser lifecycle, profile management
│       ├── locators/         # page locator definitions
│       ├── models/           # data entities (WordEntry)
│       ├── services/         # business flow (VocabularyService, word_loader)
│       ├── utils/            # logger, retry, screenshots
│       ├── exceptions.py
│       └── main.py
├── tests/
│   ├── unit/
│   └── integration/
├── data/
│   └── words.example.json    # example word list (safe to version)
├── logs/                     # per-run .jsonl files (gitignored, .gitkeep tracked)
├── screenshots/              # failure screenshots (gitignored, .gitkeep tracked)
├── .env.example              # configuration template
├── pyproject.toml
└── README.md
```

> `browser-profile/`, `logs/*.jsonl`, `screenshots/*.png`, and `.env` are never versioned.

---

## Environment setup

**1. Install dependencies:**

```bash
uv sync
```

**2. Install the Chromium browser for Playwright:**

```bash
uv run playwright install chromium
```

**3. Create your `.env` file from the template:**

```bash
cp .env.example .env
```

Edit `.env` to match your environment. The defaults work for most setups.

**4. Prepare your word list:**

```bash
cp data/words.example.json data/words.json
```

Edit `data/words.json` with the words you want to add (see [How to add words](#how-to-add-words)).

---

## How to run

```bash
uv run python -m connectlang_rpa.main
```

The bot opens the browser, verifies the session, processes all entries, and prints a summary.

You can also run via the installed script (after `uv sync`):

```bash
uv run connectlang-rpa
```

---

## Manual login

The bot does not automate login. Authentication is done once, manually:

1. Run the bot for the first time. The browser will open.
2. Log in to ConnectLang manually in the browser window.
3. Close the browser (or let the run finish — the session is already saved).
4. On subsequent runs, the bot reuses the saved session from `browser-profile/`.
5. If the session has expired, the bot stops before processing the list and prints a clear message asking you to log in manually again.

> **Never version `browser-profile/`.** It contains your active session cookies.

---

## How to add words

The word list is a JSON file (`words.json` by default, path set by `WORDS_FILE` in `.env`).

Example (`data/words.example.json`):

```json
[
  {
    "text": "der Termin",
    "entry_type": "word"
  },
  {
    "text": "Ich lerne Deutsch.",
    "entry_type": "sentence"
  },
  {
    "text": "die Zusammenarbeit"
  }
]
```

- `text` — the word or phrase to add (required).
- `entry_type` — `"word"` or `"sentence"` (optional; defaults to `"word"` if omitted).

---

## Logs and screenshots

**Structured logs:**

- Each run writes a `.jsonl` file to `logs/` with a timestamp-based name (e.g., `logs/run_2026-05-17_14-30-00.jsonl`). If a file with the same timestamp already exists, a counter suffix is appended (e.g., `run_2026-05-17_14-30-00_1.jsonl`).
- Every event — word started, word saved, word failed, session check — is a JSON line with structured fields.
- The terminal also prints a human-readable execution summary at the end.

**Failure screenshots:**

- When a word fails after retries, a screenshot is captured automatically.
- Screenshots are saved to `screenshots/` with the format `error_YYYY-MM-DD_HH-MM-SS_<sanitized-word>.png` (e.g., `error_2026-05-17_14-30-00_der_Termin.png`).

Both `logs/*.jsonl` and `screenshots/*.png` are gitignored. Only `.gitkeep` files are tracked to preserve the directories in the repository.

---

## Security

- **No credentials in source code.** All configuration is loaded from environment variables via `.env`.
- **`.env` is never versioned.** The repository only contains `.env.example` with placeholder values.
- **`browser-profile/` is never versioned.** It contains live session cookies.
- **No login automation.** The bot does not implement Google OAuth, password submission, or any authentication bypass.
- **No captcha solving.** The bot does not interact with or bypass captcha or 2FA.
- **Input validation.** The word list is validated by the `WordEntry` model before the run starts. Malformed entries are rejected early.
- **Logs and screenshots are local artifacts.** They may capture screen content (text, UI state). Treat them as sensitive and do not share or commit them.

---

## Limitations

- **UI dependency.** The bot relies on the ConnectLang page structure. If button labels or page flow change, locators may need to be updated.
- **No duplicate detection.** The bot does not check whether a word already exists before adding it. Re-running the same list may create duplicates.
- **No checkpoint.** If the run is interrupted, there is no resume mechanism. Words already processed will be processed again on a re-run.
- **No dry-run mode.** There is no way to simulate a run without actually writing to ConnectLang.
- **No full CLI yet.** The project exposes a basic script entry point (`connectlang-rpa`), but it does not support command-line flags such as `--words-file`, `--headless`, or `--dry-run`. All configuration is via `.env`.
- **Not a ConnectLang API client.** The bot drives a real browser. It is not backed by an official API and may break if the platform changes significantly.

---

## Next steps

Planned improvements, not yet implemented:

- **Duplicate detection** — check whether the word is already present before submitting the form.
- **Checkpoint / resume** — persist progress so a re-run after interruption skips already-processed entries.
- **Dry-run mode** — simulate the flow without saving, for validation purposes.
- **CLI with Typer** — expose `--words-file`, `--headless`, `--dry-run`, and other flags as command-line arguments.
- **GitHub Actions** — CI pipeline to run linting, type checking, and tests on every push.
- **MutationObserver / dynamic wait** — if the AI fill step proves unreliable with static waits, a DOM-observer approach may improve robustness.
