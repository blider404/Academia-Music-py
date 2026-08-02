"""Escaneia a pasta raiz de músicas e organiza em álbuns/faixas."""

from __future__ import annotations

from pathlib import Path

from mutagen import File as MutagenFile

from .theme import MUSIC_EXT


class Library:
    def __init__(self, root_folder: str):
        self.root_folder = Path(root_folder) if root_folder else None
        self.albums: list[dict] = []
        if self.root_folder and self.root_folder.exists():
            self.scan()

    def scan(self) -> None:
        # Nota: leitura de metadados (ID3/capas) é síncrona e roda na thread
        # principal da UI. Para bibliotecas grandes isso pode travar a
        # interface por alguns instantes — um próximo passo natural é mover
        # essa chamada para uma threading.Thread e atualizar a UI via after().
        self.albums = []
        if not self.root_folder or not self.root_folder.exists():
            return

        root_music = self._list_music(self.root_folder)
        if root_music:
            self.albums.append({
                "name": "▶ Todas",
                "path": self.root_folder,
                "tracks": root_music,
                "cover": self._find_cover(self.root_folder),
            })

        try:
            for folder in sorted(self.root_folder.iterdir()):
                if folder.is_dir() and not folder.name.startswith("."):
                    tracks = self._list_music(folder)
                    if tracks:
                        self.albums.append({
                            "name": folder.name,
                            "path": folder,
                            "tracks": tracks,
                            "cover": self._find_cover(folder),
                        })
        except PermissionError as e:
            print(f"Sem permissão: {e}")

    @staticmethod
    def _list_music(folder: Path) -> list[dict]:
        tracks = []
        try:
            for file in sorted(folder.iterdir()):
                if file.is_file() and file.suffix.lower() in MUSIC_EXT:
                    tracks.append(Library._read_metadata(file))
        except Exception:
            pass
        return tracks

    @staticmethod
    def _read_metadata(file: Path) -> dict:
        title = file.stem
        artist = "Desconhecido"
        duration = 0.0
        cover_bytes = None

        try:
            audio = MutagenFile(file, easy=True)
            if audio:
                title = str(audio.get("title", [file.stem])[0])
                artist = str(audio.get("artist", ["Desconhecido"])[0])
                if getattr(audio, "info", None) and hasattr(audio.info, "length"):
                    duration = float(audio.info.length)

            if file.suffix.lower() == ".mp3":
                from mutagen.id3 import APIC, ID3
                tags = ID3(str(file))
                for tag in tags.values():
                    if isinstance(tag, APIC):
                        cover_bytes = tag.data
                        break
        except Exception:
            pass

        return {
            "path": str(file),
            "title": title,
            "artist": artist,
            "duration": duration,
            "cover_bytes": cover_bytes,
        }

    @staticmethod
    def _find_cover(folder: Path):
        for name in ("cover.jpg", "cover.jpeg", "cover.png", "folder.jpg", "folder.png"):
            p = folder / name
            if p.exists():
                return str(p)
        return None

    def import_from_downloads(self, downloads_folder: str) -> int:
        if not self.root_folder:
            return 0
        src = Path(downloads_folder)
        if not src.exists():
            return 0

        dst = self.root_folder / "Novidades"
        dst.mkdir(exist_ok=True)
        count = 0

        for file in src.iterdir():
            if file.is_file() and file.suffix.lower() in MUSIC_EXT:
                try:
                    new_path = dst / file.name
                    if new_path.exists():
                        stem, suf = new_path.stem, new_path.suffix
                        n = 1
                        while new_path.exists():
                            new_path = dst / f"{stem}_{n}{suf}"
                            n += 1
                    file.rename(new_path)
                    count += 1
                except Exception as e:
                    print(f"Erro ao importar {file.name}: {e}")

        if count:
            self.scan()
        return count
