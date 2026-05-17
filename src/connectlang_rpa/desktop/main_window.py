from __future__ import annotations

import contextlib
from enum import Enum, auto
from pathlib import Path

import customtkinter as ctk

from connectlang_rpa.desktop import theme
from connectlang_rpa.desktop.services.execution_summary import ExecutionSummary
from connectlang_rpa.desktop.services.log_streamer import LogStreamer
from connectlang_rpa.desktop.services.process_runner import ProcessRunner
from connectlang_rpa.desktop.widgets.word_input_panel import WordInputPanel

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_BOT_COMMAND = ["uv", "run", "connectlang-rpa"]


class AppState(Enum):
    IDLE = auto()
    EDITING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    ERROR = auto()


_STATE_LABELS: dict[AppState, str] = {
    AppState.IDLE: "Pronto",
    AppState.EDITING: "Editando lista",
    AppState.RUNNING: "Executando...",
    AppState.SUCCESS: "Concluído",
    AppState.ERROR: "Erro",
}

_STATE_COLORS: dict[AppState, str] = {
    AppState.IDLE: theme.COLOR_IDLE,
    AppState.EDITING: theme.COLOR_PROCESSING,
    AppState.RUNNING: theme.COLOR_PROCESSING,
    AppState.SUCCESS: theme.COLOR_SUCCESS,
    AppState.ERROR: theme.COLOR_ERROR,
}


