# -*- mode: python ; coding: utf-8 -*-

import sys

# Lista wszystkich zasobów (ikon, ffmpeg), które mają zostać dołączone do aplikacji.
# Format: ('ścieżka/do/pliku/w/projekcie', 'gdzie/umieścić/w/aplikacji')
# '.' oznacza główny katalog wewnątrz spakowanego pliku .exe/.
assets = [
    ('ikona.png', '.'),
    ('camera_icon.png', '.'),
    ('video_icon.png', '.'),
    ('stop.png', '.'),
    ('folder_icon.png', '.'),
    ('monitors_icon.png', '.')
]

# Logika dołączająca odpowiedni plik FFmpeg w zależności od systemu
if sys.platform == "win32":
    # Na Windows dołączamy ffmpeg.exe
    assets.append(('ffmpeg.exe', '.'))
else:
    # Na Linuksie i macOS dołączamy plik 'ffmpeg'
    assets.append(('ffmpeg', '.'))


block_cipher = None


a = Analysis(
    ['battlelog_app 1_7.py'],  # Używamy nowego pliku
    pathex=[],
    binaries=[],
    datas=assets,  # <--- TO JEST NAJWAŻNIEJSZA LINIA! Mówi, aby dołączyć nasze zasoby.
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # ONEFILE: wszystkie binaries są w jednym pliku
    a.zipfiles,  # ONEFILE: wszystkie zipfiles są w jednym pliku
    a.datas,     # ONEFILE: wszystkie datas są w jednym pliku
    [],
    name='BattleLog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # <-- Ważne, aby nie pokazywać czarnego okna konsoli
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ikona.ico' if sys.platform == 'win32' else 'ikona.png', # <-- Używamy odpowiedniej ikony
)

# BattleLog v.1.7
# Copyright Advanced Protection Systems
