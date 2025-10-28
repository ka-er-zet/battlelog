#!/bin/bash
# BattleLog v1.9.3 - Skrypt uruchamiający
# Automatycznie nadaje uprawnienia wykonywania i uruchamia aplikację

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_FILE="$SCRIPT_DIR/battlelog_app_v1.9.3"

echo "BattleLog v1.9.3 - Uruchamianie..."

# Sprawdź czy plik istnieje
if [ ! -f "$APP_FILE" ]; then
    echo "BŁĄD: Nie znaleziono pliku aplikacji: $APP_FILE"
    exit 1
fi

# Nadaj uprawnienia wykonywania jeśli nie ma
if [ ! -x "$APP_FILE" ]; then
    echo "Nadawanie uprawnień wykonywania..."
    chmod +x "$APP_FILE"
fi

# Uruchom aplikację
echo "Uruchamianie BattleLog..."
"$APP_FILE"
