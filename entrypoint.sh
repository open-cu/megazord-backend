#!/bin/bash
# Скрипт для применения миграций и запуска сервера Django

# Применяем миграции
echo "Applying database migrations..."
python src/manage.py migrate

# Запускаем сервер Django
echo "Starting Django server..."
python src/manage.py runserver 0.0.0.0:8000