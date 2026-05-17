from __future__ import annotations

from playwright.sync_api import Page

from connectlang_rpa.actions.browser_actions import (
    safe_click,
    safe_fill,
    safe_select_combobox,
    wait_until_visible,
)
from connectlang_rpa.config.settings import Settings
from connectlang_rpa.locators.vocabulary_locators import VocabularyLocators
from connectlang_rpa.models.word_entry import WordEntry


class VocabularyService:
    """Coordinates the vocabulary entry flow for a single word or phrase."""

    def __init__(self, page: Page, settings: Settings) -> None:
        self._page = page
        self._settings = settings
        self._locators = VocabularyLocators(page)

    def go_to_vocabulary_page(self) -> None:
        self._page.goto(
            self._settings.target_url,
            timeout=self._settings.default_timeout_ms,
            wait_until="domcontentloaded",
        )

    def open_new_word_form(self) -> None:
        safe_click(
            self._locators.new_word_button,
            context="new word button",
            timeout_ms=self._settings.default_timeout_ms,
        )

    def fill_word_entry(self, word_entry: WordEntry) -> None:
        if word_entry.entry_type == "sentence":
            safe_click(
                self._locators.sentence_type_option,
                context="sentence type option",
                timeout_ms=self._settings.default_timeout_ms,
            )
        else:
            safe_click(
                self._locators.word_type_option,
                context="word type option",
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

    def trigger_ai_fill(self) -> None:
        safe_click(
            self._locators.ai_fill_button,
            context="AI fill button",
            timeout_ms=self._settings.default_timeout_ms,
        )

    def wait_for_ai_completion(self) -> None:
        wait_until_visible(
            self._locators.ai_filled_translation,
            context="AI generated translation",
            timeout_ms=self._settings.default_timeout_ms,
        )

    def submit_word(self) -> None:
        safe_click(
            self._locators.submit_button,
            context="submit word button",
            timeout_ms=self._settings.default_timeout_ms,
        )

    def add_word(self, word_entry: WordEntry) -> None:
        self.go_to_vocabulary_page()
        self.open_new_word_form()
        self.fill_word_entry(word_entry)
        self.select_languages()
        self.trigger_ai_fill()
        self.wait_for_ai_completion()
        self.submit_word()
