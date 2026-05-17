from __future__ import annotations

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator

_DEFAULT_TIMEOUT_MS = 10_000


class BrowserActionError(RuntimeError):
    """Raised when a browser interaction fails after all retries."""


def wait_until_visible(
    locator: Locator,
    context: str,
    timeout_ms: int | None = None,
) -> None:
    timeout = timeout_ms if timeout_ms is not None else _DEFAULT_TIMEOUT_MS
    try:
        locator.wait_for(state="visible", timeout=timeout)
    except PlaywrightError as exc:
        raise BrowserActionError(f"Timed out waiting for '{context}' to become visible") from exc


def wait_until_enabled(
    locator: Locator,
    context: str,
    timeout_ms: int | None = None,
) -> None:
    timeout = timeout_ms if timeout_ms is not None else _DEFAULT_TIMEOUT_MS
    try:
        locator.wait_for(state="visible", timeout=timeout)
        if not locator.is_enabled():
            raise BrowserActionError(f"Element '{context}' is visible but not enabled")
    except BrowserActionError:
        raise
    except PlaywrightError as exc:
        raise BrowserActionError(f"Timed out waiting for '{context}' to become enabled") from exc


def safe_click(
    locator: Locator,
    context: str,
    timeout_ms: int | None = None,
) -> None:
    timeout = timeout_ms if timeout_ms is not None else _DEFAULT_TIMEOUT_MS
    wait_until_enabled(locator, context, timeout_ms)
    try:
        locator.click(timeout=timeout)
    except PlaywrightError as exc:
        raise BrowserActionError(f"Failed to click '{context}': {exc}") from exc


def safe_fill(
    locator: Locator,
    value: str,
    context: str,
    timeout_ms: int | None = None,
) -> None:
    timeout = timeout_ms if timeout_ms is not None else _DEFAULT_TIMEOUT_MS
    wait_until_enabled(locator, context, timeout_ms)
    try:
        locator.fill(value, timeout=timeout)
    except PlaywrightError as exc:
        raise BrowserActionError(f"Failed to fill '{context}': {exc}") from exc


def safe_select(
    locator: Locator,
    value: str,
    context: str,
    timeout_ms: int | None = None,
) -> None:
    timeout = timeout_ms if timeout_ms is not None else _DEFAULT_TIMEOUT_MS
    wait_until_enabled(locator, context, timeout_ms)
    try:
        locator.select_option(value, timeout=timeout)
    except PlaywrightError as exc:
        raise BrowserActionError(f"Failed to select option on '{context}': {exc}") from exc
