# Rule: Python

## Type Hints

- All public function signatures must have full type annotations (parameters and return type).
- Avoid `Any` unless strictly unavoidable; document the reason with a one-line comment when used.
- Use `Optional[T]` or `T | None` (Python 3.10+) — never omit the `None` case implicitly.

## Naming

- Use descriptive names: `word_text`, not `wt` or `x`.
- Boolean variables and functions that return booleans must use `is_`, `has_`, or `can_` prefixes.
- Constants in `UPPER_SNAKE_CASE` at module level only.

## Functions

- Keep functions short and cohesive. One function = one responsibility.
- Prefer early returns over nested conditionals.
- No functions longer than ~30 lines without a strong reason.

## Data Structures

- Use `dataclass` for simple data containers with no behavior.
- Use `Pydantic BaseModel` for validated input/output boundaries (e.g., config, API-like models).
- Do not add business logic inside models — they are pure data holders.

## File Paths

- Use `pathlib.Path` for all file and directory operations.
- Never concatenate paths with string `+`. Use `/` operator or `Path.joinpath()`.

## State

- Avoid mutable global state. Pass dependencies explicitly as function parameters or via constructor injection.
- Module-level constants are allowed; module-level mutable variables are not.

## Separation of Concerns

- Keep pure logic (data transformation, validation, computation) separate from browser interaction code.
- Functions that receive a `Page` object must only perform browser actions — not compute business logic.

## Prohibited

- `from module import *`
- `print()` for observability — use `structlog` loggers.
- `time.sleep()` as the primary wait mechanism.
- Inline magic numbers — assign them to a named constant.