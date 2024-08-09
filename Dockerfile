FROM python:3.12.4-slim

# Установим системные зависимости для Django
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Установим рабочий каталог
WORKDIR /app

# Скопируем все файлы проекта в контейнер
COPY . .

# Установим зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Установим переменную окружения для Django
ENV DJANGO_SETTINGS_MODULE=megazord.settings

# Сделаем скрипт исполняемым
RUN chmod +x ./entrypoint.sh

# Укажем ENTRYPOINT для контейнера
ENTRYPOINT ["./entrypoint.sh"]

# Откроем порт для доступа к приложению Django
EXPOSE 8000
