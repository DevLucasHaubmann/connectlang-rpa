from __future__ import annotations

from playwright.sync_api import Locator, Page

_NEW_WORD_BUTTON = "Neues Wort"
_AI_FILL_BUTTON = "Mit KI ausfüllen"
_SUBMIT_BUTTON = "Zu meinen Wörtern hinzufügen"
_WORD_OPTION = "Wort"
_SENTENCE_OPTION = "Satz"
_WORD_SEARCH_PLACEHOLDER = "Wort suchen..."

# The "Wort hinzufügen" form renders exactly two native <select> elements.
# get_by_label("SPRACHE") is prohibited here: it resolves to the global
# <button aria-label="Sprache"> in the platform header, not the form select.
_SOURCE_LANGUAGE_SELECT_INDEX = 0
_TRANSLATION_LANGUAGE_SELECT_INDEX = 1


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
        # First textbox in the "Wort hinzufügen" form — confirmed via manual inspection.
        return self._page.get_by_role("textbox").first

    @property
    def word_type_option(self) -> Locator:
        return self._page.get_by_role("radio", name=_WORD_OPTION)

    @property
    def sentence_type_option(self) -> Locator:
        return self._page.get_by_role("radio", name=_SENTENCE_OPTION)

    @property
    def source_language_select(self) -> Locator:
        return self._page.locator("select").nth(_SOURCE_LANGUAGE_SELECT_INDEX)

    @property
    def translation_language_select(self) -> Locator:
        return self._page.locator("select").nth(_TRANSLATION_LANGUAGE_SELECT_INDEX)

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
    def word_search_input(self) -> Locator:
        return self._page.get_by_placeholder(_WORD_SEARCH_PLACEHOLDER)

    def word_in_list(self, word_text: str) -> Locator:
        """Return a locator for the word entry in the vocabulary list.

        Uses partial match because the platform prepends articles (e.g. "die Rechnung",
        "der Fahrplan"), so an exact search for the bare stem would never resolve.
        """
        return self._page.get_by_text(word_text, exact=False)
