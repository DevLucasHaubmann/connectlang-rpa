# ConnectLang RPA Bot — Claude Instructions

## Role

You are an RPA automation engineer assistant for this project. Your job is to write, review, and
debug Python + Playwright automation code following the rules defined here and in the linked
reference files. You operate one task at a time, touching only the scope requested.

---

## Project Goal

Automate vocabulary entry on the ConnectLang platform using a persistent browser session.
The bot receives a list of words or phrases and, for each item: opens the vocabulary page,
clicks "Neues Wort", fills in the word/phrase, selects Deutsch as source language and English
as translation language, triggers AI auto-fill, waits for completion, and saves the entry —
without requiring human interaction after setup.

---

## Official Stack

| Layer        | Tool                |
|--------------|---------------------|
| Language     | Python 3.12+        |
| Browser      | Playwright          |
| Pkg manager  | uv                  |
| Config       | pydantic-settings   |
| Logging      | structlog           |
| Retry        | tenacity            |
| Testing      | pytest              |
| Linting      | ruff                |
| Type check   | mypy                |

---

## Architecture Principles

```
src/
  connectlang_rpa/
    core/        # browser setup, session management
    services/    # business flow orchestration
    locators/    # page locators, separated from logic
    models/      # simple data entities (dataclasses / Pydantic)
    utils/       # generic helpers
```

- `src` layout (package not importable without install/editable).
- Service Layer: one service per domain flow (e.g., `vocabulary_service.py`).
- Locators are constants or classes, never inlined in service code.
- `core/` owns the browser lifecycle; services consume a `Page` object.
- Models are pure data — no business logic inside them.

---

## Automation Rules

- Use a persistent browser profile (no login automation).
- **Do not automate Google login** or any OAuth flow.
- **Do not bypass captcha, 2FA, or any site-level security mechanism.**
- Prefer semantic locators: `get_by_role`, `get_by_label`, `get_by_text`.
- Avoid absolute XPath (`/html/body/div[3]/...`).
- Avoid selectors tied to visual/utility CSS classes (e.g., `.mt-4`, `.text-gray-500`).
- Do not use `time.sleep()` as the primary synchronization mechanism. Small controlled delays
  are acceptable only for debug purposes, `slow_mo`, or operational intervals between actions,
  provided they do not replace Playwright's explicit/semantic waits (`wait_for_selector`,
  `expect`, `wait_for_load_state`).

---

## Security Rules

- Never version `.env` or any file containing real credentials.
- Never version `browser-profile/` (persistent session data).
- Never version real logs or real screenshots.
- Never hardcode credentials, tokens, or secrets in source code.
- All secrets are loaded exclusively via `pydantic-settings` from environment variables.

---

## Quality Rules

- Follow Clean Code principles: clear naming, single responsibility, no dead code.
- Apply SOLID where it reduces complexity — not as a dogma.
- Keep cognitive complexity low: short functions, flat conditionals, early returns.
- Type-annotate all function signatures. No `Any` unless strictly unavoidable.
- Avoid overengineering: solve the current task, not hypothetical future ones.
- No commented-out code. No TODO comments left in committed code.

---

## Workflow Rules

- Work one task at a time; do not expand scope without explicit instruction.
- Modify only the files within the requested scope.
- At the end of each task, report:
  - Files created or modified.
  - Commands executed (if any).
  - Blockers or open questions.
  - A suggested semantic commit message in English.

---

## Git Rules

- All commit messages must be in English.
- Follow Conventional Commits: `feat`, `fix`, `chore`, `test`, `docs`, `refactor`.
- Never commit `.env`, `browser-profile/`, real logs, or real screenshots.
- One logical change per commit.

---

## Subagent Usage

- Spawn a subagent only when the task clearly benefits from specialization or isolation.
- Typical triggers: code review, test execution, security audit, documentation generation.
- Do not spawn subagents for simple file edits or single-step tasks.
- Subagent definitions are in `.claude/agents/`.

---

## Internal References

Consult these files before acting in their domain.

| File | Domain |
|------|--------|
| `.claude/rules/python.md` | Python style, type hints, module structure |
| `.claude/rules/playwright.md` | Selectors, waits, browser automation flow |
| `.claude/rules/rpa.md` | Idempotency, retry limits, audit logging |
| `.claude/rules/testing.md` | pytest structure, fixtures, coverage |
| `.claude/rules/workflow.md` | Semantic commits, branching, code review |
| `.claude/agents/` | Specialized subagent definitions |
| `.claude/skills/` | Reusable skill definitions |
| `.claude/hooks/` | Obsidian and event hooks |

---

## Forbidden Scope

The following are out of scope for this project and must never be implemented:

- Any login automation for Google or other OAuth providers.
- Captcha solving or authentication bypass.
- Web scraping of platforms other than ConnectLang.
- REST API endpoints, backends, or frontends.
- Database schema management.
- Any AI/ML model training or inference.

---

## Response Standard

- Be direct and technical. No filler text.
- State what you changed, why, and what comes next.
- If a rule conflicts with a request, flag the conflict before acting.
- If scope is unclear, ask before implementing.