from __future__ import annotations

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from connectlang_rpa.actions.browser_actions import (
    BrowserActionError,
    safe_click,
    safe_fill,
    safe_select_combobox,
    wait_until_has_value,
    wait_until_hidden,
)
from connectlang_rpa.config.settings import Settings
from connectlang_rpa.exceptions import SessionExpiredError
from connectlang_rpa.locators.vocabulary_locators import VocabularyLocators
from connectlang_rpa.models.word_entry import WordEntry
from connectlang_rpa.utils.retry import transient_retry

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

    def submit_word(self) -> None:
        wait_until_has_value(
            self._locators.ai_filled_translation,
            context="AI generated translation before submit",
            timeout_ms=self._settings.default_timeout_ms,
        )
        safe_click(
            self._locators.submit_button,
            context="submit word button",
            timeout_ms=self._settings.default_timeout_ms,
        )
        self.wait_for_submission_completion()

    def add_word(self, word_entry: WordEntry) -> None:
        self.go_to_vocabulary_page()
        self.open_new_word_form()
        self.fill_word_entry(word_entry)
        self.select_languages()
        self.trigger_ai_fill()
        self.wait_for_ai_completion()
        self.submit_word()
