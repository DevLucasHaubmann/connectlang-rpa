from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog


def build_run_log_path() -> Path:
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d_%H-%M-%S")
    base = Path("logs") / f"run_{timestamp}.jsonl"
    if not base.exists():
        return base
    counter = 1
    while True:
        candidate = Path("logs") / f"run_{timestamp}_{counter}.jsonl"
        if not candidate.exists():
            return candidate
        counter += 1


class _FileWriterProcessor:
    """Writes each rendered JSON line to a file, then passes the event through."""

    def __init__(self, file_handle: io.TextIOWrapper) -> None:
        self._file = file_handle

    def __call__(
        self,
        logger: Any,
        method: str,
        event_dict: dict[str, Any],
    ) -> dict[str, Any]:
        rendered = structlog.processors.JSONRenderer()(logger, method, event_dict.copy())
        line = rendered if isinstance(rendered, str) else rendered.decode("utf-8")
        self._file.write(line + "\n")
        self._file.flush()
        return event_dict


def configure_logging(log_file: Path | None = None) -> None:
    processors: list[Any] = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.ExceptionRenderer(),
    ]

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handle = log_file.open("x", encoding="utf-8")
        processors.append(_FileWriterProcessor(file_handle))

    processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
