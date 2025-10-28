# Użyj starszej, stabilnej wersji Ubuntu (LTS)
FROM ubuntu:22.04

# Unikaj interaktywnych pytań podczas instalacji
ENV DEBIAN_FRONTEND=noninteractive

# Zainstaluj Pythona, pip, tkinter ORAZ brakujące biblioteki systemowe
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    python3-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libice6 \
    libxext6 \
    libxrender1 \
    xdg-utils \
    libx11-dev \
    libxtst-dev \
    libxkbcommon-x11-0 \
    scrot \
    python3-xlib \
    && rm -rf /var/lib/apt/lists/*

# Ustaw katalog roboczy wewnątrz kontenera
WORKDIR /app

# Skopiuj pliki aplikacji do kontenera
COPY . .


# Zainstaluj zależności Pythona w środowisku wirtualnym
RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt
# Upewnij się, że pillow jest zainstalowany (dla ImageTk)
RUN /app/venv/bin/pip install pillow

# Buduj aplikację jako jeden plik wykonywalny (onefile) i dołącz pliki ikon oraz wymagane hidden-imports
RUN /app/venv/bin/pyinstaller --onefile --name battlelog_app \
    --add-data "camera_icon.png:." \
    --add-data "folder_icon.png:." \
    --add-data "monitors_icon.png:." \
    --add-data "stop.png:." \
    --add-data "video_icon.png:." \
    --add-data "ikona.png:." \
    --add-data "ffmpeg:." \
    --hidden-import="PIL._tkinter_finder" \
    --hidden-import="pynput" \
    --hidden-import="pynput.keyboard" \
    --hidden-import="pynput.mouse" \
    --hidden-import="pynput._util" \
    --hidden-import="pynput._util.xorg" \
    --hidden-import="pyautogui" \
    --hidden-import="pynput.keyboard._xorg" \
    --hidden-import="pynput.mouse._xorg" \
    "battlelog_app_1_9.py"

# Ustaw uprawnienia do pliku wynikowego
RUN chmod +x /app/dist/battlelog_app || true
RUN chown 1000:1000 /app/dist/battlelog_app || true