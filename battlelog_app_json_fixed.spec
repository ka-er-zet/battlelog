# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['battlelog_app 1_7.py'],
    pathex=[],
    binaries=[],
    datas=[('camera_icon.png', '.'), ('folder_icon.png', '.'), ('monitors_icon.png', '.'), ('stop.png', '.'), ('video_icon.png', '.'), ('ikona.png', '.'), ('ffmpeg', '.')],
    hiddenimports=['PIL._tkinter_finder', 'pynput', 'pynput.keyboard', 'pynput.mouse', 'pynput._util', 'pynput._util.xorg', 'pyautogui', 'pynput.keyboard._xorg', 'pynput.mouse._xorg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='battlelog_app_json_fixed',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
