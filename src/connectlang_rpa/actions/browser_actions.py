from __future__ import annotations

import re

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, expect

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


def wait_until_has_value(
    locator: Locator,
    context: str,
    timeout_ms: int | None = None,
) -> None:
    """Wait for a visible textbox to contain a non-empty value.

    Polls via Playwright's expect API, which retries internally until timeout.
    Raises BrowserActionError if the field remains empty after timeout.
    """
    timeout = timeout_ms if timeout_ms is not None else _DEFAULT_TIMEOUT_MS
    wait_until_visible(locator, context, timeout_ms)
    try:
        expect(locator).to_have_value(re.compile(r".+"), timeout=timeout)
    except AssertionError as exc:
        raise BrowserActionError(
            f"'{context}' was visible but remained empty after {timeout}ms"
        ) from exc


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
        raise BrowserActionError(f"Failed to select '{value}' on '{context}': {exc}") from exc


def safe_select_combobox(
    locator: Locator,
    value: str,
    context: str,
    timeout_ms: int | None = None,
) -> None:
    """Select a value from a combobox, with fallback for custom dropdown components.

    Tries select_option(label=value) first — scoped to the specific <select> element,
    matching by visible label text. If that fails (custom widget), clicks the combobox
    to open it and then clicks the matching option within the locator's subtree.
    """
    timeout = timeout_ms if timeout_ms is not None else _DEFAULT_TIMEOUT_MS
    wait_until_enabled(locator, context, timeout_ms)
    select_option_exc: PlaywrightError | None = None
    try:
        locator.select_option(label=value, timeout=timeout)
        return
    except PlaywrightError as exc:
        select_option_exc = exc
    _click_combobox_option(locator, value, context, timeout, select_option_exc)


def _click_combobox_option(
    locator: Locator,
    value: str,
    context: str,
    timeout: int,
    select_option_exc: PlaywrightError | None = None,
) -> None:
    try:
        locator.click(timeout=timeout)
        locator.get_by_role("option", name=value).click(timeout=timeout)
    except PlaywrightError as exc:
        cause: BaseException = exc if select_option_exc is None else select_option_exc
        raise BrowserActionError(f"Failed to select '{value}' on '{context}'") from cause
