"""Widget de lista de faixas da playlist atual."""

from __future__ import annotations

import customtkinter as ctk

from ..theme import COR_ACTIVE, COR_CARD, COR_DIM, COR_HOVER, COR_TEXT
from ..utils import fmt_time


class PlaylistWidget(ctk.CTkScrollableFrame):
    def __init__(self, master, on_select, on_remove, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_select = on_select
        self.on_remove = on_remove
        self.items: list[dict] = []
        self.widgets: list[ctk.CTkFrame] = []
        self.current_index = -1

    def load(self, tracks: list[dict]) -> None:
        for widget in self.widgets:
            widget.destroy()
        self.items = list(tracks)
        self.widgets = []
        self.current_index = -1
        for idx, track in enumerate(self.items):
            self._create_item(idx, track)

    def _create_item(self, idx: int, track: dict) -> None:
        frame = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=10)
        frame.pack(fill="x", padx=6, pady=4)

        number = ctk.CTkLabel(frame, text=f"{idx + 1:02d}", font=("Courier", 12), text_color=COR_DIM, width=34)
        number.pack(side="left", padx=(10, 4), pady=10)

        info = ctk.CTkFrame(frame, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=6, pady=8)

        ctk.CTkLabel(info, text=track["title"], font=("Arial Bold", 13), text_color=COR_TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text=track["artist"], font=("Arial", 10), text_color=COR_DIM, anchor="w").pack(anchor="w")

        ctk.CTkLabel(frame, text=fmt_time(track["duration"]), font=("Courier", 11), text_color=COR_DIM, width=54).pack(side="right", padx=6)

        remove_btn = ctk.CTkButton(
            frame,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color="#311818",
            text_color="#ff6b6b",
            command=lambda i=idx: self.on_remove(i),
        )
        remove_btn.pack(side="right", padx=2, pady=8)

        for w in (frame, info, number):
            w.bind("<Button-1>", lambda e, i=idx: self.on_select(i))
        for child in info.winfo_children():
            child.bind("<Button-1>", lambda e, i=idx: self.on_select(i))

        frame.bind("<Enter>", lambda e, f=frame: f.configure(fg_color=COR_HOVER))
        frame.bind("<Leave>", lambda e, f=frame, i=idx: f.configure(fg_color=COR_ACTIVE if i == self.current_index else COR_CARD))

        self.widgets.append(frame)

    def highlight(self, idx: int) -> None:
        old = self.current_index
        self.current_index = idx
        if 0 <= old < len(self.widgets):
            self.widgets[old].configure(fg_color=COR_CARD)
        if 0 <= idx < len(self.widgets):
            self.widgets[idx].configure(fg_color=COR_ACTIVE)

    def remove_item(self, idx: int) -> None:
        # Antes: destruía só o widget removido e reindexava "na mão", mas os
        # botões/linhas restantes continuavam com o índice antigo capturado
        # na lambda de criação (on_select/on_remove ficavam errados após
        # qualquer remoção). Recriar a lista via load() garante que cada
        # widget fique com o índice correto.
        if 0 <= idx < len(self.items):
            self.items.pop(idx)
            self.load(self.items)
