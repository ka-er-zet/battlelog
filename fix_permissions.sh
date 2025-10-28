#!/bin/bash
# Skrypt naprawiający uszkodzony plik PyInstaller po transferze przez Google Drive

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_FILE="$SCRIPT_DIR/battlelog_app_v1.9.3"

echo "=== BattleLog v1.9.3 - Narzędzie naprawcze ==="
echo ""
echo "Ten skrypt próbuje naprawić plik wykonywalny jeśli został"
echo "uszkodzony podczas pobierania z Google Drive."
echo ""

if [ ! -f "$APP_FILE" ]; then
    echo "BŁĄD: Nie znaleziono pliku: $APP_FILE"
    exit 1
fi

# Sprawdź czy to właściwy plik ELF
echo "1. Sprawdzanie typu pliku..."
file "$APP_FILE" | grep -q "ELF"
if [ $? -ne 0 ]; then
    echo "   ⚠️  Plik nie jest prawidłowym plikiem wykonywalnym ELF!"
    echo "   Plik mógł zostać uszkodzony podczas pobierania."
    echo ""
    echo "ROZWIĄZANIE:"
    echo "1. Usuń ten plik"
    echo "2. Pobierz archiwum ponownie z Google Drive"
    echo "3. Podczas pobierania wybierz 'Pobierz bezpośrednio' zamiast 'Otwórz z...'"
    echo "4. Wypakuj poleceniem: tar -xzf battlelog_app_v1.9.3.tar.gz"
    exit 1
fi
echo "   ✓ Plik jest prawidłowym plikiem ELF"

# Nadaj uprawnienia
echo "2. Nadawanie uprawnień wykonywania..."
chmod +x "$APP_FILE"
echo "   ✓ Uprawnienia ustawione"

# Sprawdź rozmiar
echo "3. Sprawdzanie rozmiaru pliku..."
SIZE=$(stat -f%z "$APP_FILE" 2>/dev/null || stat -c%s "$APP_FILE" 2>/dev/null)
if [ -z "$SIZE" ]; then
    echo "   ⚠️  Nie można odczytać rozmiaru"
elif [ $SIZE -lt 100000000 ]; then
    echo "   ⚠️  Plik jest podejrzanie mały ($SIZE bajtów)"
    echo "   Oczekiwany rozmiar: ~130 MB"
    echo "   Plik prawdopodobnie jest uszkodzony!"
else
    echo "   ✓ Rozmiar pliku wygląda poprawnie: $(numfmt --to=iec $SIZE 2>/dev/null || echo "$SIZE bajtów")"
fi

# Sprawdź czy można uruchomić
echo "4. Test uruchomienia..."
timeout 2s "$APP_FILE" --help >/dev/null 2>&1
RESULT=$?
if [ $RESULT -eq 124 ]; then
    echo "   ✓ Aplikacja uruchamia się poprawnie"
    echo ""
    echo "=== Naprawa zakończona pomyślnie! ==="
    echo ""
    echo "Możesz teraz uruchomić aplikację:"
    echo "   ./battlelog_app_v1.9.3"
    echo ""
    echo "LUB użyj skryptu startowego:"
    echo "   bash start_battlelog.sh"
else
    echo "   ✗ Błąd podczas uruchamiania (kod: $RESULT)"
    echo ""
    echo "Plik został uszkodzony podczas pobierania!"
    echo ""
    echo "INSTRUKCJA NAPRAWY:"
    echo "1. Usuń bieżące pliki"
    echo "2. W Google Drive kliknij PRAWYM przyciskiem na plik"
    echo "3. Wybierz 'Pobierz' (nie 'Otwórz')"
    echo "4. Wypakuj: tar -xzf battlelog_app_v1.9.3.tar.gz"
    echo "5. Uruchom ponownie ten skrypt naprawczy"
fi

echo ""
