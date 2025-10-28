#!/bin/bash
# Tworzy środowisko venv, instaluje zależności i uruchamia aplikację do testów lokalnych

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "\nŚrodowisko venv gotowe. Aby aktywować: source venv/bin/activate"
echo "Aby uruchomić aplikację: python 'battlelog_app 1_7.py'"
