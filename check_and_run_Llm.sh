#!/bin/bash

SCREEN_NAME="llm"
SCRIPT_NAME="restarter.py"
PROCESS_NAME="python3.11 $SCRIPT_NAME"

# Проверяем, запущен ли процесс
if ! pgrep -f "$PROCESS_NAME" > /dev/null; then
    echo "Скрипт $SCRIPT_NAME не запущен. Запускаем в screen..."

    # Запускаем или подключаемся к сессии screen
    screen -dmS "$SCREEN_NAME" bash -c "
        cd /home/Aleksandr/yagpt &&
        source myenv/bin/activate &&
        python3.11 restarter.py
    "

    echo "Скрипт запущен в фоне в сессии screen: $SCREEN_NAME"
else
    echo "Скрипт $SCRIPT_NAME уже запущен."
fi
