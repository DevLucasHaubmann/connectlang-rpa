from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable
from pathlib import Path


class ProcessRunner:
    """Runs the RPA bot as a subprocess on a background thread.

    Callbacks are invoked from the worker thread — callers must marshal to
    the UI thread themselves (e.g. ``widget.after(0, callback)``).
    """

    def __init__(
        self,
        command: list[str],
        cwd: Path,
        on_started: Callable[[], None] | None = None,
        on_finished: Callable[[int], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        on_output: Callable[[str], None] | None = None,
    ) -> None:
        self._command = command
        self._cwd = cwd
        self._on_started = on_started
        self._on_finished = on_finished
        self._on_error = on_error
        self._on_output = on_output
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the process. Raises RuntimeError if already running."""
        with self._lock:
            if self._running:
                raise RuntimeError("Process is already running.")
            self._running = True

        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self) -> None:
        try:
            process = subprocess.Popen(
                self._command,
                cwd=self._cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            with self._lock:
                self._running = False
            if self._on_error:
                self._on_error(exc)
            return

        with self._lock:
            self._process = process

        if self._on_started:
            self._on_started()

        self._drain_output(process)
        process.wait()

        with self._lock:
            self._running = False

        if self._on_finished:
            self._on_finished(process.returncode)

    def _drain_output(self, process: subprocess.Popen[str]) -> None:
        if process.stdout is None:
            return
        for line in process.stdout:
            if self._on_output:
                self._on_output(line.rstrip("\n"))
