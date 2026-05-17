from __future__ import annotations

import re
from pathlib import Path

from connectlang_rpa.utils.screenshots import build_screenshot_path, sanitize_filename


class TestSanitizeFilename:
    def test_plain_word_unchanged(self) -> None:
        assert sanitize_filename("Termin") == "Termin"

    def test_spaces_replaced_with_underscores(self) -> None:
        assert sanitize_filename("der Termin") == "der_Termin"

    def test_multiple_spaces_collapse(self) -> None:
        assert sanitize_filename("der  Termin") == "der_Termin"

    def test_slash_replaced(self) -> None:
        assert sanitize_filename("a/b") == "a_b"

    def test_special_chars_replaced(self) -> None:
        result = sanitize_filename("über:sich")
        assert "/" not in result
        assert ":" not in result

    def test_leading_trailing_underscores_stripped(self) -> None:
        assert sanitize_filename(" word ") == "word"

    def test_empty_string_returns_empty(self) -> None:
        assert sanitize_filename("") == ""


class TestBuildScreenshotPath:
    def test_returns_path_inside_screenshots_dir(self) -> None:
        path = build_screenshot_path("Termin")
        assert path.parts[0] == "screenshots"

    def test_filename_starts_with_error_prefix(self) -> None:
        path = build_screenshot_path("Termin")
        assert path.name.startswith("error_")

    def test_filename_ends_with_png(self) -> None:
        path = build_screenshot_path("Termin")
        assert path.suffix == ".png"

    def test_filename_contains_sanitized_word(self) -> None:
        path = build_screenshot_path("der Termin")
        assert "der_Termin" in path.name

    def test_filename_contains_timestamp_pattern(self) -> None:
        path = build_screenshot_path("word")
        assert re.search(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}", path.name)

    def test_returns_path_object(self) -> None:
        assert isinstance(build_screenshot_path("word"), Path)
