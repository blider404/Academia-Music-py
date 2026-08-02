"""Configuração persistente do app (arquivo JSON na pasta do usuário)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .theme import CONFIG_PATH, DEFAULT_ALARM_FILE


@dataclass
class AppConfig:
    pasta_raiz: str = ""
    pasta_downloads: str = ""
    arquivo_alarme: str = str(DEFAULT_ALARM_FILE)
    volume: int = 80
    horario_fechamento: str = "22:00"
    aviso_minutos: int = 10
    alarme_ativo: bool = True
    auto_import_ativo: bool = False
    auto_import_horario: str = "06:00"
    shuffle: bool = False
    repeat: str = "none"  # none | one | all
    janela_maximizada: bool = False
    ultima_album: str = ""
    ultima_musica: str = ""
    ultima_posicao: float = 0.0


class ConfigManager:
    def __init__(self, path: Path = CONFIG_PATH):
        self.path = path
        self.data = AppConfig()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for key, value in raw.items():
                if hasattr(self.data, key):
                    setattr(self.data, key, value)
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")

    def save(self) -> None:
        try:
            self.path.write_text(json.dumps(asdict(self.data), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")
