#!/bin/bash

# Skrypt do szybkiego uruchamiania aplikacji BattleLog w trybie testowym

echo "🚀 BattleLog - Tryb testowy"
echo "=========================="

# Sprawdź czy istnieje środowisko wirtualne
if [ ! -d ".venv" ]; then
    echo "❌ Środowisko wirtualne nie istnieje. Uruchom najpierw konfigurację."
    exit 1
fi

# Aktywuj środowisko wirtualne i uruchom aplikację
echo "🐍 Aktywuję środowisko wirtualne..."
source .venv/bin/activate

echo "🔧 Sprawdzam uprawnienia ffmpeg..."
if [ -f "ffmpeg" ]; then
    chmod +x ffmpeg
    echo "✅ FFmpeg jest gotowy"
else
    echo "⚠️  FFmpeg nie został znaleziony"
fi

echo "🎯 Uruchamianie aplikacji..."
echo "   (Aby zatrzymać, naciśnij Ctrl+C)"
echo ""

# Uruchom aplikację
python battlelog_app.py
