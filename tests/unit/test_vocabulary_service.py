from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from connectlang_rpa.actions.browser_actions import BrowserActionError
from connectlang_rpa.models.word_entry import WordEntry
from connectlang_rpa.services.vocabulary_service import VocabularyService


def _make_settings(
    target_url: str = "https://connectlang.example.com/vocabulary",
    default_timeout_ms: int = 10_000,
    word_language: str = "de",
    translation_language: str = "en",
) -> MagicMock:
    settings = MagicMock()
    settings.target_url = target_url
    settings.default_timeout_ms = default_timeout_ms
    settings.word_language = word_language
    settings.translation_language = translation_language
    return settings


def _make_page() -> MagicMock:
    return MagicMock()


def _make_service() -> tuple[VocabularyService, MagicMock, MagicMock]:
    page = _make_page()
    settings = _make_settings()
    service = VocabularyService(page, settings)
    return service, page, settings


class TestConstructor:
    def test_creates_vocabulary_locators_without_real_browser(self) -> None:
        page = _make_page()
        settings = _make_settings()

        service = VocabularyService(page, settings)

        assert service._locators is not None
        assert service._page is page
        assert service._settings is settings


class TestGoToVocabularyPage:
    def test_calls_goto_with_target_url_and_timeout(self) -> None:
        service, page, settings = _make_service()

        service.go_to_vocabulary_page()

        page.goto.assert_called_once_with(
            settings.target_url,
            timeout=settings.default_timeout_ms,
            wait_until="domcontentloaded",
        )


class TestOpenNewWordForm:
    def test_calls_safe_click_on_new_word_button(self) -> None:
        service, page, settings = _make_service()
        mock_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.new_word_button = mock_locator

        with patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click:
            service.open_new_word_form()

        mock_click.assert_called_once_with(
            mock_locator,
            context="new word button",
            timeout_ms=settings.default_timeout_ms,
        )


