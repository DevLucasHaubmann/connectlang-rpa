from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from playwright.sync_api import Error as PlaywrightError

from connectlang_rpa.exceptions import SessionExpiredError
from connectlang_rpa.services.vocabulary_service import VocabularyService


def _make_service(url: str, button_raises: bool = False) -> VocabularyService:
    """Build a VocabularyService with mocked Page and locators.

    button_raises=True simulates wait_for() timing out (element never appeared).
    button_raises=False simulates wait_for() succeeding (element visible in time).
    """
    page = MagicMock()
    page.url = url

    settings = MagicMock()
    settings.target_url = "https://example.com/vocabulary"
    settings.default_timeout_ms = 5000

    service = VocabularyService(page, settings)

    locators_mock = MagicMock()
    if button_raises:
        locators_mock.new_word_button.wait_for.side_effect = PlaywrightError("Timeout")
    service._locators = locators_mock

    return service


class TestEnsureSessionActive:
    def _call(self, service: VocabularyService) -> None:
        with patch.object(service, "go_to_vocabulary_page"):
            service.ensure_session_active()

    def test_authenticated_session_does_not_raise(self) -> None:
        service = _make_service("https://example.com/vocabulary")
        self._call(service)  # must not raise

    def test_wait_for_called_with_configured_timeout(self) -> None:
        service = _make_service("https://example.com/vocabulary")
        self._call(service)
        service._locators.new_word_button.wait_for.assert_called_once_with(
            state="visible", timeout=5000
        )

    def test_login_url_raises_session_expired(self) -> None:
        service = _make_service("https://example.com/login")
        with pytest.raises(SessionExpiredError, match="login"):
            self._call(service)

    def test_auth_url_raises_session_expired(self) -> None:
        service = _make_service("https://example.com/auth/callback")
        with pytest.raises(SessionExpiredError):
            self._call(service)

    def test_signin_url_raises_session_expired(self) -> None:
        service = _make_service("https://example.com/signin")
        with pytest.raises(SessionExpiredError):
            self._call(service)

    def test_button_timeout_raises_session_expired(self) -> None:
        service = _make_service("https://example.com/vocabulary", button_raises=True)
        with pytest.raises(SessionExpiredError, match="session may have expired"):
            self._call(service)

    def test_login_url_skips_button_wait(self) -> None:
        """URL check must short-circuit before wait_for is called."""
        service = _make_service("https://example.com/login")
        with pytest.raises(SessionExpiredError, match="login"):
            self._call(service)
        service._locators.new_word_button.wait_for.assert_not_called()

    def test_go_to_vocabulary_page_is_called(self) -> None:
        service = _make_service("https://example.com/vocabulary")
        with patch.object(service, "go_to_vocabulary_page") as mock_nav:
            service.ensure_session_active()
        mock_nav.assert_called_once()
