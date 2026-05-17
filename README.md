# ConnectLang RPA Bot

Automates vocabulary entry on the ConnectLang platform using a real browser and a persistent session.

---

## Objective

The bot receives a list of German words or phrases and, for each item, navigates to the ConnectLang vocabulary page, opens the new-word form, fills in the text, selects the source and translation languages, triggers the AI auto-fill, waits for completion, and saves the entry — without requiring human interaction after setup.

It does **not** automate login, bypass captcha, or circumvent any site-level security. Authentication is done manually once; the session is then reused via a local browser profile.

---

## Two ways to run

### Terminal

```bash
uv run connectlang-rpa
```

Runs the automation directly. Logs stream to the terminal; a summary is printed at the end.

### Desktop app

```bash
uv run connectlang-desktop
```

Opens a graphical interface built with CustomTkinter. Features:

- **Word list editor** — type or paste words directly; the list is saved to `data/words.json` automatically.
- **One-click execution** — the "Iniciar robô" button runs the bot without touching the terminal.
- **Real-time logs** — each structured log line is parsed and displayed as the bot runs.
- **Progress bar** — shows how many entries have been processed out of the total.
- **Execution summary** — after the run, a panel shows total entries, successes, failures, and exit code.
- **Responsive UI** — the bot runs in a subprocess; the interface stays interactive during execution.

The desktop app is a visual layer over the same core RPA engine. It does not bypass any constraint that applies to the terminal mode.

---

## Flow for each entry

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

## Technologies

| Tool | Role |
|---|---|
| Python 3.12+ | Language |
| Playwright | Browser automation |
| CustomTkinter | Desktop UI |
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
src/connectlang_rpa/
  main.py                          ← terminal orchestrator
  core/browser.py                  ← BrowserManager: persistent context lifecycle
  core/profile.py                  ← validates browser profile directory
  services/vocabulary_service.py   ← VocabularyService: executes the add-word flow
  services/word_loader.py          ← loads and validates the word list from JSON
  locators/vocabulary_locators.py  ← all page locators, separated from flow logic
  actions/browser_actions.py       ← reusable browser interactions (click, fill, wait)
  models/word_entry.py             ← WordEntry dataclass
  utils/logger.py                  ← structlog setup, per-run log file path
  utils/retry.py                   ← tenacity retry decorators
  utils/screenshots.py             ← failure screenshot capture
  config/settings.py               ← typed settings from environment variables
  exceptions.py                    ← domain exceptions
  desktop/
    app.py                         ← desktop entry point
    main_window.py                 ← MainWindow: layout and state machine
    services/process_runner.py     ← runs the bot as a subprocess
    services/log_streamer.py       ← parses JSONL output into UI messages
    services/execution_summary.py  ← aggregates run metrics
    services/desktop_word_service.py ← reads/writes data/words.json
    widgets/word_input_panel.py    ← word list editor widget
    theme.py                       ← colors, fonts, layout constants
