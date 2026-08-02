from academia_player.ui.main_window import AcademiaPlayer
from academia_player.utils import ensure_dir

if __name__ == "__main__":
    ensure_dir("musicas")
    app = AcademiaPlayer()
    app.mainloop()
