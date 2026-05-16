# Rule: RPA

## Error Isolation

- A failure on one item (e.g., a single word or student record) must not stop the entire batch,
  unless the error is critical (session lost, page unresponsive, unrecoverable state).
- Wrap per-item processing in a try/except that logs and continues to the next item.

## Audit Logging

- Log the outcome (success or failure) for every item processed: item identifier, status, timestamp.
- Use `structlog` with structured fields — no free-form concatenated strings.
- On failure, log the exception type, message, and relevant context (e.g., word, step name).

## Screenshots on Failure

- Capture a screenshot when a recoverable action fails after retries.
- Store under a local `screenshots/` directory (gitignored). Never commit screenshots.

## Session Safety

- The persistent browser profile is a shared resource — do not delete or overwrite it mid-run.
- Before starting a run, verify the session is active; abort with a clear message if it is not.

## Idempotency

- Design flows to be restartable where possible: a re-run after partial failure should resume
  safely without requiring a full reset.
- Avoid duplication when a safe, in-scope mechanism exists to detect it (e.g., checking visible
  state on the page before submitting).
- Full duplicate-detection logic (database checks, persistent state tracking) belongs to the
  future backlog — do not implement it prematurely.

## Retry Policy

- Use `tenacity` for retries. Define explicit `stop` (max attempts) and `wait` (backoff) per action.
- Do not retry indefinitely. Log each retry attempt.
- Do not retry actions that are not idempotent without explicit justification.

## Throughput vs. Reliability

- Prioritize predictability over speed. A slower run that logs every outcome is better than a
  fast run that silently skips failures.
- Add a small, documented operational delay between actions when the target platform may rate-limit.

## Destructive Actions

- Never delete, overwrite, or submit data irreversibly unless the flow explicitly requires it and
  the action is logged before execution.
- Prefer read-verify-write over blind write.