"""Janela principal: monta a UI e orquestra config/áudio/biblioteca."""

from __future__ import annotations

import random
import threading
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

import customtkinter as ctk
from PIL import Image, ImageDraw
from tkinter import messagebox

from ..audio import AudioManager
from ..config import ConfigManager
from ..library import Library
from ..theme import (
    APP_MIN_SIZE,
    APP_SIZE,
    APP_TITLE,
    COR_ACTIVE,
    COR_BG,
    COR_BORDER,
    COR_CARD,
    COR_DIM,
    COR_GREEN,
    COR_GREEN_DARK,
    COR_HOVER,
    COR_ORANGE,
    COR_PANEL,
    COR_TEXT,
)
from ..utils import fmt_time, make_round_cover
from .playlist_widget import PlaylistWidget
from .settings_window import SettingsWindow


class AcademiaPlayer(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.config_mgr = ConfigManager()
        self.audio = AudioManager()
        self.library = Library(self.config_mgr.data.pasta_raiz)

        self.playlist: list[dict] = []
        self.current_index = -1
        self.current_album_index = -1
        self.shuffle = self.config_mgr.data.shuffle
        self.repeat = self.config_mgr.data.repeat
        self.dragging_slider = False
        self.alarm_triggered = False
        self.last_auto_import_day: Optional[str] = None
        self._cover_ref = None

        self.title(APP_TITLE)
        self.geometry(APP_SIZE)
        self.minsize(*APP_MIN_SIZE)
        self.configure(fg_color=COR_BG)

        if self.config_mgr.data.janela_maximizada:
            self.after(100, lambda: self.state("zoomed"))

        self._build_ui()
        self._refresh_album_list()
        self._restore_session()
        self._sync_volume()
        self._start_loop()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------------------------------------------------------------
    # UI
    # ---------------------------------------------------------------------

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, fg_color=COR_PANEL, height=92, corner_radius=0)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        left_logo = ctk.CTkLabel(self.header, text="🏋️", font=("Arial", 34))
        left_logo.pack(side="left", padx=(18, 10), pady=10)

        info = ctk.CTkFrame(self.header, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)

        self.lbl_title = ctk.CTkLabel(info, text="Academia Music py", font=("Arial Black", 18), text_color=COR_TEXT, anchor="w")
        self.lbl_title.pack(anchor="w", padx=4, pady=(14, 0))
        self.lbl_artist = ctk.CTkLabel(info, text="Selecione um álbum para começar", font=("Arial", 12), text_color=COR_DIM, anchor="w")
        self.lbl_artist.pack(anchor="w", padx=4)

        self.canvas_cover = ctk.CTkFrame(self.header, fg_color="transparent")
        self.canvas_cover.pack(side="right", padx=16, pady=8)
        self._show_default_cover()

        actions = ctk.CTkFrame(self.header, fg_color="transparent")
        actions.pack(side="right", padx=8)

        ctk.CTkButton(actions, text="⚙️", width=44, height=44, fg_color=COR_CARD, hover_color=COR_HOVER, font=("Arial", 18), command=self._open_settings).pack(pady=4)
        ctk.CTkButton(actions, text="⛶", width=44, height=44, fg_color=COR_CARD, hover_color=COR_HOVER, font=("Arial", 16), command=self._toggle_fullscreen).pack(pady=2)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar de álbuns
        self.albums_panel = ctk.CTkFrame(body, fg_color=COR_PANEL, width=250, corner_radius=0)
        self.albums_panel.pack(side="left", fill="y")
        self.albums_panel.pack_propagate(False)

        ctk.CTkLabel(self.albums_panel, text="ÁLBUNS", font=("Arial Black", 11), text_color=COR_GREEN).pack(anchor="w", padx=14, pady=(12, 4))

        ctk.CTkButton(
            self.albums_panel,
            text="⬇️ Importar downloads",
            height=34,
            fg_color=COR_CARD,
            hover_color=COR_HOVER,
            command=self._import_downloads,
        ).pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(
            self.albums_panel,
            text="🔄 Atualizar biblioteca",
            height=34,
            fg_color=COR_CARD,
            hover_color=COR_HOVER,
            command=self._reload_library,
        ).pack(fill="x", padx=10, pady=(0, 8))

        self.album_scroll = ctk.CTkScrollableFrame(self.albums_panel, fg_color="transparent")
        self.album_scroll.pack(fill="both", expand=True)

        ctk.CTkFrame(body, fg_color=COR_BORDER, width=1).pack(side="left", fill="y")

        # Área principal
        main = ctk.CTkFrame(body, fg_color="transparent")
        main.pack(side="left", fill="both", expand=True)

        top = ctk.CTkFrame(main, fg_color=COR_PANEL, height=44)
        top.pack(fill="x")
        top.pack_propagate(False)

        self.lbl_album_name = ctk.CTkLabel(top, text="Playlist", font=("Arial Bold", 13), text_color=COR_TEXT)
        self.lbl_album_name.pack(side="left", padx=16, pady=10)

        ctk.CTkButton(top, text="▶ Tocar tudo", width=110, height=30, fg_color=COR_GREEN, hover_color=COR_GREEN_DARK, font=("Arial Bold", 11), command=self._play_all).pack(side="right", padx=8, pady=7)
        ctk.CTkButton(top, text="🔀 Embaralhar", width=110, height=30, fg_color=COR_CARD, hover_color=COR_HOVER, font=("Arial", 11), command=self._shuffle_playlist).pack(side="right", padx=4, pady=7)

        self.playlist_widget = PlaylistWidget(main, on_select=self._play_index, on_remove=self._remove_playlist_item)
        self.playlist_widget.pack(fill="both", expand=True, padx=8, pady=4)

        self._build_controls()

    def _build_controls(self):
        controls = ctk.CTkFrame(self, fg_color=COR_PANEL, height=150, corner_radius=0)
        controls.pack(fill="x", side="bottom")
        controls.pack_propagate(False)

        progress_row = ctk.CTkFrame(controls, fg_color="transparent")
        progress_row.pack(fill="x", padx=20, pady=(12, 0))

        self.lbl_pos = ctk.CTkLabel(progress_row, text="0:00", font=("Courier", 11), text_color=COR_DIM, width=48)
        self.lbl_pos.pack(side="left")

        self.slider_progress = ctk.CTkSlider(
            progress_row,
            from_=0,
            to=100,
            fg_color=COR_BORDER,
            progress_color=COR_GREEN,
            button_color=COR_GREEN,
            button_hover_color="#3cff88",
            command=self._on_slider_move,
        )
        self.slider_progress.pack(side="left", fill="x", expand=True, padx=12)
        self.slider_progress.set(0)
        self.slider_progress.bind("<ButtonPress-1>", lambda e: self._start_drag())
        self.slider_progress.bind("<ButtonRelease-1>", lambda e: self._end_drag())

        self.lbl_dur = ctk.CTkLabel(progress_row, text="0:00", font=("Courier", 11), text_color=COR_DIM, width=48)
        self.lbl_dur.pack(side="left")

        btn_row = ctk.CTkFrame(controls, fg_color="transparent")
        btn_row.pack(pady=8)

        def make_btn(text, cmd, w=58, h=48, color=COR_CARD, font_size=18):
            return ctk.CTkButton(btn_row, text=text, width=w, height=h, fg_color=color, hover_color=COR_HOVER, font=("Arial", font_size), command=cmd)

        self.btn_shuffle = make_btn("🔀", self._toggle_shuffle, w=52, h=44, font_size=16)
        self.btn_shuffle.pack(side="left", padx=4)
        make_btn("⏮", self._prev_track, w=52, h=52).pack(side="left", padx=4)

        self.btn_play = make_btn("▶", self._toggle_play, w=70, h=60, color=COR_GREEN, font_size=24)
        self.btn_play.pack(side="left", padx=6)

        make_btn("⏭", self._next_track, w=52, h=52).pack(side="left", padx=4)
        self.btn_repeat = make_btn("🔁", self._toggle_repeat, w=52, h=44, font_size=16)
        self.btn_repeat.pack(side="left", padx=4)

        vol_row = ctk.CTkFrame(controls, fg_color="transparent")
        vol_row.pack(pady=(2, 10))

        ctk.CTkLabel(vol_row, text="🔈", font=("Arial", 14), text_color=COR_DIM).pack(side="left", padx=4)
        self.slider_volume = ctk.CTkSlider(vol_row, from_=0, to=100, width=220, fg_color=COR_BORDER, progress_color=COR_GREEN, button_color=COR_GREEN, command=self._on_volume_change)
        self.slider_volume.pack(side="left", padx=4)
        ctk.CTkLabel(vol_row, text="🔊", font=("Arial", 14), text_color=COR_DIM).pack(side="left", padx=4)
        self.lbl_volume = ctk.CTkLabel(vol_row, text=f"{self.config_mgr.data.volume}%", font=("Courier", 11), text_color=COR_DIM, width=50)
        self.lbl_volume.pack(side="left", padx=4)

        self._update_shuffle_repeat_visual()

    # ---------------------------------------------------------------------
    # Biblioteca / álbuns
    # ---------------------------------------------------------------------

    def _reload_library(self):
        self.library = Library(self.config_mgr.data.pasta_raiz)
        self._refresh_album_list()
        self._restore_session()

    def _refresh_album_list(self):
        for w in self.album_scroll.winfo_children():
            w.destroy()

        if not self.library.albums:
            ctk.CTkLabel(
                self.album_scroll,
                text="Nenhum álbum encontrado.\nAbra ⚙️ Configurações e selecione a pasta raiz.",
                font=("Arial", 11),
                text_color=COR_DIM,
                justify="center",
            ).pack(padx=12, pady=28)
            return

        for i, album in enumerate(self.library.albums):
            count = len(album["tracks"])
            frame = ctk.CTkFrame(self.album_scroll, fg_color=COR_CARD, corner_radius=10)
            frame.pack(fill="x", padx=8, pady=4)

            if album["cover"]:
                try:
                    img = Image.open(album["cover"]).convert("RGB").resize((42, 42))
                except Exception:
                    img = make_round_cover(42)
            else:
                img = make_round_cover(42)

            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(42, 42))
            cover_label = ctk.CTkLabel(frame, image=photo, text="")
            cover_label.image = photo
            cover_label.pack(side="left", padx=(10, 6), pady=8)

            text_frame = ctk.CTkFrame(frame, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True, pady=4)
            ctk.CTkLabel(text_frame, text=album["name"], font=("Arial Bold", 12), text_color=COR_TEXT, anchor="w").pack(anchor="w", padx=4)
            ctk.CTkLabel(text_frame, text=f"{count} música{'s' if count != 1 else ''}", font=("Arial", 10), text_color=COR_DIM, anchor="w").pack(anchor="w", padx=4)

            frame.bind("<Button-1>", lambda e, idx=i: self._select_album(idx))
            cover_label.bind("<Button-1>", lambda e, idx=i: self._select_album(idx))
            text_frame.bind("<Button-1>", lambda e, idx=i: self._select_album(idx))
            for child in text_frame.winfo_children():
                child.bind("<Button-1>", lambda e, idx=i: self._select_album(idx))

            frame.bind("<Enter>", lambda e, f=frame: f.configure(fg_color=COR_HOVER))
            frame.bind("<Leave>", lambda e, f=frame, idx=i: f.configure(fg_color=COR_ACTIVE if idx == self.current_album_index else COR_CARD))
            album["_frame"] = frame

    def _select_album(self, idx: int):
        if not (0 <= idx < len(self.library.albums)):
            return

        if 0 <= self.current_album_index < len(self.library.albums):
            prev_frame = self.library.albums[self.current_album_index].get("_frame")
            if prev_frame:
                prev_frame.configure(fg_color=COR_CARD)

        self.current_album_index = idx
        album = self.library.albums[idx]
        album_frame = album.get("_frame")
        if album_frame:
            album_frame.configure(fg_color=COR_ACTIVE)

        self.playlist = list(album["tracks"])
        self.current_index = -1
        self.lbl_album_name.configure(text=album["name"])
        self.playlist_widget.load(self.playlist)
        self._show_cover(album.get("cover"))

    # ---------------------------------------------------------------------
    # Reprodução
    # ---------------------------------------------------------------------

    def _play_index(self, idx: int):
        if not (0 <= idx < len(self.playlist)):
            return
        self.current_index = idx
        track = self.playlist[idx]
        if self.audio.load_and_play(track["path"]):
            self.btn_play.configure(text="⏸")
            self.lbl_title.configure(text=track["title"])
            self.lbl_artist.configure(text=track["artist"])
            self.lbl_dur.configure(text=fmt_time(track["duration"]))
            self.playlist_widget.highlight(idx)
            self._show_track_cover(track)
        else:
            messagebox.showwarning("Erro", f"Não foi possível tocar: {track['title']}")

    def _toggle_play(self):
        if not self.playlist:
            return
        if self.current_index < 0:
            self._play_index(0)
            return
        self.audio.pause_resume()
        self.btn_play.configure(text="▶" if self.audio.pausado else "⏸")

    def _next_track(self):
        if not self.playlist:
            return
        if self.shuffle:
            next_idx = random.randint(0, len(self.playlist) - 1)
        else:
            next_idx = (self.current_index + 1) % len(self.playlist)
        self._play_index(next_idx)

    def _prev_track(self):
        if not self.playlist:
            return
        if self.audio.posicao > 3:
            self.audio.seek(0)
        else:
            prev_idx = (self.current_index - 1) % len(self.playlist)
            self._play_index(prev_idx)

    def _play_all(self):
        if self.playlist:
            self._play_index(0)

    def _shuffle_playlist(self):
        if not self.playlist:
            return
        current = self.playlist[self.current_index] if 0 <= self.current_index < len(self.playlist) else None
        random.shuffle(self.playlist)
        self.playlist_widget.load(self.playlist)
        if current:
            try:
                new_idx = self.playlist.index(current)
                self.current_index = new_idx
                self.playlist_widget.highlight(new_idx)
            except ValueError:
                self.current_index = -1

    def _toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.config_mgr.data.shuffle = self.shuffle
        self.config_mgr.save()
        self._update_shuffle_repeat_visual()

    def _toggle_repeat(self):
        modes = ["none", "all", "one"]
        idx = modes.index(self.repeat)
        self.repeat = modes[(idx + 1) % len(modes)]
        self.config_mgr.data.repeat = self.repeat
        self.config_mgr.save()
        self._update_shuffle_repeat_visual()

    def _update_shuffle_repeat_visual(self):
        self.btn_shuffle.configure(fg_color=COR_GREEN if self.shuffle else COR_CARD)
        if self.repeat == "one":
            self.btn_repeat.configure(text="🔂", fg_color=COR_GREEN)
        elif self.repeat == "all":
            self.btn_repeat.configure(text="🔁", fg_color=COR_GREEN)
        else:
            self.btn_repeat.configure(text="🔁", fg_color=COR_CARD)

    def _remove_playlist_item(self, idx: int):
        self.playlist_widget.remove_item(idx)
        if idx < self.current_index:
            self.current_index -= 1
        elif idx == self.current_index:
            self.audio.stop()
            self.current_index = -1
            self.btn_play.configure(text="▶")
        # Antes: o destaque (highlight) da faixa atual não era reaplicado
        # depois de remover um item anterior a ela, então a seleção visual
        # ficava na música errada. PlaylistWidget.remove_item agora reconstrói
        # a lista do zero, então precisamos reafirmar o destaque aqui.
        if self.current_index >= 0:
            self.playlist_widget.highlight(self.current_index)

    # ---------------------------------------------------------------------
    # Progresso / volume
    # ---------------------------------------------------------------------

    def _start_drag(self):
        self.dragging_slider = True

    def _end_drag(self):
        if self.audio.duracao > 0:
            pos = (self.slider_progress.get() / 100) * self.audio.duracao
            self.audio.seek(pos)
        self.dragging_slider = False

    def _on_slider_move(self, value):
        if self.dragging_slider and self.audio.duracao > 0:
            pos = (float(value) / 100) * self.audio.duracao
            self.lbl_pos.configure(text=fmt_time(pos))

    def _on_volume_change(self, value):
        vol = int(float(value))
        self.audio.set_volume(vol / 100)
        self.lbl_volume.configure(text=f"{vol}%")
        self.config_mgr.data.volume = vol
        self.config_mgr.save()

    def _sync_volume(self):
        vol = self.config_mgr.data.volume
        self.slider_volume.set(vol)
        self.audio.set_volume(vol / 100)
        self.lbl_volume.configure(text=f"{vol}%")

    # ---------------------------------------------------------------------
    # Loop principal
    # ---------------------------------------------------------------------

    def _start_loop(self):
        try:
            if not self.dragging_slider:
                dur = self.audio.duracao
                pos = self.audio.posicao
                if dur > 0:
                    self.slider_progress.set((pos / dur) * 100)
                    self.lbl_pos.configure(text=fmt_time(pos))
                else:
                    self.slider_progress.set(0)

            if self.audio.finished() and self.current_index >= 0:
                self._on_track_finished()

            self._check_alarm()
            self._check_auto_import()
        except Exception as e:
            print(f"Erro no loop: {e}")

        self.after(400, self._start_loop)

    def _on_track_finished(self):
        if self.repeat == "one":
            self._play_index(self.current_index)
        elif self.repeat == "all" or self.current_index < len(self.playlist) - 1:
            self._next_track()
        else:
            self.btn_play.configure(text="▶")
            self.current_index = -1

    # ---------------------------------------------------------------------
    # Alarme / auto-import
    # ---------------------------------------------------------------------

    def _check_alarm(self):
        if not self.config_mgr.data.alarme_ativo:
            return

        now = datetime.now()
        try:
            hh, mm = self.config_mgr.data.horario_fechamento.split(":")
            closing = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
            warn_minutes = int(self.config_mgr.data.aviso_minutos)
            warn_time = closing - timedelta(minutes=warn_minutes)
            reset_time = closing + timedelta(minutes=5)

            if warn_time <= now < warn_time + timedelta(minutes=1):
                if not self.alarm_triggered:
                    self.alarm_triggered = True
                    threading.Thread(target=self.audio.play_alarm, args=(self.config_mgr.data.arquivo_alarme,), daemon=True).start()
                    self._show_alarm_window(warn_minutes)
            elif now >= reset_time:
                self.alarm_triggered = False
        except Exception as e:
            print(f"Erro ao verificar alarme: {e}")

    def _check_auto_import(self):
        if not self.config_mgr.data.auto_import_ativo:
            return
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        if self.last_auto_import_day == today:
            return
        try:
            hh, mm = self.config_mgr.data.auto_import_horario.split(":")
            trigger = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
            if now >= trigger:
                self.last_auto_import_day = today
                self._import_downloads(silent=True)
        except Exception:
            pass

    def _show_alarm_window(self, minutes: int):
        top = ctk.CTkToplevel(self)
        top.attributes("-fullscreen", True)
        top.attributes("-topmost", True)
        top.configure(fg_color=COR_ORANGE)

        ctk.CTkLabel(top, text="⏰ ATENÇÃO ⏰", font=("Arial Black", 54), text_color="white").pack(expand=True, pady=(60, 10))
        ctk.CTkLabel(top, text=f"A ACADEMIA FECHARÁ EM\n{minutes} MINUTOS!", font=("Arial Black", 44), text_color="white", justify="center").pack(expand=True, pady=10)
        ctk.CTkLabel(top, text=f"Horário: {self.config_mgr.data.horario_fechamento}", font=("Arial", 26), text_color="white").pack(expand=True, pady=(10, 40))
        ctk.CTkButton(top, text="OK — Entendi", font=("Arial Bold", 22), height=64, width=280, fg_color="white", text_color=COR_ORANGE, hover_color="#ffe6d1", command=top.destroy).pack(pady=(0, 60))

    def _import_downloads(self, silent: bool = False):
        folder = self.config_mgr.data.pasta_downloads
        if not folder:
            if not silent:
                messagebox.showinfo("Importar downloads", "Configure a pasta de downloads em ⚙️ Configurações primeiro.")
            return
        count = self.library.import_from_downloads(folder)
        if count:
            self._refresh_album_list()
            if not silent:
                messagebox.showinfo("Importação", f"{count} música(s) importada(s) com sucesso!")
        else:
            if not silent:
                messagebox.showinfo("Importação", "Nenhuma música encontrada na pasta de downloads.")

    # ---------------------------------------------------------------------
    # Capa
    # ---------------------------------------------------------------------

    def _show_default_cover(self):
        img = make_round_cover(76)
        self._set_cover_image(img)

    def _show_cover(self, cover_path):
        if not cover_path:
            self._show_default_cover()
            return
        try:
            img = Image.open(cover_path).convert("RGB").resize((76, 76))
            self._set_cover_image(img)
        except Exception:
            self._show_default_cover()

    def _show_track_cover(self, track: dict):
        if track.get("cover_bytes"):
            try:
                img = Image.open(BytesIO(track["cover_bytes"])).convert("RGB").resize((76, 76))
                self._set_cover_image(img)
                return
            except Exception:
                pass
        self._show_default_cover()

    def _set_cover_image(self, img: Image.Image):
        mask = Image.new("L", (76, 76), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 75, 75), fill=255)
        img = img.convert("RGBA")
        img.putalpha(mask)
        photo = ctk.CTkImage(light_image=img, dark_image=img, size=(76, 76))
        if hasattr(self, "cover_label") and self.cover_label.winfo_exists():
            self.cover_label.destroy()
        self.cover_label = ctk.CTkLabel(self.header, image=photo, text="", fg_color="transparent")
        self.cover_label.image = photo
        self.cover_label.pack(side="right", padx=16, pady=8)
        self._cover_ref = photo

    # ---------------------------------------------------------------------
    # Configurações
    # ---------------------------------------------------------------------

    def _open_settings(self):
        SettingsWindow(self, self.config_mgr, self._apply_settings)

    def _apply_settings(self):
        self.library = Library(self.config_mgr.data.pasta_raiz)
        self._refresh_album_list()
        self._sync_volume()
        self._update_shuffle_repeat_visual()
        self.alarm_triggered = False

    # ---------------------------------------------------------------------
    # Tela / sessão
    # ---------------------------------------------------------------------

    def _toggle_fullscreen(self):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def _restore_session(self):
        if self.library.albums and self.config_mgr.data.ultima_album:
            for i, album in enumerate(self.library.albums):
                if str(album["path"]) == self.config_mgr.data.ultima_album:
                    self._select_album(i)
                    break

    def _on_close(self):
        if 0 <= self.current_album_index < len(self.library.albums):
            self.config_mgr.data.ultima_album = str(self.library.albums[self.current_album_index]["path"])
        self.config_mgr.data.ultima_posicao = self.audio.posicao
        self.config_mgr.data.volume = int(self.slider_volume.get())
        self.config_mgr.data.shuffle = self.shuffle
        self.config_mgr.data.repeat = self.repeat
        self.config_mgr.data.janela_maximizada = (self.state() == "zoomed")
        self.config_mgr.save()
        self.audio.close()
        self.destroy()
