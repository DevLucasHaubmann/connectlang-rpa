from __future__ import annotations

import contextlib
from typing import Any

import structlog
from playwright.sync_api import ConsoleMessage, Page, Response
from playwright.sync_api import Error as PlaywrightError

from connectlang_rpa.actions.browser_actions import (
    BrowserActionError,
    dispatch_change_and_blur,
    human_type,
    safe_click,
    safe_select_combobox,
    wait_until_enabled,
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
        """Fill the word/phrase field using human-like keystroke simulation.

        Uses human_type() instead of fill() so that React/Vue input event handlers
        fire and the framework's internal state reflects the typed value before
        subsequent steps proceed.
        """
        if word_entry.entry_type == "sentence":
            safe_click(
                self._locators.sentence_type_option,
                context="sentence type option",
                timeout_ms=self._settings.default_timeout_ms,
            )

        human_type(
            self._locators.word_input,
            word_entry.text,
            context="word input",
            timeout_ms=self._settings.default_timeout_ms,
        )

        actual_value: str = "<error>"
        with contextlib.suppress(Exception):
            actual_value = self._locators.word_input.input_value()
        log.info("word_input_value_after_typing", word=word_entry.text, actual_value=actual_value)

    def select_languages(self) -> None:
        """Select source and translation languages and dispatch change/blur events.

        select_option() alone does not trigger the framework's onChange handlers.
        Dispatching change+blur after each selection ensures the frontend state
        is updated before the AI fill button is clicked.
        """
        safe_select_combobox(
            self._locators.source_language_select,
            self._settings.word_language,
            context="source language select",
            timeout_ms=self._settings.default_timeout_ms,
        )
        dispatch_change_and_blur(self._locators.source_language_select, "source language select")

        safe_select_combobox(
            self._locators.translation_language_select,
            self._settings.translation_language,
            context="translation language select",
            timeout_ms=self._settings.default_timeout_ms,
        )
        dispatch_change_and_blur(
            self._locators.translation_language_select, "translation language select"
        )

        source_lang: str = "<error>"
        translation_lang: str = "<error>"
        with contextlib.suppress(Exception):
            source_lang = self._locators.source_language_select.input_value()
        with contextlib.suppress(Exception):
            translation_lang = self._locators.translation_language_select.input_value()
        log.info(
            "language_state_after_selection",
            source_language=source_lang,
            translation_language=translation_lang,
        )

    def _validate_form_before_ai(self, word_text: str) -> None:
        """Verify that all fields are correctly set before triggering AI fill.

        Raises BrowserActionError if any required field is missing or incorrect.
        """
        word_value: str = ""
        with contextlib.suppress(Exception):
            word_value = self._locators.word_input.input_value()

        source_lang: str = ""
        translation_lang: str = ""
        with contextlib.suppress(Exception):
            source_lang = self._locators.source_language_select.input_value()
        with contextlib.suppress(Exception):
            translation_lang = self._locators.translation_language_select.input_value()

        ai_button_enabled = False
        with contextlib.suppress(Exception):
            btn = self._locators.ai_fill_button
            ai_button_enabled = btn.is_visible() and btn.is_enabled()

        log.info(
            "ai_fields_ready",
            word=word_text,
            word_input_value=word_value,
            source_language=source_lang,
            translation_language=translation_lang,
            ai_button_enabled=ai_button_enabled,
        )

        if not word_value:
            raise BrowserActionError(f"Word input is empty before AI fill — expected '{word_text}'")
        if not source_lang:
            raise BrowserActionError("Source language not selected before AI fill")
        if not translation_lang:
            raise BrowserActionError("Translation language not selected before AI fill")
        if not ai_button_enabled:
            raise BrowserActionError("AI fill button is not enabled before clicking")

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
    def trigger_ai_fill(self, word_text: str) -> None:
        self._validate_form_before_ai(word_text)
        if self._is_ai_fill_already_triggered():
            return
        safe_click(
            self._locators.ai_fill_button,
            context="AI fill button",
            timeout_ms=self._settings.default_timeout_ms,
        )

    @transient_retry
    def wait_for_ai_completion(self) -> None:
        """Wait for AI fill to fully complete.

        Completion requires:
        1. Translation field has a non-empty value.
        2. Submit button is enabled (not just visible) — the platform enables it
           only after the AI response is fully processed and the form is valid.
        """
        wait_until_has_value(
            self._locators.ai_filled_translation,
            context="AI generated translation",
            timeout_ms=self._settings.default_timeout_ms,
        )
        wait_until_enabled(
            self._locators.submit_button,
            context="submit button after AI completion",
            timeout_ms=self._settings.default_timeout_ms,
        )

    def _log_submit_button_details(self, word_text: str) -> None:
        """Log full DOM state of the submit button before clicking.

        Reads tagName, type, disabled, aria-disabled, textContent, and a truncated
        outerHTML via evaluate() so that any discrepancy between what Playwright sees
        and what the browser exposes is captured before the click attempt.
        """
        try:
            btn = self._locators.submit_button
            count = btn.count()
            if count == 0:
                log.warning("submit_button_not_found", word=word_text)
                return
            el = btn.first
            bbox = el.bounding_box()
            is_visible = el.is_visible()
            is_enabled = el.is_enabled()
            tag_name: str = el.evaluate("el => el.tagName")
            btn_type: str | None = el.evaluate("el => el.type || null")
            disabled: bool = el.evaluate("el => el.disabled")
            aria_disabled: str | None = el.evaluate("el => el.getAttribute('aria-disabled')")
            text_content: str = el.evaluate("el => (el.textContent || '').trim().slice(0, 100)")
            outer_html: str = el.evaluate("el => el.outerHTML.slice(0, 300)")
            log.info(
                "submit_button_detailed_state",
                word=word_text,
                button_count=count,
                tag_name=tag_name,
                btn_type=btn_type,
                disabled=disabled,
                aria_disabled=aria_disabled,
                text_content=text_content,
                outer_html=outer_html,
                bbox=bbox,
                is_visible=is_visible,
                is_enabled=is_enabled,
            )
        except Exception as exc:
            log.warning("submit_button_details_error", word=word_text, error=str(exc))

    def _log_button_hit_test(self, word_text: str) -> None:
        """Report which DOM element is at the submit button's visual center.

        Does NOT scroll — the hit-test is read-only diagnostics. Scrolling before
        elementFromPoint was found to close the modal via the platform's scroll
        listener. Logs viewport size and whether the computed center falls within
        it to explain a null elementFromPoint result.
        """
        try:
            btn = self._locators.submit_button.first
            bbox = btn.bounding_box()
            if not bbox:
                log.warning("submit_button_hittest_no_bbox", word=word_text)
                return
            cx = bbox["x"] + bbox["width"] / 2
            cy = bbox["y"] + bbox["height"] / 2
            viewport = self._page.viewport_size
            vw = viewport["width"] if viewport else None
            vh = viewport["height"] if viewport else None
            in_viewport = vw is not None and vh is not None and 0 <= cx <= vw and 0 <= cy <= vh
            result: dict[str, Any] | None = self._page.evaluate(
                """([x, y]) => {
                    const el = document.elementFromPoint(x, y);
                    if (!el) return null;
                    return {
                        tagName: el.tagName,
                        textContent: (el.textContent || '').trim().slice(0, 100),
                        className: el.className || '',
                        disabled: el.disabled ?? null,
                        ariaDisabled: el.getAttribute('aria-disabled'),
                        isButton: el.tagName === 'BUTTON',
                        outerHTML: el.outerHTML.slice(0, 200),
                    };
                }""",
                [cx, cy],
            )
            if result is None and not in_viewport:
                log.warning(
                    "submit_button_hittest_center_out_of_viewport",
                    word=word_text,
                    center_x=cx,
                    center_y=cy,
                    viewport_width=vw,
                    viewport_height=vh,
                )
            log.info(
                "submit_button_hittest",
                word=word_text,
                center_x=cx,
                center_y=cy,
                viewport_width=vw,
                viewport_height=vh,
                center_in_viewport=in_viewport,
                element_at_point=result,
            )
        except Exception as exc:
            log.warning("submit_button_hittest_error", word=word_text, error=str(exc))

    def _execute_submit_click(self, word_text: str) -> None:
        """Execute the submit click using the configured strategy.

        Strategy is controlled by SUBMIT_CLICK_STRATEGY env var (default: locator).
        All strategies are instrumented equally — network capture and persistence
        verification run after regardless of which strategy is used.
        """
        strategy = self._settings.submit_click_strategy
        btn = self._locators.submit_button
        log.info("submit_click_strategy", word=word_text, strategy=strategy)

        timeout = self._settings.default_timeout_ms
        if strategy == "locator":
            safe_click(btn, context="submit word button", timeout_ms=timeout)
        elif strategy == "locator_after_scroll":
            btn.first.scroll_into_view_if_needed()
            safe_click(btn, context="submit word button", timeout_ms=timeout)
        elif strategy == "locator_position":
            bbox = btn.first.bounding_box()
            if not bbox:
                raise BrowserActionError(
                    "submit button has no bounding box for locator_position strategy"
                )
            btn.first.click(position={"x": bbox["width"] / 2, "y": bbox["height"] / 2})
        elif strategy == "mouse_center":
            btn.first.scroll_into_view_if_needed()
            bbox = btn.first.bounding_box()
            if not bbox:
                raise BrowserActionError(
                    "submit button has no bounding box for mouse_center strategy"
                )
            cx = bbox["x"] + bbox["width"] / 2
            cy = bbox["y"] + bbox["height"] / 2
            self._page.mouse.click(cx, cy)
        elif strategy == "keyboard_space":
            btn.first.focus()
            self._page.keyboard.press("Space")
        elif strategy == "keyboard_enter":
            btn.first.focus()
            self._page.keyboard.press("Enter")
        elif strategy == "js_click":
            btn.first.evaluate("el => el.click()")
        elif strategy == "mouse_center_no_scroll":
            bbox = btn.first.bounding_box()
            if not bbox:
                raise BrowserActionError(
                    "submit button has no bounding box for mouse_center_no_scroll strategy"
                )
            cx = bbox["x"] + bbox["width"] / 2
            cy = bbox["y"] + bbox["height"] / 2
            self._page.mouse.click(cx, cy)
        else:
            raise BrowserActionError(f"Unknown submit_click_strategy: {strategy!r}")

        log.info("word_submit_clicked", word=word_text, strategy=strategy)

    def _blur_active_field(self) -> None:
        """Click the page body to blur any focused input before submitting.

        Forces the frontend to process any pending onChange/onBlur handlers
        before the submit click reaches the button.
        """
        with contextlib.suppress(PlaywrightError):
            self._page.evaluate("document.activeElement?.blur()")

    def _log_form_state_before_submit(self, word_text: str) -> None:
        """Log the visible state of every required field and the submit button."""
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

        log.info(
            "submit_button_state_before_click",
            submit_button_count=submit_count,
            submit_button_enabled=submit_enabled,
            submit_button_bbox=submit_bbox,
        )

    def wait_for_submission_completion(
        self,
        captured: list[dict[str, Any]],
        all_requests: list[dict[str, Any]],
        word_text: str,
    ) -> None:
        """Wait for the submit operation to produce a mutating network request.

        Waits for the form to close (submit button hidden) as the UI signal.
        After the form closes, waits an additional grace period for in-flight
        responses — platforms with optimistic UI close the modal before the
        server response arrives.
        Logs all requests (including GET/fetch/XHR) for diagnostic purposes.

        Raises BrowserActionError if the form closes with no mutating request,
        which indicates the click did not trigger the backend save operation.
        """
        wait_until_hidden(
            self._locators.submit_button,
            context="submit button after word submission",
            timeout_ms=self._settings.default_timeout_ms,
        )
        self._page.wait_for_timeout(3_000)

        log.info(
            "submit_all_requests_captured",
            word=word_text,
            total_count=len(all_requests),
            requests=all_requests[:30],
        )

        if not captured:
            log.warning(
                "submit_network_no_request",
                word=word_text,
                detail="form closed but no mutating request was captured",
                all_requests_count=len(all_requests),
            )
            raise BrowserActionError(
                f"submit_network_no_request: form closed for '{word_text}' "
                "but no POST/PUT/PATCH was captured. The click did not trigger a backend save."
            )

    def submit_word(self, word_text: str) -> None:
        """Click the submit button and confirm a mutating network request was made.

        Blurs any active field first so the frontend processes all pending event
        handlers before the submit click. Attaches listeners for all network
        responses, console errors, and page errors during the submit window.
        Runs a hit-test and logs full button DOM state before clicking.

        When DEBUG_PAUSE_BEFORE_SUBMIT=true, pauses the browser before clicking
        so the user can click manually to determine whether the form state is valid.

        Raises BrowserActionError if no mutating request is captured after the
        form closes, indicating a false-success scenario.
        """
        wait_until_has_value(
            self._locators.ai_filled_translation,
            context="AI generated translation before submit",
            timeout_ms=self._settings.default_timeout_ms,
        )

        self._blur_active_field()
        self._log_form_state_before_submit(word_text)
        self._log_submit_button_details(word_text)

        all_requests: list[dict[str, Any]] = []
        mutating_requests: list[dict[str, Any]] = []
        console_errors: list[str] = []
        page_errors: list[str] = []

        def _on_response(response: Response) -> None:
            entry: dict[str, Any] = {
                "method": response.request.method,
                "url": response.url,
                "resource_type": response.request.resource_type,
                "status": response.status,
            }
            all_requests.append(entry)
            if response.request.method not in ("POST", "PUT", "PATCH"):
                return
            body_excerpt = ""
            try:
                body_excerpt = response.text()[:200]
            except Exception:
                body_excerpt = "<unreadable>"
            mutating_entry = {**entry, "body_excerpt": body_excerpt}
            mutating_requests.append(mutating_entry)

        def _on_console(msg: ConsoleMessage) -> None:
            if msg.type == "error":
                console_errors.append(msg.text)
                log.warning("submit_console_error", word=word_text, message=msg.text)

        def _on_page_error(exc: Exception) -> None:
            page_errors.append(str(exc))
            log.warning("submit_page_error", word=word_text, error=str(exc))

        self._page.on("response", _on_response)
        self._page.on("console", _on_console)
        self._page.on("pageerror", _on_page_error)
        try:
            self._log_button_hit_test(word_text)
            if self._settings.debug_pause_before_submit:
                log.info(
                    "debug_pause_before_submit",
                    word=word_text,
                    detail=(
                        "Pausing before submit — click 'Zu meinen Wörtern hinzufügen' manually. "
                        "Network capture is active. Resume (▶) when done."
                    ),
                )
                self._page.pause()
                log.info(
                    "debug_pause_resumed",
                    word=word_text,
                    detail="Resumed after manual interaction. Skipping automatic click.",
                )
            else:
                self._execute_submit_click(word_text)
            self.wait_for_submission_completion(mutating_requests, all_requests, word_text)
        finally:
            self._page.remove_listener("response", _on_response)
            self._page.remove_listener("console", _on_console)
            self._page.remove_listener("pageerror", _on_page_error)

        for r in mutating_requests:
            status = r["status"]
            event = "submit_network_success" if 200 <= status < 300 else "submit_network_failed"
            log.info(
                event,
                method=r["method"],
                url=r["url"],
                status=status,
                body_excerpt=r["body_excerpt"],
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
        self.trigger_ai_fill(word_entry.text)
        self.wait_for_ai_completion()
        self.submit_word(word_entry.text)
        log.info("word_submit_feedback_received", word=word_entry.text)
        self.verify_word_persisted(word_entry.text)
