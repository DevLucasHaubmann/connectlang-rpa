from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from connectlang_rpa.desktop.services.process_runner import ProcessRunner

_CWD = Path()


def _make_runner(**kwargs: object) -> ProcessRunner:
    return ProcessRunner(command=["echo", "test"], cwd=_CWD, **kwargs)


def _wait(condition: threading.Event, timeout: float = 2.0) -> None:
    assert condition.wait(timeout), "Timed out waiting for condition."


# ------------------------------------------------------------------
# Initial state
# ------------------------------------------------------------------


def test_process_runner_initial_state_not_running() -> None:
    runner = _make_runner()
    assert not runner.is_running()


# ------------------------------------------------------------------
# start() transitions to running
# ------------------------------------------------------------------


def test_process_runner_start_sets_running_state() -> None:
    started = threading.Event()
    finished = threading.Event()

    fake_process = MagicMock()
    fake_process.stdout = iter(["line1\n"])
    fake_process.wait.side_effect = finished.wait
    fake_process.returncode = 0

    with patch("subprocess.Popen", return_value=fake_process):
        runner = ProcessRunner(
            command=["uv", "run", "connectlang-rpa"],
            cwd=_CWD,
            on_started=started.set,
        )
        runner.start()
        _wait(started)
        assert runner.is_running()

    finished.set()


# ------------------------------------------------------------------
# Prevent duplicate start
# ------------------------------------------------------------------


def test_process_runner_raises_on_duplicate_start() -> None:
    started = threading.Event()
    finished = threading.Event()

    fake_process = MagicMock()
    fake_process.stdout = iter([])
    fake_process.wait.side_effect = finished.wait
    fake_process.returncode = 0

    with patch("subprocess.Popen", return_value=fake_process):
        runner = ProcessRunner(
            command=["uv", "run", "connectlang-rpa"],
            cwd=_CWD,
            on_started=started.set,
        )
        runner.start()
        _wait(started)

        with pytest.raises(RuntimeError, match="already running"):
            runner.start()

    finished.set()


# ------------------------------------------------------------------
# on_finished with exit code 0
# ------------------------------------------------------------------


def test_process_runner_calls_on_finished_with_success_code() -> None:
    done = threading.Event()
    received_code: list[int] = []

    fake_process = MagicMock()
    fake_process.stdout = iter([])
    fake_process.returncode = 0
    fake_process.wait.return_value = None

    def on_finished(code: int) -> None:
        received_code.append(code)
        done.set()

    with patch("subprocess.Popen", return_value=fake_process):
        runner = ProcessRunner(
            command=["echo", "ok"],
            cwd=_CWD,
            on_finished=on_finished,
        )
        runner.start()
        _wait(done)

    assert received_code == [0]
    assert not runner.is_running()


# ------------------------------------------------------------------
# on_finished with non-zero exit code
# ------------------------------------------------------------------


def test_process_runner_calls_on_finished_with_error_code() -> None:
    done = threading.Event()
    received_code: list[int] = []

    fake_process = MagicMock()
    fake_process.stdout = iter([])
    fake_process.returncode = 1
    fake_process.wait.return_value = None

    def on_finished(code: int) -> None:
        received_code.append(code)
        done.set()

    with patch("subprocess.Popen", return_value=fake_process):
        runner = ProcessRunner(
            command=["false"],
            cwd=_CWD,
            on_finished=on_finished,
        )
        runner.start()
        _wait(done)

    assert received_code == [1]
    assert not runner.is_running()


# ------------------------------------------------------------------
# on_error when Popen raises
# ------------------------------------------------------------------


def test_process_runner_calls_on_error_when_popen_fails() -> None:
    done = threading.Event()
    errors: list[Exception] = []

    def on_error(exc: Exception) -> None:
        errors.append(exc)
        done.set()

    with patch("subprocess.Popen", side_effect=FileNotFoundError("uv not found")):
        runner = ProcessRunner(
            command=["uv", "run", "connectlang-rpa"],
            cwd=_CWD,
            on_error=on_error,
        )
        runner.start()
        _wait(done)

    assert len(errors) == 1
    assert isinstance(errors[0], FileNotFoundError)
    assert not runner.is_running()


# ------------------------------------------------------------------
# No Playwright or browser involved
# ------------------------------------------------------------------


def test_process_runner_does_not_import_playwright() -> None:
    import inspect

    import connectlang_rpa.desktop.services.process_runner as pr_module

    source = inspect.getsource(pr_module)
    assert "playwright" not in source, "process_runner must not import Playwright."
