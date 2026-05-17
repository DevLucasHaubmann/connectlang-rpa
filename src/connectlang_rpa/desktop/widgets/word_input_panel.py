from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk

from connectlang_rpa.desktop import theme
from connectlang_rpa.desktop.services import desktop_word_service as svc


class WordInputPanel(ctk.CTkFrame):  # type: ignore[misc]
    """Left panel: word list editor with save/clear and word counter."""

    def __init__(
        self,
        master: ctk.CTk,
        on_list_saved: Callable[[list[str]], None],
        words_path: Path = svc.WORDS_FILE,
        **kwargs: object,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_list_saved = on_list_saved
        self._words_path = words_path
        self._build()
        self._load_existing()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        section_label = ctk.CTkLabel(
            self,
            text="LISTA DE PALAVRAS",
            font=theme.FONT_SECTION,
            text_color=theme.TEXT_SECONDARY,
        )
        section_label.grid(
            row=0,
            column=0,
            padx=theme.PAD_MD,
            pady=(theme.PAD_MD, theme.PAD_SM),
            sticky="w",
        )

        self._textbox = ctk.CTkTextbox(
            self,
            font=theme.FONT_BODY,
            fg_color=theme.BG_INPUT,
            text_color=theme.TEXT_PRIMARY,
            border_color=theme.BORDER_COLOR,
            border_width=theme.BORDER_WIDTH,
            corner_radius=theme.CORNER_RADIUS,
            wrap="none",
        )
        self._textbox.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=theme.PAD_MD,
            pady=(0, theme.PAD_SM),
        )
        self._textbox.bind("<KeyRelease>", self._on_text_change)

        self._counter_label = ctk.CTkLabel(
            self,
            text="0 palavras",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_SECONDARY,
        )
        self._counter_label.grid(
            row=2,
            column=0,
            padx=theme.PAD_MD,
            sticky="w",
        )

        self._feedback_label = ctk.CTkLabel(
            self,
            text="",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_SECONDARY,
        )
        self._feedback_label.grid(
            row=3,
            column=0,
            padx=theme.PAD_MD,
            pady=(theme.PAD_XS, 0),
            sticky="w",
        )

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(
            row=4,
            column=0,
            padx=theme.PAD_MD,
            pady=(theme.PAD_SM, theme.PAD_MD),
            sticky="ew",
        )
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self._btn_save = ctk.CTkButton(
            btn_frame,
            text="Salvar lista",
            font=theme.FONT_BODY,
            height=theme.BUTTON_HEIGHT,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            text_color=theme.TEXT_PRIMARY,
            corner_radius=theme.CORNER_RADIUS,
            command=self._on_save,
        )
        self._btn_save.grid(row=0, column=0, sticky="ew", padx=(0, theme.PAD_XS))

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
            command=self._on_clear,
        )
        self._btn_clear.grid(row=0, column=1, sticky="ew", padx=(theme.PAD_XS, 0))

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_text_change(self, _event: object = None) -> None:
        words = svc.parse_lines(self._textbox.get("1.0", "end"))
        count = len(words)
        self._counter_label.configure(text=f"{count} palavra{'s' if count != 1 else ''}")
        self._btn_clear.configure(state="normal" if count else "disabled")
        self._feedback_label.configure(text="", text_color=theme.TEXT_SECONDARY)

    def _on_save(self) -> None:
        raw = self._textbox.get("1.0", "end")
        words = svc.parse_lines(raw)

        if not words:
            self._show_feedback("Lista vazia — adicione pelo menos uma palavra.", theme.COLOR_ERROR)
            return

        original_line_count = len([ln for ln in raw.splitlines() if ln.strip()])

        try:
            svc.save_words(words, self._words_path)
        except OSError as exc:
            self._show_feedback(f"Erro ao salvar: {exc}", theme.COLOR_ERROR)
            return

        self._rewrite_textbox(words)
        self._on_list_saved(words)

        removed = original_line_count - len(words)
        if removed > 0:
            msg = f"Lista salva. {removed} linha(s) removida(s) (duplicatas)."
        else:
            msg = "Lista salva com sucesso."
        self._show_feedback(msg, theme.COLOR_SUCCESS)

    def _on_clear(self) -> None:
        self._textbox.delete("1.0", "end")
        self._counter_label.configure(text="0 palavras")
        self._btn_clear.configure(state="disabled")
        self._show_feedback("Lista limpa.", theme.TEXT_SECONDARY)
        self._on_list_saved([])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _show_feedback(self, message: str, color: str) -> None:
        self._feedback_label.configure(text=message, text_color=color)

    def _rewrite_textbox(self, words: list[str]) -> None:
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", "\n".join(words))
        self._counter_label.configure(
            text=f"{len(words)} palavra{'s' if len(words) != 1 else ''}",
        )

    def set_locked(self, locked: bool) -> None:
        """Disable or re-enable editing controls during robot execution."""
        state = "disabled" if locked else "normal"
        self._btn_save.configure(state=state)
        self._textbox.configure(state=state)
        if not locked:
            # restore clear button only when there is content
            raw = self._textbox.get("1.0", "end")
            words = svc.parse_lines(raw)
            self._btn_clear.configure(state="normal" if words else "disabled")
        else:
            self._btn_clear.configure(state="disabled")

    @property
    def current_words(self) -> list[str]:
        return svc.parse_lines(self._textbox.get("1.0", "end"))

    def _load_existing(self) -> None:
        words = svc.load_words(self._words_path)
        if not words:
            return
        self._rewrite_textbox(words)
        self._btn_clear.configure(state="normal")
        msg = f"{len(words)} palavra(s) carregada(s) do arquivo."
        self._show_feedback(msg, theme.TEXT_SECONDARY)
