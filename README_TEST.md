# BattleLog - Środowisko Testowe

## Szybkie uruchamianie w trybie testowym

### Metoda 1: Skrypt bash (najszybsza)
```bash
./run_test.sh
```

### Metoda 2: Skrypt Python z diagnostyką
```bash
.venv/bin/python test_app.py
```

### Metoda 3: Bezpośrednie uruchomienie
```bash
source .venv/bin/activate
python battlelog_app.py
```

## Struktura środowiska

```
BATTLELOG_v1_2_python/
├── .venv/                    # Środowisko wirtualne Python
├── battlelog_app.py          # Główna aplikacja
├── test_app.py              # Skrypt testowy z diagnostyką
├── run_test.sh              # Skrypt bash do szybkiego uruchamiania
├── requirements.txt         # Zależności Pythona
├── ffmpeg                   # Binarny plik FFmpeg (Linux)
├── ffmpeg.exe              # Binarny plik FFmpeg (Windows)
└── *.png                   # Ikony aplikacji
```

## Zalety środowiska testowego

✅ **Szybkość** - Brak potrzeby budowania aplikacji za każdym razem  
✅ **Debugowanie** - Pełny dostęp do logów i błędów  
✅ **Rozwój** - Natychmiastowe testowanie zmian w kodzie  
✅ **Izolacja** - Wszystkie zależności w środowisku wirtualnym  

## Testowanie zmian

1. **Edytuj kod** w pliku `battlelog_app.py`
2. **Zapisz plik** (Ctrl+S)
3. **Uruchom aplikację**:
   ```bash
   ./run_test.sh
   ```
4. **Testuj funkcjonalność**
5. **Zatrzymaj aplikację** (Ctrl+C)
6. **Powtórz** od kroku 1

## Środowisko wirtualne

Środowisko wirtualne zostało skonfigurowane z następującymi pakietami:
- `customtkinter` - Nowoczesny UI framework
- `mss` - Przechwytywanie ekranu
- `opencv-python` - Przetwarzanie obrazów i wideo
- `numpy` - Operacje numeryczne
- `Pillow` - Manipulacja obrazami
- `pyinstaller` - Budowanie aplikacji

## Rozwiązywanie problemów

### Problem z ffmpeg
```bash
chmod +x ffmpeg
```

### Problem z uprawnieniami
```bash
chmod +x run_test.sh
```

### Problem z zależnościami
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Problem z GUI na Linuksie
Upewnij się, że masz zainstalowane:
```bash
sudo apt-get install python3-tk
```

## Uwagi dla systemu Linux

- Aplikacja używa `tkinter` do GUI
- Może wymagać zainstalowania `python3-tk`
- FFmpeg jest dołączony jako binarny plik Linux
- Testowane na Ubuntu 22.04

## Debugowanie

Jeśli aplikacja nie uruchamia się, użyj skryptu testowego:
```bash
.venv/bin/python test_app.py
```

Skrypt wyświetli szczegółowe informacje o:
- Brakujących plikach
- Problemach z uprawnieniami
- Błędach importu
- Statusie FFmpeg
