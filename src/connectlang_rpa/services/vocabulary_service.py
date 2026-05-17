from __future__ import annotations

import contextlib
from typing import Any

import structlog
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, Response

from connectlang_rpa.actions.browser_actions import (
    BrowserActionError,
    safe_click,
    safe_fill,
    safe_select_combobox,
    wait_until_has_value,
    wait_until_hidden,
)
from connectlang_rpa.config.settings import Settings
from connectlang_rpa.exceptions import SessionExpiredError, WordPersistenceError
from connectlang_rpa.locators.vocabulary_locators import VocabularyLocators
from connectlang_rpa.models.word_entry import WordEntry
from connectlang_rpa.utils.retry import transient_retry

log = structlog.get_logger(__name__)

_LOGIN_URL_PATTERNS = ("login", "auth", "entrar", "signin", "sign-in")


class VocabularyService:
    """Coordinates the vocabulary entry flow for a single word or phrase."""

    def __init__(self, page: Page, settings: Settings) -> None:
        self._page = page
        self._settings = settings
        self._locators = VocabularyLocators(page)

    def ensure_session_active(self) -> None:
        """Navigate to the vocabulary page and verify the session is authenticated.

        Raises SessionExpiredError if the URL signals a login redirect or the
        main vocabulary button does not appear within the configured timeout.
        """
        self.go_to_vocabulary_page()
        current_url = self._page.url.lower()
        if any(pattern in current_url for pattern in _LOGIN_URL_PATTERNS):
            raise SessionExpiredError(
                f"Redirected to login page ({self._page.url}). "
                "Open the browser, log in manually, and run again."
            )
        self._assert_vocabulary_page_ready()

    def _assert_vocabulary_page_ready(self) -> None:
        """Wait for the main vocabulary button to become visible.

        Uses a semantic wait so slow page loads do not produce false negatives.
        Raises SessionExpiredError if the button does not appear within timeout.
        """
        try:
            self._locators.new_word_button.wait_for(
                state="visible",
                timeout=self._settings.default_timeout_ms,
            )
        except PlaywrightError as exc:
            raise SessionExpiredError(
                "Vocabulary page loaded but the expected UI was not found within timeout. "
                "The session may have expired. Open the browser, log in manually, and run again."
            ) from exc

    @transient_retry
    def go_to_vocabulary_page(self) -> None:
        try:
            self._page.goto(
                self._settings.target_url,
                timeout=self._settings.default_timeout_ms,
                wait_until="domcontentloaded",
            )
        except PlaywrightError as exc:
            raise BrowserActionError(f"Failed to navigate to vocabulary page: {exc}") from exc

    @transient_retry
    def open_new_word_form(self) -> None:
        safe_click(
            self._locators.new_word_button,
            context="new word button",
            timeout_ms=self._settings.default_timeout_ms,
        )

    def fill_word_entry(self, word_entry: WordEntry) -> None:
        # "Wort" is the default type — only switch when sentence is explicitly required.
        if word_entry.entry_type == "sentence":
            safe_click(
                self._locators.sentence_type_option,
                context="sentence type option",
                timeout_ms=self._settings.default_timeout_ms,
            )

        safe_fill(
            self._locators.word_input,
            word_entry.text,
            context="word input",
            timeout_ms=self._settings.default_timeout_ms,
        )

    def select_languages(self) -> None:
        safe_select_combobox(
            self._locators.source_language_select,
            self._settings.word_language,
            context="source language select",
            timeout_ms=self._settings.default_timeout_ms,
        )
        safe_select_combobox(
            self._locators.translation_language_select,
            self._settings.translation_language,
            context="translation language select",
            timeout_ms=self._settings.default_timeout_ms,
        )

    def _is_ai_fill_already_triggered(self) -> bool:
        """Return True if the AI fill was already triggered (in progress or completed).

        Prevents duplicate clicks when trigger_ai_fill is retried.
        - Button disabled → AI is generating (in progress).
        - Translation field has a value → AI already completed.

        Does NOT catch PlaywrightError: if a visible element fails input_value(),
        that is a real browser error and must propagate, not be silenced.
        """
        button = self._locators.ai_fill_button
        if button.is_visible() and not button.is_enabled():
            return True
        translation = self._locators.ai_filled_translation
        if translation.is_visible():
            return bool(translation.input_value())
        return False

    @transient_retry
    def trigger_ai_fill(self) -> None:
        if self._is_ai_fill_already_triggered():
            return
        safe_click(
            self._locators.ai_fill_button,
            context="AI fill button",
            timeout_ms=self._settings.default_timeout_ms,
        )

    @transient_retry
    def wait_for_ai_completion(self) -> None:
        wait_until_has_value(
            self._locators.ai_filled_translation,
            context="AI generated translation",
            timeout_ms=self._settings.default_timeout_ms,
        )

    def wait_for_submission_completion(self) -> None:
        """Wait for the creation form to close after submitting a word.

        The ConnectLang UI does not expose a role="status" message after saving.
        The reliable signal is the submit button becoming hidden, which happens
        when the modal/form closes on success.
        """
        wait_until_hidden(
            self._locators.submit_button,
            context="submit button after word submission",
            timeout_ms=self._settings.default_timeout_ms,
        )

    def _log_form_state_before_submit(self, word_text: str) -> None:
        """Log the visible state of every required field and the submit button.

        Purely diagnostic — does not raise, does not block submission.
        """
        translation_value: str = ""
        try:
            t = self._locators.ai_filled_translation
            translation_value = t.input_value() if t.is_visible() else "<not visible>"
        except PlaywrightError:
            translation_value = "<error reading>"

        submit_enabled = False
        submit_count = 0
        submit_bbox: object = None
        with contextlib.suppress(Exception):
            btn = self._locators.submit_button
            submit_count = btn.count()
            submit_enabled = btn.is_enabled()
            if submit_count > 0:
                submit_bbox = btn.first.bounding_box()

        source_lang: str = "<unknown>"
        translation_lang: str = "<unknown>"
        with contextlib.suppress(Exception):
            source_lang = self._locators.source_language_select.input_value()
        with contextlib.suppress(Exception):
            translation_lang = self._locators.translation_language_select.input_value()

        log.info(
            "pre_submit_field_state",
            word=word_text,
            translation=translation_value,
            source_language=source_lang,
            translation_language=translation_lang,
            submit_button_count=submit_count,
            submit_button_enabled=submit_enabled,
            submit_button_bbox=submit_bbox,
            url=self._page.url,
        )

    def submit_word(self, word_text: str) -> None:
        """Click the submit button and wait for the form to close.

        Attaches a temporary response listener to capture mutating HTTP requests
        made during the submit window. Logs network outcomes for diagnostics;
        does not raise based on network state alone (UI signal remains authoritative
        for form-close detection).
        """
        wait_until_has_value(
            self._locators.ai_filled_translation,
            context="AI generated translation before submit",
            timeout_ms=self._settings.default_timeout_ms,
        )
        self._log_form_state_before_submit(word_text)

        captured: list[dict[str, Any]] = []

        def _on_response(response: Response) -> None:
            if response.request.method not in ("POST", "PUT", "PATCH"):
                return
            body_excerpt = ""
            try:
                body_excerpt = response.text()[:200]
            except Exception:
                body_excerpt = "<unreadable>"
            captured.append(
                {
                    "method": response.request.method,
                    "url": response.url,
                    "status": response.status,
                    "body_excerpt": body_excerpt,
                }
            )

        self._page.on("response", _on_response)
        try:
            safe_click(
                self._locators.submit_button,
                context="submit word button",
                timeout_ms=self._settings.default_timeout_ms,
            )
            log.info("word_submit_clicked", word=word_text)
            self.wait_for_submission_completion()
        finally:
            self._page.remove_listener("response", _on_response)

        if captured:
            for r in captured:
                status = r["status"]
                event = "submit_network_success" if 200 <= status < 300 else "submit_network_failed"
                log.info(
                    event,
                    method=r["method"],
                    url=r["url"],
                    status=status,
                    body_excerpt=r["body_excerpt"],
                )
        else:
            log.warning(
                "submit_network_no_request",
                detail="no mutating request captured during submit",
            )

    def verify_word_persisted(self, word_text: str) -> None:
        """Navigate to the vocabulary page and confirm the word appears in the list.

        Filters using the search box before checking so the result is not affected
        by pagination. Uses partial match because the platform prepends articles
        (e.g. "die Rechnung"), so an exact search for the bare stem never resolves.

        Raises WordPersistenceError if the word is not visible within the configured
        timeout.
        """
        self.go_to_vocabulary_page()
        try:
            search = self._locators.word_search_input
            search.wait_for(state="visible", timeout=self._settings.default_timeout_ms)
            search.fill(word_text)
        except PlaywrightError:
            log.warning("word_search_input_unavailable", word=word_text)

        locator = self._locators.word_in_list(word_text)
        try:
            locator.wait_for(state="visible", timeout=self._settings.default_timeout_ms)
        except PlaywrightError as exc:
            raise WordPersistenceError(
                f"Word '{word_text}' not found in vocabulary list after submission"
            ) from exc
        log.info("word_persistence_confirmed", word=word_text)

    def add_word(self, word_entry: WordEntry) -> None:
        self.go_to_vocabulary_page()
        self.open_new_word_form()
        self.fill_word_entry(word_entry)
        self.select_languages()
        self.trigger_ai_fill()
        self.wait_for_ai_completion()
        self.submit_word(word_entry.text)
        log.info("word_submit_feedback_received", word=word_entry.text)
        self.verify_word_persisted(word_entry.text)
