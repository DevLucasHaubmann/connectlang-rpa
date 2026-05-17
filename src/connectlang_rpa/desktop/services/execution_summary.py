from __future__ import annotations

from dataclasses import dataclass, field

from connectlang_rpa.desktop.services.log_streamer import ParsedLogLine

_STATUS_SUCCESS = "SUCESSO"
_STATUS_ERROR = "ERRO"
_STATUS_RUNNING = "EM EXECUÇÃO"
_STATUS_IDLE = "AGUARDANDO"


@dataclass
class ExecutionSummary:
    """Aggregates bot execution metrics from structured log events.

    Designed to be fed via handle_event() as lines are parsed by LogStreamer.
    Call finalize() when the process exits, then to_display_lines() to render.
    """

    total: int = 0
    successes: int = 0
    failures: int = 0
    exit_code: int | None = None
    screenshots: list[str] = field(default_factory=list)
    _finalized: bool = field(default=False, repr=False)

    def reset(self) -> None:
        self.total = 0
        self.successes = 0
        self.failures = 0
        self.exit_code = None
        self.screenshots = []
        self._finalized = False

    def handle_event(self, parsed: ParsedLogLine) -> None:
        event = parsed.event
        if event == "execution_started" and parsed.total is not None:
            self.total = parsed.total
        elif event == "word_added_successfully":
            self.successes += 1
        elif event == "word_failed":
            self.failures += 1
        elif event == "screenshot_saved" and parsed.path:
            self.screenshots.append(parsed.path)

    def finalize(self, exit_code: int) -> None:
        self.exit_code = exit_code
        self._finalized = True

    @property
    def is_finalized(self) -> bool:
        return self._finalized

    @property
    def status_text(self) -> str:
        if not self._finalized:
            return _STATUS_RUNNING if self.total > 0 or self.successes > 0 else _STATUS_IDLE
        return _STATUS_SUCCESS if self.exit_code == 0 else _STATUS_ERROR

    def to_display_lines(self) -> list[str]:
        if not self._finalized:
            return []

        lines: list[str] = [
            "─" * 32,
            f"  Status:    {self.status_text}",
            f"  Total:     {self.total}",
            f"  Sucesso:   {self.successes}",
            f"  Falhas:    {self.failures}",
            f"  Cód. saída: {self.exit_code}",
        ]

        if self.failures > 0:
            lines.append("  ⚠ Detalhes das falhas estão nos logs.")

        for path in self.screenshots:
            lines.append(f"  📸 {path}")

        lines.append("─" * 32)
        return lines
