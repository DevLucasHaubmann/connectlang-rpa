from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from connectlang_rpa.core.profile import ensure_browser_profile_ready

if TYPE_CHECKING:
    from connectlang_rpa.config.settings import Settings


class BrowserManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._context

    def start(self) -> BrowserManager:
        ensure_browser_profile_ready(self._settings.browser_profile_dir)
        self._playwright = sync_playwright().start()
        try:
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self._settings.browser_profile_dir),
                headless=self._settings.headless,
            )
            self._context.set_default_timeout(self._settings.default_timeout_ms)
            self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
        except Exception:
            self._stop_playwright()
            raise
        return self

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
            self._context = None
            self._page = None
        self._stop_playwright()

    def _stop_playwright(self) -> None:
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self) -> BrowserManager:
        return self.start()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
