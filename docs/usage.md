# Usage Guide

Step-by-step instructions for setting up and running the ConnectLang RPA Bot from scratch.

---

## Prerequisites

Before starting, confirm you have:

- **Python 3.12 or later** — required by the project.
- **uv** — package and environment manager (see [Section 1](#1-install-uv)).
- **A ConnectLang account** — you must be able to log in manually via Google.
- **Permission to run a local browser** — the bot opens a real Chromium window.

---

## 1. Install uv

Consult the [uv official documentation](https://docs.astral.sh/uv/getting-started/installation/) for
platform-specific instructions.

After installation, confirm it works:

```bash
uv --version
```

---

## 2. Install dependencies

From the project root:

```bash
uv sync
```

This creates a virtual environment and installs all runtime and development dependencies
declared in `pyproject.toml`.

---

## 3. Install the Playwright browser

```bash
uv run playwright install chromium
```

This downloads the Chromium binary managed by Playwright. It is separate from any
system-installed browser.

---

## 4. Create the environment file

**Bash / macOS / Linux:**

```bash
cp .env.example .env
```

**PowerShell (Windows):**

```powershell
Copy-Item .env.example .env
```

Open `.env` and review the values. The defaults work for most setups.

| Variable | Description | Default |
|---|---|---|
| `TARGET_URL` | ConnectLang vocabulary page URL | `https://connectlang.com.br/aluno/vocabulario` |
| `BROWSER_PROFILE_DIR` | Directory for the persistent browser profile | `browser-profile` |
| `HEADLESS` | Run the browser without a visible window (`true`/`false`) | `false` |
| `DEFAULT_TIMEOUT_MS` | Playwright action timeout in milliseconds | `30000` |
| `ACTION_DELAY_MS` | Delay between actions (milliseconds) | `300` |
| `BATCH_SIZE` | Maximum entries per run | `30` |
| `WORD_LANGUAGE` | Source language for vocabulary entries | `Deutsch` |
| `TRANSLATION_LANGUAGE` | Translation language for vocabulary entries | `English` |
| `WORDS_FILE` | Path to the word list JSON file | `words.json` |

> Do not commit `.env`. It is gitignored. Only `.env.example` belongs in version control.

---

## 5. Prepare the word list

**Bash / macOS / Linux:**

```bash
cp data/words.example.json data/words.json
```

**PowerShell (Windows):**

```powershell
Copy-Item data/words.example.json data/words.json
```

Edit `data/words.json` with the entries you want to add:

```json
[
  { "text": "der Termin", "entry_type": "word" },
  { "text": "Ich lerne Deutsch.", "entry_type": "sentence" },
  { "text": "die Zusammenarbeit" }
]
```

- `text` — the word or phrase to add. **Required.**
- `entry_type` — `"word"` or `"sentence"`. Optional; defaults to `"word"` if omitted.

If the file is missing, empty, or contains invalid JSON, the bot exits with an error before
opening the browser. No browser action is taken on an invalid word list.

---

## 6. First run and manual login

The bot does **not** automate login. Authentication is done once, manually.

1. Run the bot (see [Section 7](#7-run-the-automation)).
2. A Chromium window opens with the persistent profile.
3. Log in to ConnectLang manually in that browser window.
4. After logging in, close the browser or let the run finish — the session is saved to
   `browser-profile/`.
5. On subsequent runs, the bot reuses the saved session automatically.

If the session has expired, the bot stops before processing the list and prints a clear
message asking you to log in again.

> **Never version `browser-profile/`.** It contains your active session cookies.
> It is gitignored and must stay local.

---

## 7. Run the automation

```bash
uv run python -m connectlang_rpa.main
```

Alternatively, use the installed script entry point (available after `uv sync`):

```bash
uv run connectlang-rpa
```

Both commands are equivalent. The bot does not support command-line flags; all configuration
is via `.env`.

The bot will:

1. Load and validate the word list.
2. Open the browser with the persistent profile.
3. Verify the session is active.
4. Process each entry: open form, fill text, select languages, trigger AI fill, save.
5. Log the outcome for each entry.
6. Print an execution summary and exit.

---

## 8. Read the execution summary

At the end of each run, the bot prints a summary to the terminal:

| Field | Description |
|---|---|
| `total` | Total number of entries attempted. |
| `successes` | Number of entries saved successfully. |
| `failures` | Number of entries that failed after retries. |
| `elapsed` | Total run time. |
| `log_file` | Path to the `.jsonl` log file for this run. |

If any entry failed, the summary also lists the failed words and the path to their
screenshots (if captured).

---

## 9. Check logs and screenshots

**Logs:**

Each run writes a structured log file to `logs/`:

```
logs/run_2026-05-17_14-30-00.jsonl
```

If two runs start within the same second, a numeric suffix is appended:

```
logs/run_2026-05-17_14-30-00_1.jsonl
```

Each line in the file is a JSON object representing one event (word started, word saved,
word failed, session check, etc.).

**Screenshots:**

When an entry fails after retries, a screenshot is captured automatically:

```
screenshots/error_2026-05-17_14-30-00_der_Termin.png
```

Both `logs/*.jsonl` and `screenshots/*.png` are gitignored. Only `.gitkeep` files are
tracked to preserve the directories in the repository.

> Logs and screenshots may capture visible page content (text, form state). Treat them
> as sensitive local artifacts. Do not share or commit them.

---

## 10. Common errors

| Error | Probable cause | Resolution |
|---|---|---|
| `SessionExpiredError` / vocabulary page unavailable | Session cookie expired; ConnectLang redirected to login. | Log in manually (see [Section 6](#6-first-run-and-manual-login)) and run again. |
| Browser profile locked | Another Chromium process is using `browser-profile/`. | Close any open browser windows that use the same profile, then retry. |
| `words.json` not found | `WORDS_FILE` points to a path that does not exist. | Check the `WORDS_FILE` value in `.env` and confirm the file is present. |
| Invalid JSON in word list | Malformed JSON in `data/words.json`. | Validate the file with a JSON linter. Correct the syntax and retry. |
| Invalid `entry_type` value | A word entry has an `entry_type` other than `"word"` or `"sentence"`. | Fix the value in `data/words.json`. The allowed values are `"word"` and `"sentence"`. |
| AI fill timeout | The AI auto-fill step did not complete within `DEFAULT_TIMEOUT_MS`. | Increase `DEFAULT_TIMEOUT_MS` in `.env`, or retry the failed words manually. |
| Button / locator not found | ConnectLang changed a button label or page structure. | Check `locators/vocabulary_locators.py` and update the affected selector. |
| Possible duplicate word | The same word was already present and the bot submitted it again. | The bot does not detect duplicates. Review the ConnectLang vocabulary list and remove duplicates manually. |

---

## 11. Quality commands

Run these before committing any change:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest
```

All four must pass with no errors.

---

## 12. Safety checklist before committing

```bash
git status
```

Verify that none of the following appear as staged or untracked files:

- `.env` — contains local secrets.
- `browser-profile/` — contains live session cookies.
- `logs/*.jsonl` — may contain screen content.
- `screenshots/*.png` — may contain screen content.

If any of these appear, add them to `.gitignore` or remove them from the staging area
before committing.
