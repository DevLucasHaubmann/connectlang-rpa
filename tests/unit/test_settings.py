from __future__ import annotations

import pytest
from pydantic import ValidationError

from connectlang_rpa.config.settings import Settings

_VALID_ENV: dict[str, str] = {
    "TARGET_URL": "https://example.com",
    "BROWSER_PROFILE_DIR": "/tmp/profile",
    "WORDS_FILE": "/tmp/words.json",
    "HEADLESS": "true",
    "DEFAULT_TIMEOUT_MS": "5000",
    "ACTION_DELAY_MS": "0",
    "BATCH_SIZE": "10",
    "WORD_LANGUAGE": "de",
    "TRANSLATION_LANGUAGE": "en",
}


def _make_settings(
    overrides: dict[str, str] | None = None,
    monkeypatch: pytest.MonkeyPatch | None = None,
) -> Settings:
    env = {**_VALID_ENV, **(overrides or {})}
    if monkeypatch is not None:
        for key, value in env.items():
            monkeypatch.setenv(key, value)
    return Settings(**{k.lower(): v for k, v in env.items()})  # type: ignore[arg-type]


class TestSettingsValid:
    def test_resolves_path_fields(self) -> None:
        from pathlib import Path

        s = _make_settings()
        assert isinstance(s.browser_profile_dir, Path)
        assert isinstance(s.words_file, Path)

    def test_parses_bool_headless(self) -> None:
        s = _make_settings()
        assert s.headless is True

    def test_parses_int_fields(self) -> None:
        s = _make_settings()
        assert s.default_timeout_ms == 5000
        assert s.batch_size == 10
        assert s.action_delay_ms == 0

    def test_action_delay_zero_is_valid(self) -> None:
        s = _make_settings({"ACTION_DELAY_MS": "0"})
        assert s.action_delay_ms == 0


class TestSettingsValidation:
    def test_rejects_empty_target_url(self) -> None:
        with pytest.raises(ValidationError, match="empty"):
            _make_settings({"TARGET_URL": "   "})

    def test_rejects_empty_word_language(self) -> None:
        with pytest.raises(ValidationError, match="empty"):
            _make_settings({"WORD_LANGUAGE": ""})

    def test_rejects_empty_translation_language(self) -> None:
        with pytest.raises(ValidationError, match="empty"):
            _make_settings({"TRANSLATION_LANGUAGE": "  "})

    def test_rejects_zero_default_timeout_ms(self) -> None:
        with pytest.raises(ValidationError, match="greater than 0"):
            _make_settings({"DEFAULT_TIMEOUT_MS": "0"})

    def test_rejects_negative_default_timeout_ms(self) -> None:
        with pytest.raises(ValidationError, match="greater than 0"):
            _make_settings({"DEFAULT_TIMEOUT_MS": "-1"})

    def test_rejects_zero_batch_size(self) -> None:
        with pytest.raises(ValidationError, match="greater than 0"):
            _make_settings({"BATCH_SIZE": "0"})

    def test_rejects_negative_action_delay_ms(self) -> None:
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            _make_settings({"ACTION_DELAY_MS": "-1"})
