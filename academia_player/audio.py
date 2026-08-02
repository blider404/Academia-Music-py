"""Camada de reprodução de áudio, isolada da UI (usa pygame.mixer)."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Optional

import pygame
from mutagen import File as MutagenFile


class AudioManager:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.set_num_channels(8)
        self._lock = threading.Lock()
        self._volume = 0.8
        self._duracao = 0.0
        self._arquivo_atual: Optional[str] = None
        self._tempo_ini = 0.0
        self._posicao_ini = 0.0
        self._pausado = False
        self._posicao_pausa = 0.0
        self._tocando = False
        self._alarm_channel = pygame.mixer.Channel(1)

    @property
    def duracao(self) -> float:
        return self._duracao

    @property
    def tocando(self) -> bool:
        return self._tocando and not self._pausado

    @property
    def pausado(self) -> bool:
        return self._pausado

    @property
    def arquivo_atual(self) -> Optional[str]:
        return self._arquivo_atual

    @property
    def posicao(self) -> float:
        if not self._tocando:
            return 0.0
        if self._pausado:
            return self._posicao_pausa
        return min(self._posicao_ini + (time.time() - self._tempo_ini), self._duracao)

    def set_volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, value))
        pygame.mixer.music.set_volume(self._volume)

    def load_and_play(self, path: str, start_pos: float = 0.0) -> bool:
        try:
            with self._lock:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self._volume)
                pygame.mixer.music.play(start=start_pos)
                self._arquivo_atual = path
                self._duracao = self._get_duration(path)
                self._posicao_ini = start_pos
                self._tempo_ini = time.time()
                self._pausado = False
                self._tocando = True
                self._posicao_pausa = start_pos
            return True
        except Exception as e:
            print(f"Erro ao tocar '{path}': {e}")
            return False

    def pause_resume(self) -> None:
        with self._lock:
            if not self._tocando:
                return
            if self._pausado:
                pygame.mixer.music.unpause()
                self._posicao_ini = self._posicao_pausa
                self._tempo_ini = time.time()
                self._pausado = False
            else:
                self._posicao_pausa = self.posicao
                pygame.mixer.music.pause()
                self._pausado = True

    def stop(self) -> None:
        with self._lock:
            pygame.mixer.music.stop()
            self._arquivo_atual = None
            self._duracao = 0.0
            self._tempo_ini = 0.0
            self._posicao_ini = 0.0
            self._pausado = False
            self._tocando = False
            self._posicao_pausa = 0.0

    def seek(self, seconds: float) -> None:
        if not self._tocando:
            return
        with self._lock:
            paused = self._pausado
            pygame.mixer.music.play(start=max(0.0, seconds))
            self._posicao_ini = max(0.0, seconds)
            self._tempo_ini = time.time()
            if paused:
                pygame.mixer.music.pause()
                self._posicao_pausa = self._posicao_ini
                self._pausado = True

    def finished(self) -> bool:
        if not self._tocando or self._pausado:
            return False
        return not pygame.mixer.music.get_busy()

    def play_alarm(self, path: str) -> None:
        # Usa o mesmo lock que protege o resto do mixer: essa função é chamada
        # a partir de uma thread separada (ver _check_alarm), então sem o lock
        # ela podia disputar o mixer com load_and_play/pause_resume/seek
        # chamados na thread principal ao mesmo tempo.
        try:
            if not path or not Path(path).exists():
                raise FileNotFoundError("Arquivo de alarme não encontrado")
            with self._lock:
                sound = pygame.mixer.Sound(path)
                self._alarm_channel.stop()
                self._alarm_channel.set_volume(1.0)
                self._alarm_channel.play(sound, loops=1)
        except Exception as e:
            print(f"Erro ao tocar alarme: {e}")

    @staticmethod
    def _get_duration(path: str) -> float:
        try:
            audio = MutagenFile(path)
            if audio and getattr(audio, "info", None) and hasattr(audio.info, "length"):
                return float(audio.info.length)
        except Exception:
            pass
        return 0.0

    def close(self) -> None:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            pygame.quit()
        except Exception:
            pass
