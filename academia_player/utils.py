"""Funções utilitárias puras — fáceis de testar isoladamente, sem UI."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .theme import COR_CARD


def fmt_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def safe_int(value: str, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def make_round_cover(size: int = 76) -> Image.Image:
    img = Image.new("RGB", (size, size), COR_CARD)
    draw = ImageDraw.Draw(img)
    draw.ellipse((12, 12, size - 12, size - 12), fill="#243129")
    draw.ellipse((size // 2 - 9, size // 2 - 9, size // 2 + 9, size // 2 + 9), fill=COR_CARD)
    return img