class TestFillWordEntry:
    def test_word_type_clicks_word_option_and_fills_text(self) -> None:
        service, page, settings = _make_service()
        word_locator = MagicMock()
        input_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.word_type_option = word_locator
        service._locators.word_input = input_locator

        entry = WordEntry(text="Haus", entry_type="word")

        with (
            patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click,
            patch("connectlang_rpa.services.vocabulary_service.safe_fill") as mock_fill,
        ):
            service.fill_word_entry(entry)

        mock_click.assert_called_once_with(
            word_locator,
            context="word type option",
            timeout_ms=settings.default_timeout_ms,
        )
        mock_fill.assert_called_once_with(
            input_locator,
            "Haus",
            context="word input",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_sentence_type_clicks_sentence_option_and_fills_text(self) -> None:
        service, page, settings = _make_service()
        sentence_locator = MagicMock()
        input_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.sentence_type_option = sentence_locator
        service._locators.word_input = input_locator

        entry = WordEntry(text="Das Haus ist groß.", entry_type="sentence")

        with (
            patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click,
            patch("connectlang_rpa.services.vocabulary_service.safe_fill") as mock_fill,
        ):
            service.fill_word_entry(entry)

        mock_click.assert_called_once_with(
            sentence_locator,
            context="sentence type option",
            timeout_ms=settings.default_timeout_ms,
        )
        mock_fill.assert_called_once_with(
            input_locator,
            "Das Haus ist groß.",
            context="word input",
            timeout_ms=settings.default_timeout_ms,
        )


class TestSelectLanguages:
    def test_uses_word_language_setting_for_source(self) -> None:
        service, page, settings = _make_service()
        source_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.source_language_select = source_locator

        with patch(
            "connectlang_rpa.services.vocabulary_service.safe_select_combobox"
        ) as mock_select:
            service.select_languages()

        mock_select.assert_any_call(
            source_locator,
            settings.word_language,
            context="source language select",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_uses_translation_language_setting_for_translation(self) -> None:
        service, page, settings = _make_service()
        translation_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.translation_language_select = translation_locator

        with patch(
            "connectlang_rpa.services.vocabulary_service.safe_select_combobox"
        ) as mock_select:
            service.select_languages()

        mock_select.assert_any_call(
            translation_locator,
            settings.translation_language,
            context="translation language select",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_calls_safe_select_combobox_for_both_fields_in_order(self) -> None:
        service, page, settings = _make_service()
        source_locator = MagicMock()
        translation_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.source_language_select = source_locator
        service._locators.translation_language_select = translation_locator

        with patch(
            "connectlang_rpa.services.vocabulary_service.safe_select_combobox"
        ) as mock_select:
            service.select_languages()

        assert mock_select.call_count == 2
        assert mock_select.call_args_list == [
            call(
                source_locator,
                settings.word_language,
                context="source language select",
                timeout_ms=settings.default_timeout_ms,
            ),
            call(
                translation_locator,
                settings.translation_language,
                context="translation language select",
                timeout_ms=settings.default_timeout_ms,
            ),
        ]

    def test_source_language_error_propagates_without_swallowing(self) -> None:
        service, page, settings = _make_service()
        service._locators = MagicMock()
        original = BrowserActionError("Failed to select 'de' on 'source language select'")

        with patch(
            "connectlang_rpa.services.vocabulary_service.safe_select_combobox",
            side_effect=original,
        ):
            with pytest.raises(BrowserActionError) as exc_info:
                service.select_languages()

        assert exc_info.value is original

    def test_translation_language_error_propagates_without_swallowing(self) -> None:
        service, page, settings = _make_service()
        service._locators = MagicMock()
        original = BrowserActionError("Failed to select 'en' on 'translation language select'")

        def _raise_on_translation(locator: MagicMock, value: str, **kwargs: object) -> None:
            if "translation" in kwargs.get("context", ""):
                raise original

        with patch(
            "connectlang_rpa.services.vocabulary_service.safe_select_combobox",
            side_effect=_raise_on_translation,
        ):
            with pytest.raises(BrowserActionError) as exc_info:
                service.select_languages()

        assert exc_info.value is original


class TestTriggerAiFill:
    def test_calls_safe_click_on_ai_fill_button(self) -> None:
        service, page, settings = _make_service()
        ai_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.ai_fill_button = ai_locator

        with patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click:
            service.trigger_ai_fill()

        mock_click.assert_called_once_with(
            ai_locator,
            context="AI fill button",
            timeout_ms=settings.default_timeout_ms,
        )


class TestWaitForAiCompletion:
    def test_calls_wait_until_has_value_on_ai_translation(self) -> None:
        service, page, settings = _make_service()
        translation_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.ai_filled_translation = translation_locator

        with patch(
            "connectlang_rpa.services.vocabulary_service.wait_until_has_value"
        ) as mock_wait:
            service.wait_for_ai_completion()

        mock_wait.assert_called_once_with(
            translation_locator,
            context="AI generated translation",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_error_propagates_when_field_remains_empty(self) -> None:
        service, page, settings = _make_service()
        service._locators = MagicMock()
        original = BrowserActionError(
            "'AI generated translation' was visible but remained empty after 10000ms"
        )

        with patch(
            "connectlang_rpa.services.vocabulary_service.wait_until_has_value",
            side_effect=original,
        ):
            with pytest.raises(BrowserActionError) as exc_info:
                service.wait_for_ai_completion()

        assert exc_info.value is original


class TestSubmitWord:
    def test_calls_safe_click_on_submit_button(self) -> None:
        service, page, settings = _make_service()
        submit_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.submit_button = submit_locator

        with patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click:
            service.submit_word()

        mock_click.assert_called_once_with(
            submit_locator,
            context="submit word button",
            timeout_ms=settings.default_timeout_ms,
        )


class TestAddWord:
    def test_orchestrates_all_steps_in_order(self) -> None:
        service, page, settings = _make_service()
        entry = WordEntry(text="Haus", entry_type="word")

        call_order: list[str] = []

        def _record(name: str):  # noqa: ANN202
            return lambda *_: call_order.append(name)

        service.go_to_vocabulary_page = MagicMock(side_effect=_record("go_to_vocabulary_page"))
        service.open_new_word_form = MagicMock(side_effect=_record("open_new_word_form"))
        service.fill_word_entry = MagicMock(side_effect=_record("fill_word_entry"))
        service.select_languages = MagicMock(side_effect=_record("select_languages"))
        service.trigger_ai_fill = MagicMock(side_effect=_record("trigger_ai_fill"))
        service.wait_for_ai_completion = MagicMock(side_effect=_record("wait_for_ai_completion"))
        service.submit_word = MagicMock(side_effect=_record("submit_word"))

        service.add_word(entry)

        assert call_order == [
            "go_to_vocabulary_page",
            "open_new_word_form",
            "fill_word_entry",
            "select_languages",
            "trigger_ai_fill",
            "wait_for_ai_completion",
            "submit_word",
        ]
        service.fill_word_entry.assert_called_once_with(entry)

    def test_does_not_open_real_browser(self) -> None:
        page = _make_page()
        settings = _make_settings()
        service = VocabularyService(page, settings)

        page.launch = MagicMock()
        page.connect = MagicMock()

        service.go_to_vocabulary_page = MagicMock()
        service.open_new_word_form = MagicMock()
        service.fill_word_entry = MagicMock()
        service.select_languages = MagicMock()
        service.trigger_ai_fill = MagicMock()
        service.wait_for_ai_completion = MagicMock()
        service.submit_word = MagicMock()

        service.add_word(WordEntry(text="Tisch"))

        page.launch.assert_not_called()
        page.connect.assert_not_called()
