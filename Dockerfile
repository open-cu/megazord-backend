FROM python:3.12.4-slim
LABEL description="Megazord backend image"

USER root
ENV APP_USER=app
ARG ENVIRONMENT=production
ENV ENVIRONMENT=${ENVIRONMENT}
ENV DJANGO_SETTINGS_MODULE="megazord.settings"

ARG WORK_DIR=/opt
ENV PYTHONPATH=$WORK_DIR

WORKDIR $WORK_DIR

COPY requirements.txt requirements.tests.txt ./
RUN pip install -r requirements.txt -r requirements.tests.txt

COPY . .

RUN \
    apt-get update && apt-get install -y --no-install-recommends \
    make \
    && apt-get autoclean && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    $APP_USER \
    && chown $APP_USER:$APP_USER $WORK_DIR

USER $APP_USER

EXPOSE 8000

CMD ["python", "src/main.py"]
