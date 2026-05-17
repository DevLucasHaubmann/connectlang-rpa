from __future__ import annotations

from unittest.mock import MagicMock

from connectlang_rpa.locators import VocabularyLocators


def _make_page() -> MagicMock:
    return MagicMock()


def test_new_word_button_uses_get_by_role() -> None:
    page = _make_page()
    locators = VocabularyLocators(page)

    _ = locators.new_word_button

    page.get_by_role.assert_called_once_with("button", name="Neues Wort")


def test_ai_fill_button_uses_get_by_role() -> None:
    page = _make_page()
    locators = VocabularyLocators(page)

    _ = locators.ai_fill_button

    page.get_by_role.assert_called_once_with("button", name="Mit KI ausfüllen")


def test_submit_button_uses_get_by_role() -> None:
    page = _make_page()
    locators = VocabularyLocators(page)

    _ = locators.submit_button

    page.get_by_role.assert_called_once_with("button", name="Zu meinen Wörtern hinzufügen")


def test_word_type_option_uses_radio_role() -> None:
    page = _make_page()
    locators = VocabularyLocators(page)

    _ = locators.word_type_option

    page.get_by_role.assert_called_once_with("radio", name="Wort")


def test_sentence_type_option_uses_radio_role() -> None:
    page = _make_page()
    locators = VocabularyLocators(page)

    _ = locators.sentence_type_option

    page.get_by_role.assert_called_once_with("radio", name="Satz")


def test_word_input_uses_first_textbox_role() -> None:
    page = _make_page()
    locators = VocabularyLocators(page)

    _ = locators.word_input

    page.get_by_role.assert_called_once_with("textbox")


def test_source_language_select_uses_get_by_label() -> None:
    page = _make_page()
    locators = VocabularyLocators(page)

    _ = locators.source_language_select

    page.get_by_label.assert_called_once_with("SPRACHE")


def test_translation_language_select_uses_get_by_label() -> None:
    page = _make_page()
    locators = VocabularyLocators(page)

    _ = locators.translation_language_select

    page.get_by_label.assert_called_once_with("SPRACHE DER ÜBERSETZUNG")


def test_locators_do_not_call_click_or_fill() -> None:
    page = _make_page()
    locators = VocabularyLocators(page)

    _ = locators.new_word_button
    _ = locators.ai_fill_button
    _ = locators.submit_button
    _ = locators.word_type_option
    _ = locators.sentence_type_option
    _ = locators.source_language_select
    _ = locators.translation_language_select

    for mock_locator in (page.get_by_role.return_value, page.get_by_label.return_value):
        mock_locator.click.assert_not_called()
        mock_locator.fill.assert_not_called()
        mock_locator.select_option.assert_not_called()
