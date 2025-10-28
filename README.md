# BattleLog

Kompletna, skoncentrowana dokumentacja użytkownika i dewelopera — opis projektu, jak z niego korzystać, jak go budować i publikować.

## Krótkie wprowadzenie
BattleLog to aplikacja desktopowa napisana w Pythonie (tkinter / customtkinter) odpowiedzialna za nagrywanie ekranu/okien oraz późniejszy post-processing (kodowanie, konteneryzacja) przy pomocy FFmpeg.

Najważniejsze fakty:
- Język: Python 3.x
- UI: tkinter + customtkinter
- Multimedia: FFmpeg (używane przez aplikację do przetwarzania), OpenCV (opcjonalnie, jeśli używane w projekcie)
- Konkurencja/wywołania procesów: użycie wątków (`threading`), zdarzeń (`threading.Event`) i kolejki przetwarzania do serializacji ciężkich zadań FFmpeg

## Struktura repozytorium (ważne pliki)
- `battlelog_app_1_9.py` — główny plik aplikacji (UI i logika nagrywania/post-processingu).
- `requirements.txt` — lista zależności Python.
- `Dockerfile` — obraz buildera do tworzenia jednoplikowego wykonwalnego przez PyInstaller.
- `battlelog_onefile.spec` — specyfikacja PyInstaller (jeśli potrzebna do rebuild).
- `build/` — folder z artefaktami build (lokalny, zwykle ignorowany w repo).

## Wymagania środowiskowe
- System: Linux (x86_64) — aplikacja testowana była na Ubuntu; do zbudowania binarki wymagany jest system zgodny z docelową architekturą.
- Python 3.8+ (zalecane 3.10+)
- Narzędzia: `docker` + `docker build` (jeśli korzystasz z obrazu buildera), lokalnie: `pyinstaller` (opcjonalnie)
- FFmpeg: aplikacja używa ffmpeg; wersja powinna być kompatybilna z opcjami używanymi w skryptach (zalecane: nowsze stabilne wydanie).

## Szybki start — uruchomienie w trybie developerskim
1. Utwórz i aktywuj virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Uruchom aplikację:

```bash
python battlelog_app_1_9.py
```

Po uruchomieniu powinno pojawić się okno aplikacji. Interfejs pozwala ustawić czas nagrania (w minutach — zakres 1..120, domyślnie 9), język interfejsu oraz rozpocząć/zatrzymać nagrywanie.

## Najważniejsze elementy interfejsu i workflow
- Przycisk nagrywania: start/stop; ikona zatrzymania ma kolor czerwony (w wersji aktualnej) dla lepszej widoczności.
- Czas nagrania: pole przyjmuje wartość w minutach; program wewnętrznie konwertuje na sekundy.
- Status: aplikacja łączy status nagrywania i przetwarzania w jedną linię aby pokazać użytkownikowi aktualny stan (nagrywanie / przetwarzanie / gotowe).

Proces nagrywania i przetwarzania:
1. Użytkownik uruchamia nagrywanie.
2. Aplikacja tworzy zadanie nagrywania i zapisuje surowy plik.
3. Po zakończeniu nagrania surowy plik jest przekazywany do kolejki przetwarzania.
4. Przetwarzanie (FFmpeg) jest uruchamiane w oddzielnym wątku; aplikacja używa licznika `active_processing_threads` i kolejki (`deque`) aby serializować lub limitować równoległe zadania.
5. Użytkownik może anulować przetwarzanie; aplikacja używa `threading.Event` (np. `processing_cancelled`) by wysłać żądanie przerwania do procesu.

Uwagi dotyczące zasobów:
- Aby zmniejszyć wpływ FFmpeg na responsywność systemu aplikacja używa `psutil` do obniżenia priorytetu procesów ffmpeg uruchamianych z poziomu aplikacji.

## Konfiguracja (FFmpeg i ścieżki)
- Jeśli aplikacja nie znajduje `ffmpeg` / `ffprobe`, upewnij się że binarki są w PATH lub ustaw je w konfiguracji aplikacji (jeśli aplikacja udostępnia taką opcję).
- W repo nie trzymamy dużych binarek (ponad 100 MB) — artefakty budowy powinny być publikowane jako Release.

