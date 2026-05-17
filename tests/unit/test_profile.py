from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from connectlang_rpa.core.profile import (
    BrowserProfileLockError,
    ensure_browser_profile_ready,
)


def test_creates_directory_when_absent(tmp_path: Path) -> None:
    profile_dir = tmp_path / "new_profile"
    assert not profile_dir.exists()
    ensure_browser_profile_ready(profile_dir)
    assert profile_dir.is_dir()


def test_succeeds_when_directory_exists_and_no_locks(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    ensure_browser_profile_ready(profile_dir)  # must not raise


def test_raises_when_profile_path_is_a_file(tmp_path: Path) -> None:
    profile_file = tmp_path / "profile"
    profile_file.write_text("not a directory")
    with pytest.raises(ValueError, match="not a directory"):
        ensure_browser_profile_ready(profile_file)


@pytest.mark.parametrize("lock_name", ["SingletonLock", "SingletonCookie", "SingletonSocket"])
def test_raises_on_lock_file(tmp_path: Path, lock_name: str) -> None:
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    (profile_dir / lock_name).write_text("")
    with pytest.raises(BrowserProfileLockError, match=lock_name):
        ensure_browser_profile_ready(profile_dir)


def test_lock_error_message_mentions_closing_browser(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    (profile_dir / "SingletonLock").write_text("")
    pattern = "(?i)(chromium|chrome|playwright|navegador|browser)"
    with pytest.raises(BrowserProfileLockError, match=pattern):
        ensure_browser_profile_ready(profile_dir)


def test_browser_manager_start_calls_preflight(tmp_path: Path) -> None:
    from connectlang_rpa.core.browser import BrowserManager

    settings = MagicMock()
    settings.browser_profile_dir = tmp_path / "profile"
    settings.headless = True
    settings.default_timeout_ms = 10_000

    with (
        patch("connectlang_rpa.core.browser.ensure_browser_profile_ready") as mock_preflight,
        patch("connectlang_rpa.core.browser.sync_playwright") as mock_sync_pw,
    ):
        mock_context = MagicMock()
        mock_context.pages = []
        mock_pw = MagicMock()
        mock_pw.chromium.launch_persistent_context.return_value = mock_context
        mock_sync_pw.return_value.start.return_value = mock_pw

        manager = BrowserManager(settings)
        manager.start()

        mock_preflight.assert_called_once_with(settings.browser_profile_dir)
