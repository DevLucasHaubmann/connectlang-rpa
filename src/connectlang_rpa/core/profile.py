from __future__ import annotations

from pathlib import Path

_CHROMIUM_LOCK_FILES = ("SingletonLock", "SingletonCookie", "SingletonSocket")


class BrowserProfileLockError(RuntimeError):
    pass


def ensure_browser_profile_ready(profile_dir: Path) -> None:
    """Validate and prepare the persistent browser profile directory.

    Raises:
        ValueError: if profile_dir exists but is not a directory.
        BrowserProfileLockError: if a Chromium lock file is detected.
    """
    if profile_dir.exists() and not profile_dir.is_dir():
        raise ValueError(
            f"Browser profile path exists but is not a directory: {profile_dir}"
        )

    profile_dir.mkdir(parents=True, exist_ok=True)

    detected = [name for name in _CHROMIUM_LOCK_FILES if (profile_dir / name).exists()]
    if detected:
        files = ", ".join(detected)
        raise BrowserProfileLockError(
            f"Chromium lock file(s) detected in profile directory: {files}. "
            "Close any open Chromium, Chrome, or Playwright browser "
            "using this profile and try again."
        )