## Budowa jednoplikowego wykonwalnego (PyInstaller) — lokalnie
Uwaga: buduje się dla architektury hosta. Wynik zależy od wersji bibliotek systemowych.

1. Upewnij się, że masz zainstalowany `pyinstaller` w środowisku:

```bash
pip install pyinstaller
```

2. Uruchom PyInstaller (przykład):

```bash
pyinstaller --onefile --name battlelog_app_1_9 battlelog_app_1_9.py
```

3. Po zakończeniu binarka znajdzie się w `dist/battlelog_app_1_9`.

## Budowa jednoplikowego wykonwalnego — przez Docker (rekomendowane dla reproducibility)
Użycie Dockera zapewnia spójne, powtarzalne środowisko buildów i minimalizuje różnice między maszynami.

1. Zbuduj obraz buildera (jeśli Dockerfile zawiera definicję):

```bash
docker build -t battlelog-builder -f Dockerfile .
```

2. Uruchom build wewnątrz kontenera (przykładowe polecenie):

```bash
docker run --rm -v "$PWD":/app -w /app battlelog-builder /bin/bash -c "pyinstaller --onefile --name battlelog_app_1_9 battlelog_app_1_9.py"
```

3. Skopiuj wygenerowany plik z kontenera / sprawdź katalog `dist` na hoście.

Uwaga: obraz buildera powinien zawierać odpowiednie zależności systemowe wymagane przez pyinstaller i pakowane biblioteki.

## Pakowanie i dystrybucja
- Do dystrybucji przygotowujemy archiwum tar.gz, aby zachować prawa wykonywania:

```bash
tar -czf battlelog_v1.9.3_linux_x86_64.tar.gz dist/battlelog_app_1_9
sha256sum battlelog_v1.9.3_linux_x86_64.tar.gz > SHA256SUMS.txt
```

- Do publikacji używamy GitHub Releases — dodaj tar.gz jako asset do releasu.

Krótka wzmianka o Git LFS:
- Jeśli zamierzasz trzymać duże pliki w repo, rozważ Git LFS; jednak zalecane jest przechowywanie binarek w Releases, aby nie obciążać historii Git.

## Troubleshooting — najczęstsze problemy i rozwiązania
- Problem: push do GitHub odrzucany z powodu dużych plików (>100 MB)
  - Rozwiązanie: usuń duże pliki z repo i użyj GitHub Releases lub Git LFS.

- Problem: brak `ffmpeg`/`ffprobe` w PATH — aplikacja zgłasza błąd przy starcie przetwarzania
  - Rozwiązanie: zainstaluj ffmpeg lub wskaż pełną ścieżkę do binarek.

- Problem: "Could not load PyInstaller's embedded PKG archive" przy uruchamianiu binarki
  - Najczęściej efekt uszkodzonego pliku (transfer/upload). Sprawdź sumy kontrolne (SHA256). Używaj tar.gz do transferów, aby zachować prawa exec i uniknąć dodatkowych zaburzeń.

- Problem: błędy związane z X server podczas budowania w Dockerze (np. ostrzeżenia dotyczące pynput)
  - Ostrzeżenia te zwykle nie blokują budowy; jeśli aplikacja ma interakcje niskiego poziomu z systemem wejścia, testuj binarkę na maszynie docelowej.

## Praca z tłumaczeniami
- Tłumaczenia znajdują się w słowniku `TRANSLATIONS` (PL/EN/UA). Jeśli dodajesz nowe teksty interfejsu, dodaj klucze do wszystkich dostępnych języków.

## Development notes — szybkie wskazówki dla programisty
- Kod używa mechanizmów: `threading.Event` (cancellation), `deque` jako kolejka przetwarzania, `psutil` do obniżania priorytetu procesów ffmpeg.
- Podczas debugowania obserwuj licznik `active_processing_threads` i logi wywołań subprocess/ffmpeg.

## Testowanie po buildzie
- Po stworzeniu onefile executable uruchom go lokalnie i sprawdź, czy GUI startuje i czy przetwarzanie działa dla przykładowego, krótkiego nagrania.

---

Ten plik zawiera konkretne instrukcje potrzebne do uruchamiania, budowy i publikacji aplikacji. Jeśli chcesz, mogę od razu:
- zrobić commit i push tego pliku do zdalnego repo (`origin/master`),
albo możesz wskazać inny branch/ścieżkę.
