# Rule: Testing

## Priority Order

1. Unit tests for pure logic first: models, validators, helpers, `word_loader`, settings parsing.
2. Integration tests for non-browser services (file I/O, config loading).
3. Manual tests for browser flows — document them; do not automate against a live browser initially.

## Unit Tests

- Test one behavior per test function.
- Name tests: `test_<unit>_<condition>_<expected_result>`.
- Do not depend on external state, network, or the filesystem unless explicitly testing I/O.
- Use `tmp_path` (pytest fixture) for any filesystem operations in tests.

## What to Cover

- `word_loader`: valid file, empty file, malformed lines, encoding edge cases.
- `models`: field validation, defaults, rejection of invalid input.
- `settings`: required fields present, missing required field raises on startup.
- Sanitization helpers: known inputs → expected outputs.

## Test Organization

```
tests/
  unit/        # pure logic, no I/O
  integration/ # config, file loading
  manual/      # markdown documents describing browser test procedures
```

## Quality Gates

When the project environment exists (`pyproject.toml`, `uv`), run before closing any task:

```
uv run ruff check .
uv run mypy src/
uv run pytest tests/unit tests/integration
```

## Prohibited

- Tests that pass by catching and ignoring exceptions (`except: pass`).
- Mocking internal implementation details — mock at external boundaries only.
- Tests that depend on insertion order or random data without a fixed seed.

## Manual Browser Tests

- Document manual test steps in `tests/manual/<flow>.md`.
- Include: preconditions, steps, expected result, and how to verify in the browser.
- Do not substitute manual docs with empty test stubs.