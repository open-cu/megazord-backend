FROM python:3.12.4-slim

# Set the working directory
WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for Django settings module
ENV DJANGO_SETTINGS_MODULE=megazord.settings

# Collect static files
#RUN python manage.py collectstatic --noinput

#Переехать на postgresql

# Делаем скрипт исполняемым
RUN chmod +x ./entrypoint.sh

# Указываем ENTRYPOINT для контейнера
ENTRYPOINT ["./entrypoint.sh"]