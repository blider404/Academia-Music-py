"""Janela de configurações (biblioteca, alarme, auto-importação, volume)."""

from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from ..config import ConfigManager
from ..theme import COR_CARD, COR_CARD_2, COR_DIM, COR_GREEN, COR_GREEN_DARK, COR_HOVER, COR_PANEL, COR_TEXT, DEFAULT_ALARM_FILE
from ..utils import safe_int


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, config: ConfigManager, on_save):
        super().__init__(master)
        self.config = config
        self.on_save = on_save
        self.title("⚙️ Configurações")
        self.geometry("620x640")
        self.resizable(False, False)
        self.configure(fg_color=COR_PANEL)
        self.grab_set()
        self._build_ui()
        self._fill_values()

    def _build_ui(self):
        ctk.CTkLabel(self, text="⚙️ CONFIGURAÇÕES", font=("Arial Black", 20), text_color=COR_GREEN).pack(pady=(18, 0))
        ctk.CTkLabel(self, text="Ajuste a biblioteca, o alarme e o comportamento do player.", font=("Arial", 12), text_color=COR_DIM).pack(pady=(0, 14))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        def section(title: str):
            ctk.CTkLabel(self.scroll, text=title, font=("Arial Bold", 14), text_color=COR_GREEN).pack(anchor="w", padx=8, pady=(14, 6))

        def row(label: str, widget_factory, **kwargs):
            frame = ctk.CTkFrame(self.scroll, fg_color=COR_CARD, corner_radius=10)
            frame.pack(fill="x", padx=4, pady=4)
            ctk.CTkLabel(frame, text=label, font=("Arial", 12), text_color=COR_TEXT, width=220, anchor="w").pack(side="left", padx=12, pady=10)
            widget = widget_factory(frame, **kwargs)
            widget.pack(side="right", padx=12, pady=8)
            return widget

        section("Biblioteca")
        self.entry_root = row("Pasta raiz das músicas", lambda p: ctk.CTkEntry(p, width=240, placeholder_text="Selecione a pasta"))
        ctk.CTkButton(self.scroll, text="📂 Escolher pasta de músicas", fg_color=COR_CARD_2, hover_color=COR_HOVER, command=self._choose_root).pack(fill="x", padx=4, pady=(2, 8))

        self.entry_downloads = row("Pasta de downloads", lambda p: ctk.CTkEntry(p, width=240, placeholder_text="Opcional"))
        ctk.CTkButton(self.scroll, text="📂 Escolher pasta de downloads", fg_color=COR_CARD_2, hover_color=COR_HOVER, command=self._choose_downloads).pack(fill="x", padx=4, pady=(2, 8))

        section("Alarme")
        self.entry_alarm = row("Arquivo de alarme (MP3/WAV)", lambda p: ctk.CTkEntry(p, width=240, placeholder_text="alarme.mp3"))
        ctk.CTkButton(self.scroll, text="🎵 Escolher arquivo de alarme", fg_color=COR_CARD_2, hover_color=COR_HOVER, command=self._choose_alarm).pack(fill="x", padx=4, pady=(2, 8))

        self.switch_alarm = row("Ativar alarme", lambda p: ctk.CTkSwitch(p, text="", progress_color=COR_GREEN))
        self.entry_close = row("Horário de fechamento (HH:MM)", lambda p: ctk.CTkEntry(p, width=120, placeholder_text="22:00"))
        self.entry_warn = row("Aviso antecipado (minutos)", lambda p: ctk.CTkEntry(p, width=120, placeholder_text="10"))
        self.switch_auto = row("Auto-importar downloads", lambda p: ctk.CTkSwitch(p, text="", progress_color=COR_GREEN))
        self.entry_auto_time = row("Horário auto-importação (HH:MM)", lambda p: ctk.CTkEntry(p, width=120, placeholder_text="06:00"))
        self.entry_volume = row("Volume inicial (0 a 100)", lambda p: ctk.CTkSlider(p, from_=0, to=100, width=220, progress_color=COR_GREEN, button_color=COR_GREEN))
        self.lbl_volume = ctk.CTkLabel(self.scroll, text="", font=("Courier", 11), text_color=COR_DIM)
        self.lbl_volume.pack(anchor="e", padx=10, pady=(0, 6))
        self.entry_volume.configure(command=lambda v: self.lbl_volume.configure(text=f"{int(v)}%"))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(footer, text="💾 Salvar", height=44, fg_color=COR_GREEN, hover_color=COR_GREEN_DARK, text_color="#000", font=("Arial Bold", 14), command=self._save).pack(side="right", padx=4)
        ctk.CTkButton(footer, text="Cancelar", height=44, fg_color=COR_CARD_2, hover_color=COR_HOVER, command=self.destroy).pack(side="right", padx=6)

    def _fill_values(self):
        cfg = self.config.data
        self.entry_root.insert(0, cfg.pasta_raiz)
        self.entry_downloads.insert(0, cfg.pasta_downloads)
        self.entry_alarm.insert(0, cfg.arquivo_alarme)
        self.switch_alarm.select() if cfg.alarme_ativo else self.switch_alarm.deselect()
        self.entry_close.insert(0, cfg.horario_fechamento)
        self.entry_warn.insert(0, str(cfg.aviso_minutos))
        self.switch_auto.select() if cfg.auto_import_ativo else self.switch_auto.deselect()
        self.entry_auto_time.insert(0, cfg.auto_import_horario)
        self.entry_volume.set(cfg.volume)
        self.lbl_volume.configure(text=f"{cfg.volume}%")

    def _choose_root(self):
        p = filedialog.askdirectory(title="Selecione a pasta raiz das músicas")
        if p:
            self.entry_root.delete(0, "end")
            self.entry_root.insert(0, p)

    def _choose_downloads(self):
        p = filedialog.askdirectory(title="Selecione a pasta de downloads")
        if p:
            self.entry_downloads.delete(0, "end")
            self.entry_downloads.insert(0, p)

    def _choose_alarm(self):
        p = filedialog.askopenfilename(
            title="Selecione o arquivo do alarme",
            filetypes=[("Áudio", "*.mp3 *.wav *.ogg *.flac"), ("Todos", "*.*")],
        )
        if p:
            self.entry_alarm.delete(0, "end")
            self.entry_alarm.insert(0, p)

    def _save(self):
        cfg = self.config.data
        cfg.pasta_raiz = self.entry_root.get().strip()
        cfg.pasta_downloads = self.entry_downloads.get().strip()
        cfg.arquivo_alarme = self.entry_alarm.get().strip() or str(DEFAULT_ALARM_FILE)
        cfg.alarme_ativo = bool(self.switch_alarm.get())
        cfg.horario_fechamento = self.entry_close.get().strip() or "22:00"
        cfg.aviso_minutos = safe_int(self.entry_warn.get().strip(), 10)
        cfg.auto_import_ativo = bool(self.switch_auto.get())
        cfg.auto_import_horario = self.entry_auto_time.get().strip() or "06:00"
        cfg.volume = int(float(self.entry_volume.get()))
        self.config.save()
        self.on_save()
        self.destroy()