```

Key design decisions:

- **`main.py` as the thin orchestrator.** It wires dependencies and drives the batch loop. Business logic lives in services.
- **Locators are constants, not strings scattered in service code.** Any selector change requires editing one file.
- **Actions are reusable.** `browser_actions.py` wraps interactions so services stay readable and retries are applied consistently.
- **Session failure is a hard stop.** If the session has expired, the bot exits before the batch loop begins.
- **Error isolation per item.** A failure on one word is logged and the bot continues to the next.
- **Desktop is a visual layer, not a new engine.** The desktop app calls `uv run connectlang-rpa` as a subprocess; it does not import or call Playwright directly. This keeps the automation logic in one place.

---

## Why Playwright instead of Selenium

- **Auto-waiting built in.** Playwright waits for elements to be actionable before interacting.
- **Semantic locators.** `get_by_role`, `get_by_label`, and `get_by_text` are resilient to minor DOM changes.
- **Persistent context support.** `launch_persistent_context()` provides a first-class API for reusing a browser profile across runs.
- **Modern ergonomics.** The synchronous API is straightforward, type stubs are complete, and mypy integration works well.

---

## Folder structure

```
connectlang-rpa/
├── src/
│   └── connectlang_rpa/
│       ├── actions/
│       ├── config/
│       ├── core/
│       ├── desktop/
│       │   ├── services/
│       │   └── widgets/
│       ├── locators/
│       ├── models/
│       ├── services/
│       ├── utils/
│       ├── exceptions.py
│       └── main.py
├── tests/
│   ├── unit/
│   └── integration/
├── data/
│   └── words.example.json    # example word list (safe to version)
├── logs/                     # per-run .jsonl files (gitignored)
├── screenshots/              # failure screenshots (gitignored)
├── .env.example
├── pyproject.toml
└── README.md
```

> `data/words.json`, `browser-profile/`, `logs/*.jsonl`, `screenshots/*.png`, and `.env` are **never versioned**.
> Only `data/words.example.json`, `logs/.gitkeep`, and `screenshots/.gitkeep` are tracked.

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
cp .env.example .env   # Linux / macOS
Copy-Item .env.example .env   # PowerShell
```

Edit `.env` to match your environment. The defaults work for most setups.

**4. Prepare your word list:**

```bash
cp data/words.example.json data/words.json   # Linux / macOS
Copy-Item data/words.example.json data/words.json   # PowerShell
```

Edit `data/words.json` with the words you want to add — or use the desktop app editor.

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

The word list is a JSON file (`data/words.json` by default, path set by `WORDS_FILE` in `.env`).

**Via terminal (manual edit):**

```json
[
  { "text": "der Termin", "entry_type": "word" },
  { "text": "Ich lerne Deutsch.", "entry_type": "sentence" },
  { "text": "die Zusammenarbeit" }
]
```

- `text` — the word or phrase to add (required).
- `entry_type` — `"word"` or `"sentence"` (optional; defaults to `"word"`).

**Via desktop app:**

Type or paste words in the word editor panel (one word per line) and click **Salvar lista**. The app writes `data/words.json` automatically, with all entries set to `entry_type: "word"`. Sentence entries must be created by editing the JSON file directly.

---

## Logs and screenshots

**Structured logs:**

- Each run writes a `.jsonl` file to `logs/` with a timestamp-based name.
- Every event is a JSON line with structured fields (word text, status, error type).
- The terminal prints a human-readable summary at the end of the run.
- The desktop app displays parsed log lines in real time in the LOGS panel.

**Failure screenshots:**

- When a word fails after retries, a screenshot is captured automatically.
- Saved to `screenshots/` as `error_YYYY-MM-DD_HH-MM-SS_<sanitized-word>.png`.

Both `logs/*.jsonl` and `screenshots/*.png` are gitignored. Only `.gitkeep` files are tracked.

---

## Security

- **No credentials in source code.** All configuration is loaded from environment variables.
- **`.env` is never versioned.** Only `.env.example` with placeholder values is tracked.
- **`browser-profile/` is never versioned.** It contains live session cookies.
- **`data/words.json` is never versioned.** It is a local working file. Only `data/words.example.json` is tracked.
- **No login automation.** The bot does not implement Google OAuth, password submission, or any authentication bypass.
- **No captcha solving.**
- **Logs and screenshots are local artifacts.** They may capture screen content. Do not share or commit them.

---

## Limitations

- **UI dependency.** The bot drives a real browser. Any change to button labels, form structure, or page flow may break locators.
- **No duplicate detection.** The bot does not check whether a word already exists before adding it.
- **No checkpoint.** If the run is interrupted, there is no resume mechanism.
- **No dry-run mode.** There is no way to simulate a run without writing to ConnectLang.
- **No CLI flags.** All configuration is via `.env`. The bot does not support `--words-file`, `--headless`, or `--dry-run`.
- **Desktop hardcodes `entry_type: "word"`.** The word editor always writes `"entry_type": "word"`. Sentence entries require manual JSON editing.
- **Desktop requires `uv` in PATH.** The app launches the bot via `uv run connectlang-rpa`. If `uv` is not accessible from the shell that opens the desktop app, the run will fail immediately.
- **Not a ConnectLang API client.** The bot drives a real browser and may break if the platform changes significantly.

---

## Quality commands

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

---

## Next steps

Planned improvements, not yet implemented:

- **Duplicate detection** — check whether the word is already present before submitting.
- **Checkpoint / resume** — persist progress so a re-run skips already-processed entries.
- **Dry-run mode** — simulate the flow without saving.
- **CLI with Typer** — expose `--words-file`, `--headless`, and `--dry-run` as flags.
- **GitHub Actions** — CI pipeline for linting, type checking, and tests on every push.
- **Sentence support in desktop editor** — allow selecting `entry_type` per word in the UI.
