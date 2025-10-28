# BattleLog v1.9.3 - Linux x86-64

## ⚠️ WAŻNE - Pobieranie z Google Drive

**Jeśli pobierasz z Google Drive**, plik może zostać uszkodzony. 

**Prawidłowy sposób pobierania:**
1. Kliknij PRAWYM przyciskiem myszy na plik w Google Drive
2. Wybierz **"Pobierz"** (nie "Otwórz z...")
3. Poczekaj na zakończenie pobierania

## Instrukcja instalacji

### Wariant A: Użyj skryptu startowego (ZALECANE)

```bash
unzip battlelog_app_v1.9.3.zip
# LUB: tar -xzf battlelog_app_v1.9.3.tar.gz

cd battlelog_v1.9.3
bash start_battlelog.sh
```

### Wariant B: Uruchomienie ręczne

```bash
chmod +x battlelog_app_v1.9.3
./battlelog_app_v1.9.3
```

### Wariant C: Jeśli występuje błąd "Could not load PKG archive"

To oznacza uszkodzenie podczas pobierania. Użyj skryptu naprawczego:

```bash
bash fix_permissions.sh
```

Jeśli nadal nie działa - **pobierz plik ponownie**, upewniając się że:
- Pobierasz bezpośrednio (prawy przycisk → Pobierz)
- Nie otwierasz pliku w przeglądarce przed zapisaniem
- Wypakowujesz używając `unzip` lub `tar -xzf`

## Wymagania systemowe

- Linux x86-64 (Ubuntu 20.04+, Debian 11+, Fedora 35+, etc.)
- Środowisko graficzne (X11/Wayland)
- FFmpeg (opcjonalnie - dla lepszej kompresji wideo)

## Co nowego w wersji 1.9.3

- ✅ Zmieniono czas nagrywania z sekund na **minuty** (1-120 min)
- ✅ Aktualizacja tłumaczeń (PL/EN/UA)
- ✅ System kolejkowania przetwarzania wideo
- ✅ Możliwość rozpoczęcia nowego nagrania podczas przetwarzania
- ✅ Optymalizacja zużycia zasobów

## Rozmiar

- Spakowany (ZIP): ~124 MB
- Rozpakowany: ~125 MB
- Wszystkie zależności wbudowane (brak instalacji)

## Suma kontrolna (SHA256)

battlelog_app_v1.9.3: 82a13b59e7bf950cd6f23a855952f27dbb4a6db375d3fc35cfac474ec50f2136

## Wsparcie

https://apsystems.tech/
