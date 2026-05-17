from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from playwright.sync_api import Error as PlaywrightError

from connectlang_rpa.actions import (
    BrowserActionError,
    safe_click,
    safe_fill,
    safe_select,
    wait_until_enabled,
    wait_until_visible,
)


def _make_locator(*, is_enabled: bool = True) -> MagicMock:
    locator = MagicMock()
    locator.is_enabled.return_value = is_enabled
    return locator


# --- wait_until_visible ---


def test_wait_until_visible_calls_wait_for_visible() -> None:
    locator = _make_locator()
    wait_until_visible(locator, "test element")
    locator.wait_for.assert_called_once_with(state="visible", timeout=10_000)


def test_wait_until_visible_uses_custom_timeout() -> None:
    locator = _make_locator()
    wait_until_visible(locator, "test element", timeout_ms=3_000)
    locator.wait_for.assert_called_once_with(state="visible", timeout=3_000)


def test_wait_until_visible_raises_browser_action_error_on_timeout() -> None:
    locator = _make_locator()
    locator.wait_for.side_effect = PlaywrightError("timeout")
    with pytest.raises(BrowserActionError, match="test element"):
        wait_until_visible(locator, "test element")


def test_wait_until_visible_preserves_original_cause() -> None:
    locator = _make_locator()
    original = PlaywrightError("timeout")
    locator.wait_for.side_effect = original
    with pytest.raises(BrowserActionError) as exc_info:
        wait_until_visible(locator, "test element")
    assert exc_info.value.__cause__ is original


# --- wait_until_enabled ---


def test_wait_until_enabled_calls_wait_for_visible_then_is_enabled() -> None:
    locator = _make_locator(is_enabled=True)
    wait_until_enabled(locator, "test element")
    locator.wait_for.assert_called_once_with(state="visible", timeout=10_000)
    locator.is_enabled.assert_called_once()


def test_wait_until_enabled_raises_if_not_enabled() -> None:
    locator = _make_locator(is_enabled=False)
    with pytest.raises(BrowserActionError, match="not enabled"):
        wait_until_enabled(locator, "disabled element")


def test_wait_until_enabled_raises_on_playwright_timeout() -> None:
    locator = _make_locator()
    locator.wait_for.side_effect = PlaywrightError("timeout")
    with pytest.raises(BrowserActionError, match="disabled element"):
        wait_until_enabled(locator, "disabled element")


def test_wait_until_enabled_preserves_original_cause_on_playwright_error() -> None:
    locator = _make_locator()
    original = PlaywrightError("timeout")
    locator.wait_for.side_effect = original
    with pytest.raises(BrowserActionError) as exc_info:
        wait_until_enabled(locator, "test element")
    assert exc_info.value.__cause__ is original


# --- safe_click ---


def test_safe_click_calls_click_with_timeout() -> None:
    locator = _make_locator()
    safe_click(locator, "new word button")
    locator.click.assert_called_once_with(timeout=10_000)


def test_safe_click_uses_custom_timeout() -> None:
    locator = _make_locator()
    safe_click(locator, "new word button", timeout_ms=5_000)
    locator.click.assert_called_once_with(timeout=5_000)


def test_safe_click_raises_on_playwright_error() -> None:
    locator = _make_locator()
    locator.click.side_effect = PlaywrightError("element not interactable")
    with pytest.raises(BrowserActionError, match="Failed to click 'new word button'"):
        safe_click(locator, "new word button")


def test_safe_click_preserves_cause() -> None:
    locator = _make_locator()
    original = PlaywrightError("element not interactable")
    locator.click.side_effect = original
    with pytest.raises(BrowserActionError) as exc_info:
        safe_click(locator, "new word button")
    assert exc_info.value.__cause__ is original


# --- safe_fill ---


def test_safe_fill_calls_fill_with_value_and_timeout() -> None:
    locator = _make_locator()
    safe_fill(locator, "Hund", "word input")
    locator.fill.assert_called_once_with("Hund", timeout=10_000)


def test_safe_fill_uses_custom_timeout() -> None:
    locator = _make_locator()
    safe_fill(locator, "Katze", "word input", timeout_ms=4_000)
    locator.fill.assert_called_once_with("Katze", timeout=4_000)


def test_safe_fill_raises_on_playwright_error() -> None:
    locator = _make_locator()
    locator.fill.side_effect = PlaywrightError("fill failed")
    with pytest.raises(BrowserActionError, match="Failed to fill 'word input'"):
        safe_fill(locator, "Hund", "word input")


def test_safe_fill_preserves_cause() -> None:
    locator = _make_locator()
    original = PlaywrightError("fill failed")
    locator.fill.side_effect = original
    with pytest.raises(BrowserActionError) as exc_info:
        safe_fill(locator, "Hund", "word input")
    assert exc_info.value.__cause__ is original


# --- safe_select ---


def test_safe_select_calls_select_option_with_value_and_timeout() -> None:
    locator = _make_locator()
    safe_select(locator, "de", "source language select")
    locator.select_option.assert_called_once_with("de", timeout=10_000)


def test_safe_select_uses_custom_timeout() -> None:
    locator = _make_locator()
    safe_select(locator, "en", "translation language select", timeout_ms=2_000)
    locator.select_option.assert_called_once_with("en", timeout=2_000)


def test_safe_select_raises_on_playwright_error() -> None:
    locator = _make_locator()
    locator.select_option.side_effect = PlaywrightError("select failed")
    expected = "Failed to select option on 'source language select'"
    with pytest.raises(BrowserActionError, match=expected):
        safe_select(locator, "de", "source language select")


def test_safe_select_preserves_cause() -> None:
    locator = _make_locator()
    original = PlaywrightError("select failed")
    locator.select_option.side_effect = original
    with pytest.raises(BrowserActionError) as exc_info:
        safe_select(locator, "de", "source language select")
    assert exc_info.value.__cause__ is original


# --- isolation: no page navigation or flow methods called ---


def test_actions_do_not_call_goto_or_page_methods() -> None:
    locator = _make_locator()
    safe_click(locator, "button")
    safe_fill(locator, "value", "input")
    safe_select(locator, "opt", "select")

    assert not hasattr(locator, "goto") or not locator.goto.called
