from __future__ import annotations

import structlog
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from connectlang_rpa.actions.browser_actions import BrowserActionError

_log = structlog.get_logger(__name__)

_MAX_ATTEMPTS = 3
_WAIT_INITIAL_S = 1.0
_WAIT_MAX_S = 10.0


def _log_retry_attempt(state: RetryCallState) -> None:
    exc = state.outcome.exception() if state.outcome else None
    _log.warning(
        "retry_attempt",
        attempt=state.attempt_number,
        max_attempts=_MAX_ATTEMPTS,
        error=str(exc) if exc else None,
    )


transient_retry = retry(
    stop=stop_after_attempt(_MAX_ATTEMPTS),
    wait=wait_exponential_jitter(initial=_WAIT_INITIAL_S, max=_WAIT_MAX_S),
    retry=retry_if_exception_type(BrowserActionError),
    before_sleep=_log_retry_attempt,
    reraise=True,
)
