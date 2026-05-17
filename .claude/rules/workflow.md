# Rule: Workflow

## Task Execution

- Work one task at a time. Do not start the next task without explicit approval.
- Read and understand the full task scope before making any changes.
- Modify only files within the declared scope. Do not make opportunistic improvements outside it.

## Before Acting

- Identify all files that will be touched.
- If scope is ambiguous, ask before implementing — do not assume.
- If a rule in `CLAUDE.md` or a domain rule conflicts with the request, flag the conflict first.

## After Acting

Report at the end of every task:

1. **Files analyzed** — every file read, even if unchanged.
2. **Files modified** — with a one-line description of what changed.
3. **Commands executed** — exact commands run, if any.
4. **Blockers / open questions** — anything that could not be resolved.
5. **Suggested commit** — semantic commit message in English (see format below).

## Commit Format

Follow Conventional Commits:

```
<type>(<scope>): <short summary in imperative mood>
```

Types: `feat`, `fix`, `chore`, `test`, `docs`, `refactor`.

Examples:
- `feat(vocabulary): add word entry loader`
- `fix(locators): correct new word button selector`
- `docs(claude): update rpa workflow rules`

- One logical change per commit.
- Never bundle unrelated changes into a single commit.
- Commit messages must be in English.

## Branching

- Use feature branches: `feat/<task-slug>`, `fix/<issue-slug>`, `chore/<task-slug>`.
- Do not commit directly to `main`.
- Open a PR for review before merging, even for solo work.

## Prohibited

- Advancing to the next task without closing the current one.
- Leaving TODO comments in committed code.
- Committing `.env`, `browser-profile/`, screenshots, or real logs.