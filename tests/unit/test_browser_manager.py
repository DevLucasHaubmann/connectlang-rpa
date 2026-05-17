from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from connectlang_rpa.core.browser import BrowserManager


def _make_settings(tmp_path: Path) -> MagicMock:
    settings = MagicMock()
    settings.browser_profile_dir = tmp_path / "profile"
    settings.headless = True
    settings.default_timeout_ms = 10_000
    return settings


def test_page_before_start_raises(tmp_path: Path) -> None:
    manager = BrowserManager(_make_settings(tmp_path))
    with pytest.raises(RuntimeError, match="not started"):
        _ = manager.page  # noqa: F841


def test_context_before_start_raises(tmp_path: Path) -> None:
    manager = BrowserManager(_make_settings(tmp_path))
    with pytest.raises(RuntimeError, match="not started"):
        _ = manager.context  # noqa: F841


def test_close_without_start_is_safe(tmp_path: Path) -> None:
    manager = BrowserManager(_make_settings(tmp_path))
    manager.close()  # must not raise


def test_close_is_idempotent(tmp_path: Path) -> None:
    manager = BrowserManager(_make_settings(tmp_path))
    manager.close()
    manager.close()  # second call must not raise


def test_settings_stored_on_init(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    manager = BrowserManager(settings)
    assert manager._settings is settings


def test_start_failure_stops_playwright(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    with patch("connectlang_rpa.core.browser.sync_playwright") as mock_sync_playwright:
        mock_pw_instance = MagicMock()
        mock_sync_playwright.return_value.start.return_value = mock_pw_instance
        mock_pw_instance.chromium.launch_persistent_context.side_effect = RuntimeError(
            "launch failed"
        )

        manager = BrowserManager(settings)
        with pytest.raises(RuntimeError, match="launch failed"):
            manager.start()

        mock_pw_instance.stop.assert_called_once()


def test_context_manager_calls_start_and_close(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    manager = BrowserManager(settings)

    with patch.object(manager, "start", return_value=manager) as mock_start, \
         patch.object(manager, "close") as mock_close:
        with manager:
            pass
        mock_start.assert_called_once()
        mock_close.assert_called_once()
