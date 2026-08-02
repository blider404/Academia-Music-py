"""Constantes de tema, tamanhos e caminhos padrão do app."""

from __future__ import annotations

from pathlib import Path

APP_TITLE = "Academia Music Py"
APP_SIZE = "1200x760"
APP_MIN_SIZE = (980, 640)

COR_BG = "#0b0f0c"
COR_PANEL = "#111614"
COR_CARD = "#18201c"
COR_CARD_2 = "#1d2722"
COR_HOVER = "#243129"
COR_ACTIVE = "#143524"
COR_GREEN = "#00c853"
COR_GREEN_DARK = "#00a94a"
COR_RED = "#ff4d4d"
COR_ORANGE = "#ff7a18"
COR_TEXT = "#f4f7f5"
COR_DIM = "#87928d"
COR_BORDER = "#25322b"

MUSIC_EXT = (".mp3", ".wav", ".ogg", ".flac", ".m4a")
CONFIG_PATH = Path.home() / ".academia_player_pro_config.json"

# Antes: Path.cwd() / "alarme.mp3" -> dependia da pasta de onde o script era
# executado. Agora é relativo à raiz do pacote, então funciona sempre.
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALARM_FILE = PACKAGE_ROOT / "alarme.mp3"
