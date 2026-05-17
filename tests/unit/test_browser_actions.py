from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from playwright.sync_api import Error as PlaywrightError

from connectlang_rpa.actions import (
    BrowserActionError,
    safe_click,
    safe_fill,
    safe_select,
    safe_select_combobox,
    wait_until_enabled,
    wait_until_has_value,
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


# --- wait_until_has_value ---


def test_wait_until_has_value_calls_wait_for_visible_first() -> None:
    locator = _make_locator()
    with patch("connectlang_rpa.actions.browser_actions.expect") as mock_expect:
        mock_expect.return_value.to_have_value = MagicMock()
        wait_until_has_value(locator, "translation field")
    locator.wait_for.assert_called_once_with(state="visible", timeout=10_000)


def test_wait_until_has_value_calls_to_have_value_with_nonempty_pattern() -> None:
    locator = _make_locator()
    with patch("connectlang_rpa.actions.browser_actions.expect") as mock_expect:
        assertion = MagicMock()
        mock_expect.return_value = assertion
        wait_until_has_value(locator, "translation field", timeout_ms=5_000)
    mock_expect.assert_called_once_with(locator)
    assertion.to_have_value.assert_called_once()
    args, kwargs = assertion.to_have_value.call_args
    assert kwargs.get("timeout") == 5_000


def test_wait_until_has_value_uses_default_timeout() -> None:
    locator = _make_locator()
    with patch("connectlang_rpa.actions.browser_actions.expect") as mock_expect:
        assertion = MagicMock()
        mock_expect.return_value = assertion
        wait_until_has_value(locator, "translation field")
    _, kwargs = assertion.to_have_value.call_args
    assert kwargs.get("timeout") == 10_000


def test_wait_until_has_value_raises_browser_action_error_when_field_empty() -> None:
    locator = _make_locator()
    with patch("connectlang_rpa.actions.browser_actions.expect") as mock_expect:
        mock_expect.return_value.to_have_value.side_effect = AssertionError("value empty")
        with pytest.raises(BrowserActionError, match="remained empty"):
            wait_until_has_value(locator, "AI generated translation")


def test_wait_until_has_value_includes_context_in_error_message() -> None:
    locator = _make_locator()
    with patch("connectlang_rpa.actions.browser_actions.expect") as mock_expect:
        mock_expect.return_value.to_have_value.side_effect = AssertionError("value empty")
        with pytest.raises(BrowserActionError, match="AI generated translation"):
            wait_until_has_value(locator, "AI generated translation")


def test_wait_until_has_value_preserves_original_cause() -> None:
    locator = _make_locator()
    original = AssertionError("value empty")
    with patch("connectlang_rpa.actions.browser_actions.expect") as mock_expect:
        mock_expect.return_value.to_have_value.side_effect = original
        with pytest.raises(BrowserActionError) as exc_info:
            wait_until_has_value(locator, "translation field")
    assert exc_info.value.__cause__ is original


def test_wait_until_has_value_raises_browser_action_error_when_not_visible() -> None:
    locator = _make_locator()
    locator.wait_for.side_effect = PlaywrightError("timeout")
    with pytest.raises(BrowserActionError, match="translation field"):
        wait_until_has_value(locator, "translation field")


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
    with pytest.raises(BrowserActionError, match="source language select"):
        safe_select(locator, "de", "source language select")


def test_safe_select_preserves_cause() -> None:
    locator = _make_locator()
    original = PlaywrightError("select failed")
    locator.select_option.side_effect = original
    with pytest.raises(BrowserActionError) as exc_info:
        safe_select(locator, "de", "source language select")
    assert exc_info.value.__cause__ is original


# --- safe_select_combobox ---


def test_safe_select_combobox_uses_select_option_when_available() -> None:
    locator = _make_locator()
    safe_select_combobox(locator, "Deutsch", "source language select")
    locator.select_option.assert_called_once_with("Deutsch", timeout=10_000)


def test_safe_select_combobox_uses_custom_timeout() -> None:
    locator = _make_locator()
    safe_select_combobox(locator, "English", "translation language select", timeout_ms=5_000)
    locator.select_option.assert_called_once_with("English", timeout=5_000)


def test_safe_select_combobox_falls_back_to_click_when_select_option_fails() -> None:
    locator = _make_locator()
    option_locator = MagicMock()
    locator.select_option.side_effect = PlaywrightError("not a native select")
    locator.page.get_by_role.return_value = option_locator

    safe_select_combobox(locator, "Deutsch", "source language select")

    locator.click.assert_called_once()
    locator.page.get_by_role.assert_called_once_with("option", name="Deutsch")
    option_locator.click.assert_called_once()


def test_safe_select_combobox_raises_with_value_in_message_on_fallback_failure() -> None:
    locator = _make_locator()
    locator.select_option.side_effect = PlaywrightError("not a native select")
    locator.page.get_by_role.return_value.click.side_effect = PlaywrightError("option not found")

    with pytest.raises(BrowserActionError, match="Deutsch"):
        safe_select_combobox(locator, "Deutsch", "source language select")


def test_safe_select_combobox_raises_with_context_in_message_on_fallback_failure() -> None:
    locator = _make_locator()
    locator.select_option.side_effect = PlaywrightError("not a native select")
    locator.page.get_by_role.return_value.click.side_effect = PlaywrightError("option not found")

    with pytest.raises(BrowserActionError, match="source language select"):
        safe_select_combobox(locator, "Deutsch", "source language select")


def test_safe_select_combobox_preserves_cause_on_fallback_failure() -> None:
    locator = _make_locator()
    original = PlaywrightError("option not found")
    locator.select_option.side_effect = PlaywrightError("not a native select")
    locator.page.get_by_role.return_value.click.side_effect = original

    with pytest.raises(BrowserActionError) as exc_info:
        safe_select_combobox(locator, "Deutsch", "source language select")

    assert exc_info.value.__cause__ is original


def test_safe_select_combobox_does_not_call_click_when_select_option_succeeds() -> None:
    locator = _make_locator()
    safe_select_combobox(locator, "English", "translation language select")
    locator.click.assert_not_called()


# --- isolation: no page navigation or flow methods called ---


def test_actions_do_not_call_goto_or_page_methods() -> None:
    locator = _make_locator()
    safe_click(locator, "button")
    safe_fill(locator, "value", "input")
    safe_select(locator, "opt", "select")

    assert not hasattr(locator, "goto") or not locator.goto.called
