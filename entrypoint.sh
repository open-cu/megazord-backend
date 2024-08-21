#!/bin/bash

# Применяем миграции
python src/manage.py migrate

# Запускаем Django сервер
uvicorn --app-dir src megazord.asgi:application --host 0.0.0.0 --port 8000
