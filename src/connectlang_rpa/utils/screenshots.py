from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import structlog
from playwright.sync_api import Page

log = structlog.get_logger(__name__)

_SCREENSHOTS_DIR = Path("screenshots")
_UNSAFE_CHARS_RE = re.compile(r"[^\w\-]")


def sanitize_filename(text: str) -> str:
    """Replace characters unsafe for filenames with underscores, collapse runs."""
    sanitized = _UNSAFE_CHARS_RE.sub("_", text)
    return re.sub(r"_+", "_", sanitized).strip("_")


def build_screenshot_path(word: str) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_word = sanitize_filename(word)
    filename = f"error_{timestamp}_{safe_word}.png"
    return _SCREENSHOTS_DIR / filename


def capture_failure_screenshot(page: Page, word: str) -> Path | None:
    """Save a screenshot for a failed word. Returns the path or None if saving fails."""
    path = build_screenshot_path(word)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path))
        log.info("screenshot_saved", path=str(path), word=word)
        return path
    except Exception as exc:
        log.warning("screenshot_failed", word=word, error=str(exc))
        return None
