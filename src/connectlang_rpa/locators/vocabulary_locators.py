from __future__ import annotations

from playwright.sync_api import Locator, Page

_NEW_WORD_BUTTON = "Neues Wort"
_AI_FILL_BUTTON = "Mit KI ausfüllen"
_SUBMIT_BUTTON = "Zu meinen Wörtern hinzufügen"
_WORD_OPTION = "Wort"
_SENTENCE_OPTION = "Satz"


class VocabularyLocators:
    """Centralizes locators for the vocabulary entry page.

    Returns Locator objects only — no actions, no waits, no flow logic.
    """

    def __init__(self, page: Page) -> None:
        self._page = page

    @property
    def new_word_button(self) -> Locator:
        return self._page.get_by_role("button", name=_NEW_WORD_BUTTON)

    @property
    def word_input(self) -> Locator:
        # Fallback: no stable role/label confirmed yet — using placeholder as best guess.
        # TODO: verify against live DOM; replace if a label or aria-label is present.
        return self._page.get_by_placeholder("Wort oder Phrase eingeben")

    @property
    def word_type_option(self) -> Locator:
        return self._page.get_by_role("radio", name=_WORD_OPTION)

    @property
    def sentence_type_option(self) -> Locator:
        return self._page.get_by_role("radio", name=_SENTENCE_OPTION)

    @property
    def source_language_select(self) -> Locator:
        # TODO: verify label text against live DOM; combobox may carry a different accessible name.
        return self._page.get_by_role("combobox", name="Sprache des Wortes")

    @property
    def translation_language_select(self) -> Locator:
        # TODO: verify label text against live DOM.
        return self._page.get_by_role("combobox", name="Sprache der Übersetzung")

    @property
    def ai_fill_button(self) -> Locator:
        return self._page.get_by_role("button", name=_AI_FILL_BUTTON)

    @property
    def ai_filled_translation(self) -> Locator:
        # TODO: confirm role/label once AI response renders in DOM.
        return self._page.get_by_role("textbox", name="Übersetzung")

    @property
    def ai_filled_example(self) -> Locator:
        # TODO: confirm role/label once AI response renders in DOM.
        return self._page.get_by_role("textbox", name="Beispielsatz")

    @property
    def submit_button(self) -> Locator:
        return self._page.get_by_role("button", name=_SUBMIT_BUTTON)

    @property
    def success_message(self) -> Locator:
        # TODO: confirm exact text/role after a successful submission.
        return self._page.get_by_role("status")
