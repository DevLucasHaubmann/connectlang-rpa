import functools
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    target_url: str
    browser_profile_dir: Path
    words_file: Path
    headless: bool
    default_timeout_ms: int
    action_delay_ms: int
    batch_size: int
    word_language: str
    translation_language: str
    debug_pause_before_submit: bool = False
    submit_click_strategy: str = "locator"
    viewport_height: int = 1300

    @field_validator("submit_click_strategy")
    @classmethod
    def must_be_valid_strategy(cls, value: str) -> str:
        valid = {
            "locator",
            "locator_after_scroll",
            "locator_position",
            "mouse_center",
            "keyboard_space",
            "keyboard_enter",
            "js_click",
            "mouse_center_no_scroll",
        }
        if value not in valid:
            raise ValueError(f"must be one of {sorted(valid)}")
        return value

    @field_validator("target_url", "word_language", "translation_language")
    @classmethod
    def must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field must not be empty")
        return value

    @field_validator("default_timeout_ms", "batch_size")
    @classmethod
    def must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("field must be greater than 0")
        return value

    @field_validator("action_delay_ms")
    @classmethod
    def must_be_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("field must be greater than or equal to 0")
        return value


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
