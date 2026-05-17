from __future__ import annotations

from enum import Enum, auto

import customtkinter as ctk

from connectlang_rpa.desktop import theme


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
        self._configure_window()
        self._build_layout()
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

    def _build_word_panel(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            self,
            fg_color=theme.BG_SECONDARY,
            corner_radius=theme.CORNER_RADIUS,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.BORDER_COLOR,
            width=theme.WORD_PANEL_WIDTH,
        )
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_propagate(False)

        label = ctk.CTkLabel(
            frame,
            text="LISTA DE PALAVRAS",
            font=theme.FONT_SECTION,
            text_color=theme.TEXT_SECONDARY,
        )
        label.grid(
            row=0, column=0, padx=theme.PAD_MD,
            pady=(theme.PAD_MD, theme.PAD_SM), sticky="w",
        )

        placeholder = ctk.CTkLabel(
            frame,
            text="Editor de palavras\n(Task 12.3)",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_DISABLED,
        )
        placeholder.grid(row=1, column=0, padx=theme.PAD_MD, pady=theme.PAD_MD)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(
            row=2, column=0, padx=theme.PAD_MD,
            pady=(theme.PAD_SM, theme.PAD_MD), sticky="ew",
        )
        btn_frame.grid_columnconfigure(0, weight=1)

        self._btn_clear = ctk.CTkButton(
            btn_frame,
            text="Limpar lista",
            font=theme.FONT_BODY,
            height=theme.BUTTON_HEIGHT,
            fg_color=theme.BG_INPUT,
            hover_color=theme.BG_HOVER,
            text_color=theme.TEXT_SECONDARY,
            corner_radius=theme.CORNER_RADIUS,
            border_width=theme.BORDER_WIDTH,
            border_color=theme.BORDER_COLOR,
            state="disabled",
        )
        self._btn_clear.grid(row=0, column=0, sticky="ew")

        return frame

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

        placeholder = ctk.CTkLabel(
            center,
            text="Painel de execução\n(Task 12.4)",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_DISABLED,
        )
        placeholder.grid(row=2, column=0, pady=theme.PAD_LG)

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

    def set_progress(self, current: int, total: int) -> None:
        fraction = current / total if total > 0 else 0.0
        self._progress_bar.set(fraction)
        self._progress_label.configure(text=f"{current} / {total} palavras")
