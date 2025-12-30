FROM python:3.12-slim AS runtime

WORKDIR /app/backend

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:/root/.local/bin:$PATH"\
    PYTHONPATH="/app:$PYTHONPATH" \
    UV_COMPILE_BYTECODE=1


RUN apt-get update && \
    apt-get install -y build-essential libpq-dev gettext libmagic-dev libjpeg-dev zlib1g-dev gdb && \
    apt-get purge -y --auto-remove -o APT:AutoRemove:RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./ /app
RUN uv sync --frozen --no-cache

COPY .docker/dev/app/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Переменные окружения для gunicorn (можно переопределить через docker-compose)
ENV GUNICORN_WORKERS=4 \
    GUNICORN_THREADS=2 \
    GUNICORN_BIND=0.0.0.0:8000 \
    GUNICORN_TIMEOUT=120

# Переменные окружения для тестового суперпользователя (можно переопределить через docker-compose)
ENV DJANGO_SUPERUSER_USERNAME=admin \
    DJANGO_SUPERUSER_EMAIL=admin@example.com \
    DJANGO_SUPERUSER_PASSWORD=admin

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]

CMD uv run gunicorn \
    --workers ${GUNICORN_WORKERS} \
    --threads ${GUNICORN_THREADS} \
    --bind ${GUNICORN_BIND} \
    --timeout ${GUNICORN_TIMEOUT} \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    org.entrypoints.main.wsgi:application