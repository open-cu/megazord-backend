#!/bin/bash

# Применяем миграции
python src/manage.py migrate

# Запускаем Django сервер
python src/manage.py runserver 0.0.0.0:8000
