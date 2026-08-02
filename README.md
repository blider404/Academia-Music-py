# 🏋️ Academia Music py

Player de música para academia com interface moderna (customtkinter), configurações
na própria UI, alarme sonoro de horário de fechamento e gerenciamento por álbuns.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Na primeira execução, abra ⚙️ **Configurações** e selecione a pasta raiz das suas músicas.
Cada subpasta dentro dela vira um álbum na barra lateral.

## Estrutura do projeto

```
academia_player/
├── main.py                        # ponto de entrada
├── requirements.txt
├── academia_player/
│   ├── theme.py                   # constantes visuais e caminhos padrão
│   ├── utils.py                   # funções puras (fmt_time, safe_int, ...)
│   ├── config.py                  # AppConfig + ConfigManager (persistência em JSON)
│   ├── audio.py                   # AudioManager (camada sobre pygame.mixer)
│   ├── library.py                 # Library (varre pastas e lê metadados/capas)
│   └── ui/
│       ├── playlist_widget.py     # PlaylistWidget
│       ├── settings_window.py     # SettingsWindow
│       └── main_window.py         # AcademiaPlayer (janela principal)
├── musicas/                       # sua biblioteca musical (ignorada pelo git)
└── alarme.mp3                     # som de alerta (ignorado pelo git)
```

## Funcionalidades

- Organização automática por álbuns (subpastas)
- Shuffle e modos de repetição (nenhum / uma / todas)
- Capas de álbum lidas de `cover.jpg`/`folder.jpg` ou embutidas no ID3 do MP3
- Alarme sonoro configurável antes do horário de fechamento
- Auto-importação diária de uma pasta de downloads
- Sessão restaurada ao reabrir (último álbum, volume, shuffle/repeat, janela maximizada)

