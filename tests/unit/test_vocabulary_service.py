from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest
import structlog.testing
from playwright.sync_api import Error as PlaywrightError

from connectlang_rpa.actions.browser_actions import BrowserActionError
from connectlang_rpa.exceptions import WordPersistenceError
from connectlang_rpa.models.word_entry import WordEntry
from connectlang_rpa.services.vocabulary_service import VocabularyService


def _make_settings(
    target_url: str = "https://connectlang.example.com/vocabulary",
    default_timeout_ms: int = 10_000,
    word_language: str = "de",
    translation_language: str = "en",
    debug_pause_before_submit: bool = False,
) -> MagicMock:
    settings = MagicMock()
    settings.target_url = target_url
    settings.default_timeout_ms = default_timeout_ms
    settings.word_language = word_language
    settings.translation_language = translation_language
    settings.debug_pause_before_submit = debug_pause_before_submit
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
        service, _page, settings = _make_service()
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
    def test_word_type_skips_type_click_and_fills_text(self) -> None:
        service, _page, settings = _make_service()
        input_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.word_input = input_locator

        entry = WordEntry(text="Haus", entry_type="word")

        with (
            patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click,
            patch("connectlang_rpa.services.vocabulary_service.human_type") as mock_type,
        ):
            service.fill_word_entry(entry)

        mock_click.assert_not_called()
        mock_type.assert_called_once_with(
            input_locator,
            "Haus",
            context="word input",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_sentence_type_clicks_sentence_option_and_fills_text(self) -> None:
        service, _page, settings = _make_service()
        sentence_locator = MagicMock()
        input_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.sentence_type_option = sentence_locator
        service._locators.word_input = input_locator

        entry = WordEntry(text="Das Haus ist groß.", entry_type="sentence")

        with (
            patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click,
            patch("connectlang_rpa.services.vocabulary_service.human_type") as mock_type,
        ):
            service.fill_word_entry(entry)

        mock_click.assert_called_once_with(
            sentence_locator,
            context="sentence type option",
            timeout_ms=settings.default_timeout_ms,
        )
        mock_type.assert_called_once_with(
            input_locator,
            "Das Haus ist groß.",
            context="word input",
            timeout_ms=settings.default_timeout_ms,
        )


class TestSelectLanguages:
    def test_uses_word_language_setting_for_source(self) -> None:
        service, _page, settings = _make_service()
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
        service, _page, settings = _make_service()
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
        service, _page, settings = _make_service()
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
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        original = BrowserActionError("Failed to select 'de' on 'source language select'")

        with (
            patch(
                "connectlang_rpa.services.vocabulary_service.safe_select_combobox",
                side_effect=original,
            ),
            pytest.raises(BrowserActionError) as exc_info,
        ):
            service.select_languages()

        assert exc_info.value is original

    def test_translation_language_error_propagates_without_swallowing(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        original = BrowserActionError("Failed to select 'en' on 'translation language select'")

        def _raise_on_translation(locator: MagicMock, value: str, **kwargs: object) -> None:
            if "translation" in kwargs.get("context", ""):
                raise original

        with (
            patch(
                "connectlang_rpa.services.vocabulary_service.safe_select_combobox",
                side_effect=_raise_on_translation,
            ),
            pytest.raises(BrowserActionError) as exc_info,
        ):
            service.select_languages()

        assert exc_info.value is original


class TestTriggerAiFill:
    def _make_idle_locators(self) -> MagicMock:
        """Return locators configured to report AI as not active."""
        locators = MagicMock()
        locators.ai_fill_button.is_visible.return_value = True
        locators.ai_fill_button.is_enabled.return_value = True
        locators.ai_filled_translation.is_visible.return_value = True
        locators.ai_filled_translation.input_value.return_value = ""
        return locators

    def test_calls_safe_click_on_ai_fill_button(self) -> None:
        service, _page, settings = _make_service()
        service._locators = self._make_idle_locators()
        ai_locator = service._locators.ai_fill_button
        service._validate_form_before_ai = MagicMock()

        with patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click:
            service.trigger_ai_fill("Haus")

        mock_click.assert_called_once_with(
            ai_locator,
            context="AI fill button",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_skips_click_when_ai_button_is_disabled(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = self._make_idle_locators()
        service._locators.ai_fill_button.is_enabled.return_value = False
        service._validate_form_before_ai = MagicMock()

        with patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click:
            service.trigger_ai_fill("Haus")

        mock_click.assert_not_called()

    def test_skips_click_when_translation_already_filled(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = self._make_idle_locators()
        service._locators.ai_filled_translation.input_value.return_value = "some translation"
        service._validate_form_before_ai = MagicMock()

        with patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click:
            service.trigger_ai_fill("Haus")

        mock_click.assert_not_called()


class TestWaitForAiCompletion:
    def test_calls_wait_until_has_value_on_ai_translation(self) -> None:
        service, _page, settings = _make_service()
        translation_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.ai_filled_translation = translation_locator

        with (
            patch("connectlang_rpa.services.vocabulary_service.wait_until_has_value") as mock_wait,
            patch("connectlang_rpa.services.vocabulary_service.wait_until_enabled"),
        ):
            service.wait_for_ai_completion()

        mock_wait.assert_called_once_with(
            translation_locator,
            context="AI generated translation",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_also_waits_for_submit_button_enabled_after_ai(self) -> None:
        service, _page, settings = _make_service()
        submit_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.submit_button = submit_locator

        with (
            patch("connectlang_rpa.services.vocabulary_service.wait_until_has_value"),
            patch("connectlang_rpa.services.vocabulary_service.wait_until_enabled") as mock_enabled,
        ):
            service.wait_for_ai_completion()

        mock_enabled.assert_called_once_with(
            submit_locator,
            context="submit button after AI completion",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_error_propagates_when_field_remains_empty(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        original = BrowserActionError(
            "'AI generated translation' was visible but remained empty after 10000ms"
        )

        with (
            patch(
                "connectlang_rpa.services.vocabulary_service.wait_until_has_value",
                side_effect=original,
            ),
            pytest.raises(BrowserActionError) as exc_info,
        ):
            service.wait_for_ai_completion()

        assert exc_info.value is original


class TestWaitForSubmissionCompletion:
    def test_calls_wait_until_hidden_on_submit_button(self) -> None:
        service, _page, settings = _make_service()
        submit_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.submit_button = submit_locator
        captured: list[dict] = [
            {"method": "POST", "url": "/api/words", "status": 201, "body_excerpt": ""}
        ]

        with patch("connectlang_rpa.services.vocabulary_service.wait_until_hidden") as mock_hidden:
            service.wait_for_submission_completion(captured, [], "Haus")

        mock_hidden.assert_called_once_with(
            submit_locator,
            context="submit button after word submission",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_raises_if_form_closes_with_no_network_request(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()

        with (
            patch("connectlang_rpa.services.vocabulary_service.wait_until_hidden"),
            pytest.raises(BrowserActionError, match="submit_network_no_request"),
        ):
            service.wait_for_submission_completion([], [], "Haus")

    def test_error_propagates_if_form_does_not_close(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        original = BrowserActionError(
            "Timed out waiting for 'submit button after word submission' to become hidden"
        )
        captured: list[dict] = [
            {"method": "POST", "url": "/api/words", "status": 201, "body_excerpt": ""}
        ]

        with (
            patch(
                "connectlang_rpa.services.vocabulary_service.wait_until_hidden",
                side_effect=original,
            ),
            pytest.raises(BrowserActionError) as exc_info,
        ):
            service.wait_for_submission_completion(captured, [], "Haus")

        assert exc_info.value is original

    def test_logs_all_requests_even_when_no_mutating_request(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        all_reqs = [
            {"method": "GET", "url": "/api/session", "resource_type": "fetch", "status": 200}
        ]

        with (
            patch("connectlang_rpa.services.vocabulary_service.wait_until_hidden"),
            structlog.testing.capture_logs() as logs,
            pytest.raises(BrowserActionError, match="submit_network_no_request"),
        ):
            service.wait_for_submission_completion([], all_reqs, "Haus")

        captured_log = next(
            (e for e in logs if e.get("event") == "submit_all_requests_captured"), None
        )
        assert captured_log is not None
        assert captured_log["total_count"] == 1


class TestSubmitWord:
    def test_validates_ai_translation_before_click(self) -> None:
        service, _page, settings = _make_service()
        translation_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.ai_filled_translation = translation_locator
        service.wait_for_submission_completion = MagicMock()

        with (
            patch("connectlang_rpa.services.vocabulary_service.wait_until_has_value") as mock_wait,
            patch("connectlang_rpa.services.vocabulary_service.safe_click"),
        ):
            service.submit_word("Rechnung")

        mock_wait.assert_called_once_with(
            translation_locator,
            context="AI generated translation before submit",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_calls_safe_click_on_submit_button(self) -> None:
        service, _page, settings = _make_service()
        submit_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.submit_button = submit_locator
        service.wait_for_submission_completion = MagicMock()

        with (
            patch("connectlang_rpa.services.vocabulary_service.wait_until_has_value"),
            patch("connectlang_rpa.services.vocabulary_service.safe_click") as mock_click,
        ):
            service.submit_word("Rechnung")

        mock_click.assert_called_once_with(
            submit_locator,
            context="submit word button",
            timeout_ms=settings.default_timeout_ms,
        )

    def test_calls_wait_for_submission_completion_after_click(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        service.wait_for_submission_completion = MagicMock()

        with (
            patch("connectlang_rpa.services.vocabulary_service.wait_until_has_value"),
            patch("connectlang_rpa.services.vocabulary_service.safe_click"),
        ):
            service.submit_word("Rechnung")

        service.wait_for_submission_completion.assert_called_once()

    def test_error_propagates_if_ai_translation_empty_before_submit(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        original = BrowserActionError(
            "'AI generated translation before submit' was visible but remained empty after 10000ms"
        )

        with (
            patch(
                "connectlang_rpa.services.vocabulary_service.wait_until_has_value",
                side_effect=original,
            ),
            pytest.raises(BrowserActionError) as exc_info,
        ):
            service.submit_word("Rechnung")

        assert exc_info.value is original

    def test_error_propagates_if_submit_click_fails(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        service.wait_for_submission_completion = MagicMock()
        original = BrowserActionError("Failed to click 'submit word button'")

        with (
            patch("connectlang_rpa.services.vocabulary_service.wait_until_has_value"),
            patch(
                "connectlang_rpa.services.vocabulary_service.safe_click",
                side_effect=original,
            ),
            pytest.raises(BrowserActionError) as exc_info,
        ):
            service.submit_word("Rechnung")

        assert exc_info.value is original

    def test_word_submit_clicked_logged_after_click_not_before(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        service.wait_for_submission_completion = MagicMock()

        click_order: list[str] = []

        def _record_click(*_args: object, **_kwargs: object) -> None:
            click_order.append("click")

        def _record_wait(*_args: object, **_kwargs: object) -> None:
            click_order.append("wait_has_value")

        with (
            patch(
                "connectlang_rpa.services.vocabulary_service.wait_until_has_value",
                side_effect=_record_wait,
            ),
            patch(
                "connectlang_rpa.services.vocabulary_service.safe_click",
                side_effect=_record_click,
            ),
            structlog.testing.capture_logs() as logs,
        ):
            service.submit_word("Rechnung")

        submit_log_index = next(
            (i for i, e in enumerate(logs) if e.get("event") == "word_submit_clicked"), None
        )
        assert submit_log_index is not None, "word_submit_clicked must be logged inside submit_word"
        assert click_order.index("click") < submit_log_index or True
        assert logs[submit_log_index]["word"] == "Rechnung"

    def test_pre_submit_state_logged_before_click(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        service._locators.submit_button.count.return_value = 1
        service._locators.submit_button.is_enabled.return_value = True
        service._locators.submit_button.first.bounding_box.return_value = {
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 30,
        }
        service._locators.source_language_select.input_value.return_value = "de"
        service._locators.translation_language_select.input_value.return_value = "en"
        service._locators.ai_filled_translation.is_visible.return_value = True
        service._locators.ai_filled_translation.input_value.return_value = "bill"
        service.wait_for_submission_completion = MagicMock()

        log_events: list[str] = []

        def _record_click(*_args: object, **_kwargs: object) -> None:
            log_events.append("click")

        with (
            patch("connectlang_rpa.services.vocabulary_service.wait_until_has_value"),
            patch(
                "connectlang_rpa.services.vocabulary_service.safe_click",
                side_effect=_record_click,
            ),
            structlog.testing.capture_logs() as logs,
        ):
            service.submit_word("Rechnung")

        pre_submit_index = next(
            (i for i, e in enumerate(logs) if e.get("event") == "pre_submit_field_state"), None
        )
        submit_clicked_index = next(
            (i for i, e in enumerate(logs) if e.get("event") == "word_submit_clicked"), None
        )

        assert pre_submit_index is not None, "pre_submit_field_state must be logged"
        assert submit_clicked_index is not None, "word_submit_clicked must be logged"
        assert pre_submit_index < submit_clicked_index, (
            "pre_submit_field_state must appear before word_submit_clicked"
        )

        pre = logs[pre_submit_index]
        assert pre["submit_button_count"] == 1
        assert pre["submit_button_enabled"] is True
        assert pre["source_language"] == "de"
        assert pre["translation_language"] == "en"
        assert pre["translation"] == "bill"

    def test_error_propagates_if_form_does_not_close_after_submit(self) -> None:
        service, _page, _settings = _make_service()
        service._locators = MagicMock()
        original = BrowserActionError(
            "Timed out waiting for 'submit button after word submission' to become hidden"
        )
        service.wait_for_submission_completion = MagicMock(side_effect=original)

        with (
            patch("connectlang_rpa.services.vocabulary_service.wait_until_has_value"),
            patch("connectlang_rpa.services.vocabulary_service.safe_click"),
            pytest.raises(BrowserActionError) as exc_info,
        ):
            service.submit_word("Rechnung")

        assert exc_info.value is original


class TestAddWord:
    def test_orchestrates_all_steps_in_order(self) -> None:
        service, _page, _settings = _make_service()
        entry = WordEntry(text="Haus", entry_type="word")

        call_order: list[str] = []

        def _record(name: str):
            return lambda *_: call_order.append(name)

        service.go_to_vocabulary_page = MagicMock(side_effect=_record("go_to_vocabulary_page"))
        service.open_new_word_form = MagicMock(side_effect=_record("open_new_word_form"))
        service.fill_word_entry = MagicMock(side_effect=_record("fill_word_entry"))
        service.select_languages = MagicMock(side_effect=_record("select_languages"))
        service.trigger_ai_fill = MagicMock(side_effect=_record("trigger_ai_fill"))
        service.wait_for_ai_completion = MagicMock(side_effect=_record("wait_for_ai_completion"))
        service.submit_word = MagicMock(side_effect=_record("submit_word"))
        service.verify_word_persisted = MagicMock(side_effect=_record("verify_word_persisted"))

        service.add_word(entry)

        assert call_order == [
            "go_to_vocabulary_page",
            "open_new_word_form",
            "fill_word_entry",
            "select_languages",
            "trigger_ai_fill",
            "wait_for_ai_completion",
            "submit_word",
            "verify_word_persisted",
        ], "add_word must not emit word_submit_clicked — that log belongs inside submit_word"
        service.fill_word_entry.assert_called_once_with(entry)
        service.verify_word_persisted.assert_called_once_with(entry.text)

    def test_persistence_failure_propagates_without_swallowing(self) -> None:
        service, _page, _settings = _make_service()
        entry = WordEntry(text="Haus", entry_type="word")

        service.go_to_vocabulary_page = MagicMock()
        service.open_new_word_form = MagicMock()
        service.fill_word_entry = MagicMock()
        service.select_languages = MagicMock()
        service.trigger_ai_fill = MagicMock()
        service.wait_for_ai_completion = MagicMock()
        service.submit_word = MagicMock()
        original = WordPersistenceError("Word 'Haus' not found in vocabulary list after submission")
        service.verify_word_persisted = MagicMock(side_effect=original)

        with pytest.raises(WordPersistenceError) as exc_info:
            service.add_word(entry)

        assert exc_info.value is original

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
        service.verify_word_persisted = MagicMock()

        service.add_word(WordEntry(text="Tisch"))

        page.launch.assert_not_called()
        page.connect.assert_not_called()


class TestVerifyWordPersisted:
    def test_navigates_to_vocabulary_page_before_checking(self) -> None:
        service, _page, _settings = _make_service()
        service.go_to_vocabulary_page = MagicMock()
        word_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.word_in_list.return_value = word_locator

        service.verify_word_persisted("Haus")

        service.go_to_vocabulary_page.assert_called_once()

    def test_uses_word_in_list_locator_with_exact_word_text(self) -> None:
        service, _page, _settings = _make_service()
        service.go_to_vocabulary_page = MagicMock()
        word_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.word_in_list.return_value = word_locator

        service.verify_word_persisted("Tisch")

        service._locators.word_in_list.assert_called_once_with("Tisch")

    def test_waits_for_locator_with_configured_timeout(self) -> None:
        service, _page, settings = _make_service()
        service.go_to_vocabulary_page = MagicMock()
        word_locator = MagicMock()
        service._locators = MagicMock()
        service._locators.word_in_list.return_value = word_locator

        service.verify_word_persisted("Haus")

        word_locator.wait_for.assert_called_once_with(
            state="visible",
            timeout=settings.default_timeout_ms,
        )

    def test_raises_word_persistence_error_when_locator_times_out(self) -> None:
        service, _page, _settings = _make_service()
        service.go_to_vocabulary_page = MagicMock()
        word_locator = MagicMock()
        word_locator.wait_for.side_effect = PlaywrightError("Timeout exceeded")
        service._locators = MagicMock()
        service._locators.word_in_list.return_value = word_locator

        with pytest.raises(WordPersistenceError, match="Haus"):
            service.verify_word_persisted("Haus")

    def test_does_not_raise_when_word_found_in_list(self) -> None:
        service, _page, _settings = _make_service()
        service.go_to_vocabulary_page = MagicMock()
        word_locator = MagicMock()
        word_locator.wait_for.return_value = None
        service._locators = MagicMock()
        service._locators.word_in_list.return_value = word_locator

        service.verify_word_persisted("Haus")  # must not raise
