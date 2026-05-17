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

`data/words.json` is the local working file. It is **not versioned**. `data/words.example.json`
is the versioned template.

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
opening the browser.

Alternatively, use the desktop app to manage the word list (see [Section 8](#8-edit-words-in-the-desktop-app)).

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

### Option A — Terminal

```bash
uv run connectlang-rpa
```

The bot loads the word list, opens the browser, processes each entry, and prints a summary.
Structured logs stream to the terminal in real time.

### Option B — Desktop app

```bash
uv run connectlang-desktop
```

Opens a graphical window with three panels:

| Panel | Purpose |
|---|---|
| Word list editor (left) | Add/remove words; click **Salvar lista** to persist to `data/words.json`. |
| Execution panel (right) | Shows progress bar, current word, and execution status. |
| Log panel (bottom) | Displays parsed log lines in real time as the bot runs. |

Click **Iniciar robô** to start the run. The button is disabled until the word list has
at least one entry. The word list editor is locked while a run is in progress.

After the run completes, an execution summary panel appears showing total entries, successes,
failures, and exit code.

> The desktop app requires `uv` to be accessible in the PATH of the shell that launches it.

---

## 8. Edit words in the desktop app

The word editor accepts one word or phrase per line. Blank lines and duplicates are ignored.

1. Type or paste words in the text area (one per line).
2. Click **Salvar lista**.
3. The app writes `data/words.json` and enables the **Iniciar robô** button.

Note: the desktop editor always saves entries with `entry_type: "word"`. To add sentence
entries (`entry_type: "sentence"`), edit `data/words.json` directly in a text editor.

---

## 9. Read the execution summary

At the end of each run, the bot prints a summary to the terminal (and displays it in the
desktop app's execution panel):

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

## 10. Check logs and screenshots

**Logs:**

Each run writes a structured log file to `logs/`:

```
logs/run_2026-05-17_14-30-00.jsonl
```

If two runs start within the same second, a numeric suffix is appended:

```
logs/run_2026-05-17_14-30-00_1.jsonl
```

Each line is a JSON object representing one event (word started, word saved, word failed,
session check, etc.).

**Screenshots:**

When an entry fails after retries, a screenshot is captured automatically:

```
screenshots/error_2026-05-17_14-30-00_der_Termin.png
```

Both `logs/*.jsonl` and `screenshots/*.png` are gitignored. Only `.gitkeep` files are
tracked to preserve the directories.

> Logs and screenshots may capture visible page content. Treat them as sensitive local
> artifacts. Do not share or commit them.

---

## 11. Common errors

| Error | Probable cause | Resolution |
|---|---|---|
| `SessionExpiredError` / vocabulary page unavailable | Session cookie expired. | Log in manually (see [Section 6](#6-first-run-and-manual-login)) and run again. |
| Browser profile locked | Another Chromium process is using `browser-profile/`. | Close any open browser windows using the same profile, then retry. |
| `words.json` not found | `WORDS_FILE` points to a path that does not exist. | Check `WORDS_FILE` in `.env` and confirm the file is present. |
| Invalid JSON in word list | Malformed JSON in `data/words.json`. | Validate with a JSON linter; correct and retry. |
| Invalid `entry_type` value | A word entry has a value other than `"word"` or `"sentence"`. | Fix the value in `data/words.json`. |
| AI fill timeout | The AI auto-fill step did not complete within `DEFAULT_TIMEOUT_MS`. | Increase `DEFAULT_TIMEOUT_MS` in `.env`, or retry the failed words. |
| Button / locator not found | ConnectLang changed a button label or page structure. | Check `locators/vocabulary_locators.py` and update the affected selector. |
| Possible duplicate word | The same word was already present and the bot submitted it again. | The bot does not detect duplicates. Review ConnectLang and remove duplicates manually. |
| Desktop: bot does not start | `uv` is not in PATH. | Ensure `uv` is installed and accessible from the shell that opens the desktop app. |

---

## 12. Quality commands

Run these before committing any change:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

All three must pass with no errors.

---

## 13. Safety checklist before committing

```bash
git status
```

Verify that none of the following appear as staged or untracked files:

- `.env` — contains local secrets.
- `browser-profile/` — contains live session cookies.
- `data/words.json` — local working file; not for version control.
- `logs/*.jsonl` — may contain screen content.
- `screenshots/*.png` — may contain screen content.

If any of these appear, remove them from the staging area before committing.