class MainWindow(ctk.CTk):  # type: ignore[misc]  # CTk has no type stubs
    def __init__(self) -> None:
        super().__init__()
        self._state = AppState.IDLE
        self._runner: ProcessRunner | None = None
        self._summary = ExecutionSummary()
        self._streamer = LogStreamer(
            on_line=lambda line: self.after(0, self.append_log, line),
            on_word_update=lambda word: self.after(0, self._handle_word_update, word),
            on_progress=lambda c, t: self.after(0, self.set_progress, c, t),
            on_event=lambda parsed: self.after(0, self._summary.handle_event, parsed),
        )
        self._configure_window()
        self._build_layout()
        self._sync_initial_word_list()
        self._apply_state(self._state)

    # ------------------------------------------------------------------
    # Window configuration
    # ------------------------------------------------------------------

    def _configure_window(self) -> None:
        self.title("ConnectLang RPA Bot")
        self.geometry(f"{theme.WINDOW_DEFAULT_WIDTH}x{theme.WINDOW_DEFAULT_HEIGHT}")
        self.minsize(theme.WINDOW_MIN_WIDTH, theme.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=theme.BG_PRIMARY)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self._header = self._build_header()
        self._header.grid(row=0, column=0, columnspan=2, sticky="ew")

        self._word_panel = self._build_word_panel()
        self._word_panel.grid(
            row=1, column=0, sticky="nsew",
            padx=(theme.PAD_MD, theme.PAD_SM),
            pady=(theme.PAD_SM, theme.PAD_SM),
        )

        self._exec_panel = self._build_exec_panel()
        self._exec_panel.grid(
            row=1, column=1, sticky="nsew",
            padx=(theme.PAD_SM, theme.PAD_MD),
            pady=(theme.PAD_SM, theme.PAD_SM),
        )

        self._log_panel = self._build_log_panel()
        self._log_panel.grid(
            row=2, column=0, columnspan=2, sticky="ew",
            padx=theme.PAD_MD,
            pady=(0, theme.PAD_MD),
        )

    def _build_header(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            self,
            fg_color=theme.BG_TERTIARY,
            corner_radius=0,
            height=theme.HEADER_HEIGHT,
            border_width=0,
        )
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_propagate(False)

        title = ctk.CTkLabel(
            frame,
            text="ConnectLang RPA Bot",
            font=theme.FONT_TITLE,
            text_color=theme.TEXT_PRIMARY,
        )
        title.grid(row=0, column=0, padx=theme.PAD_LG, pady=theme.PAD_SM, sticky="w")

        status_container = ctk.CTkFrame(frame, fg_color="transparent")
        status_container.grid(
            row=0, column=1, padx=theme.PAD_LG, pady=theme.PAD_SM, sticky="e",
        )

        status_dot = ctk.CTkLabel(
            status_container,
            text="●",
            font=theme.FONT_SMALL,
            text_color=theme.COLOR_IDLE,
        )
        status_dot.grid(row=0, column=0, padx=(0, theme.PAD_XS))

        status_label = ctk.CTkLabel(
            status_container,
            text="Pronto",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_SECONDARY,
        )
        status_label.grid(row=0, column=1)

        self._header_status_dot = status_dot
        self._header_status_label = status_label

        return frame

    def _build_word_panel(self) -> WordInputPanel:
        return WordInputPanel(
            self,
            on_list_saved=self._on_word_list_saved,
            fg_color=theme.BG_SECONDARY,
            corner_radius=theme.CORNER_RADIUS,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.BORDER_COLOR,
            width=theme.WORD_PANEL_WIDTH,
        )

    def _build_exec_panel(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            self,
            fg_color=theme.BG_SECONDARY,
            corner_radius=theme.CORNER_RADIUS,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.BORDER_COLOR,
        )
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            frame,
            text="EXECUÇÃO",
            font=theme.FONT_SECTION,
            text_color=theme.TEXT_SECONDARY,
        )
        label.grid(
            row=0, column=0, padx=theme.PAD_MD,
            pady=(theme.PAD_MD, theme.PAD_SM), sticky="w",
        )

        center = ctk.CTkFrame(frame, fg_color="transparent")
        center.grid(row=1, column=0, padx=theme.PAD_MD, pady=theme.PAD_SM, sticky="nsew")
        center.grid_columnconfigure(0, weight=1)

        self._progress_bar = ctk.CTkProgressBar(
            center,
            mode="determinate",
            progress_color=theme.COLOR_PROCESSING,
            fg_color=theme.BG_INPUT,
            corner_radius=theme.CORNER_RADIUS,
            height=6,
        )
        self._progress_bar.set(0)
        self._progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, theme.PAD_XS))

        self._progress_label = ctk.CTkLabel(
            center,
            text="0 / 0 palavras",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_SECONDARY,
        )
        self._progress_label.grid(row=1, column=0, sticky="w")

        self._exec_status_label = ctk.CTkLabel(
            center,
            text="Aguardando execução",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_DISABLED,
        )
        self._exec_status_label.grid(row=2, column=0, pady=theme.PAD_LG)

        self._summary_box = ctk.CTkTextbox(
            center,
            font=theme.FONT_MONO,
            fg_color=theme.LOG_BG,
            text_color=theme.TEXT_MONO,
            border_color=theme.LOG_BORDER,
            border_width=theme.BORDER_WIDTH,
            corner_radius=theme.CORNER_RADIUS,
            state="disabled",
            wrap="none",
            height=120,
        )
        self._summary_box.grid(row=3, column=0, sticky="ew", pady=(0, theme.PAD_SM))
        self._summary_box.grid_remove()

        self._btn_run = ctk.CTkButton(
            frame,
            text="Iniciar robô",
            font=theme.FONT_SUBTITLE,
            height=theme.BUTTON_HEIGHT,
            width=theme.BUTTON_WIDTH_PRIMARY,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_PRIMARY,
            corner_radius=theme.CORNER_RADIUS,
            state="disabled",
            command=self._on_run_clicked,
        )
        self._btn_run.grid(row=2, column=0, pady=(theme.PAD_SM, theme.PAD_MD))

        return frame

    def _build_log_panel(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            self,
            fg_color=theme.BG_SECONDARY,
            corner_radius=theme.CORNER_RADIUS,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.BORDER_COLOR,
            height=theme.LOG_PANEL_HEIGHT,
        )
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_propagate(False)

        label = ctk.CTkLabel(
            frame,
            text="LOGS",
            font=theme.FONT_SECTION,
            text_color=theme.TEXT_SECONDARY,
        )
        label.grid(
            row=0, column=0, padx=theme.PAD_MD,
            pady=(theme.PAD_SM, theme.PAD_XS), sticky="w",
        )

        self._log_box = ctk.CTkTextbox(
            frame,
            font=theme.FONT_MONO,
            fg_color=theme.LOG_BG,
            text_color=theme.TEXT_MONO,
            border_color=theme.LOG_BORDER,
            border_width=theme.BORDER_WIDTH,
            corner_radius=theme.CORNER_RADIUS,
            state="disabled",
            wrap="none",
        )
        self._log_box.grid(
            row=1, column=0, sticky="nsew",
            padx=theme.PAD_MD,
            pady=(0, theme.PAD_MD),
        )

        return frame

    # ------------------------------------------------------------------
    # Word list callbacks
    # ------------------------------------------------------------------

    def _sync_initial_word_list(self) -> None:
        self._on_word_list_saved(self._word_panel.current_words)

    def _on_word_list_saved(self, words: list[str]) -> None:
        if self._state == AppState.RUNNING:
            return
        has_words = len(words) > 0
        self._btn_run.configure(state="normal" if has_words else "disabled")

    # ------------------------------------------------------------------
    # Run callbacks (called from worker thread — must use after())
    # ------------------------------------------------------------------

    def _on_run_clicked(self) -> None:
        self._streamer.reset()
        self._summary.reset()
        self._hide_summary()
        self._runner = ProcessRunner(
            command=_BOT_COMMAND,
            cwd=_PROJECT_ROOT,
            on_started=lambda: self.after(0, self._handle_started),
            on_finished=lambda code: self.after(0, self._handle_finished, code),
            on_error=lambda exc: self.after(0, self._handle_error, exc),
            on_output=self._streamer.process_line,
        )
        with contextlib.suppress(RuntimeError):
            self._runner.start()

    def _handle_started(self) -> None:
        self.set_state(AppState.RUNNING)
        self._btn_run.configure(state="disabled")
        self._word_panel.set_locked(True)
        self._exec_status_label.configure(
            text="Executando...", text_color=theme.COLOR_PROCESSING,
        )
        self._clear_log()
        self.append_log("▶ Robô iniciado.")

    def _handle_word_update(self, word: str) -> None:
        self._exec_status_label.configure(
            text=f"Processando: {word}", text_color=theme.COLOR_PROCESSING,
        )

    def _handle_finished(self, returncode: int) -> None:
        self._summary.finalize(returncode)
        if returncode == 0:
            self.set_state(AppState.SUCCESS)
            self._exec_status_label.configure(
                text=f"Concluído (código {returncode})", text_color=theme.COLOR_SUCCESS,
            )
            self.append_log(f"✔ Execução concluída com sucesso (código {returncode}).")
        else:
            self.set_state(AppState.ERROR)
            self._exec_status_label.configure(
                text=f"Erro (código {returncode})", text_color=theme.COLOR_ERROR,
            )
            self.append_log(f"✘ Execução finalizada com erro (código {returncode}).")
        self._show_summary()
        self._word_panel.set_locked(False)
        self._btn_run.configure(state="normal")

    def _handle_error(self, exc: Exception) -> None:
        self._summary.finalize(1)
        self.set_state(AppState.ERROR)
        self._exec_status_label.configure(
            text="Erro ao iniciar processo", text_color=theme.COLOR_ERROR,
        )
        self.append_log(f"✘ Falha ao iniciar robô: {exc}")
        self._show_summary()
        self._word_panel.set_locked(False)
        self._btn_run.configure(state="normal")

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def set_state(self, state: AppState) -> None:
        self._state = state
        self._apply_state(state)

    def _apply_state(self, state: AppState) -> None:
        label = _STATE_LABELS[state]
        color = _STATE_COLORS[state]
        self._header_status_dot.configure(text_color=color)
        self._header_status_label.configure(text=label)

    # ------------------------------------------------------------------
    # Public helpers (will be wired by future tasks)
    # ------------------------------------------------------------------

    def append_log(self, text: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", text + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_log(self) -> None:
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _show_summary(self) -> None:
        lines = self._summary.to_display_lines()
        self._summary_box.configure(state="normal")
        self._summary_box.delete("1.0", "end")
        self._summary_box.insert("end", "\n".join(lines))
        self._summary_box.configure(state="disabled")
        self._summary_box.grid()

    def _hide_summary(self) -> None:
        self._summary_box.grid_remove()

    def set_progress(self, current: int, total: int) -> None:
        fraction = current / total if total > 0 else 0.0
        self._progress_bar.set(fraction)
        self._progress_label.configure(text=f"{current} / {total} palavras")
