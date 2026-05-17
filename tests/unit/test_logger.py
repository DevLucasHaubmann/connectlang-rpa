from __future__ import annotations

import json

import pytest
import structlog

from connectlang_rpa.utils.logger import configure_logging


class TestConfigureLogging:
    def test_configure_logging_does_not_raise(self) -> None:
        configure_logging()

    def test_json_renderer_is_in_processor_chain(self) -> None:
        configure_logging()
        config = structlog.get_config()
        processor_types = [type(p).__name__ for p in config["processors"]]
        assert "JSONRenderer" in processor_types

    def test_timestamper_is_in_processor_chain(self) -> None:
        configure_logging()
        config = structlog.get_config()
        processor_types = [type(p).__name__ for p in config["processors"]]
        assert "TimeStamper" in processor_types

    def test_log_output_is_valid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        configure_logging()
        log = structlog.get_logger("test")
        log.info("test_event", word="Termin")
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["event"] == "test_event"
        assert parsed["word"] == "Termin"
        assert "timestamp" in parsed
        assert "level" in parsed
