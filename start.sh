#!/usr/bin/env bash
# Start script for Render

set -e

export PATH="$HOME/.local/bin:/opt/render/.local/bin:$PATH"

cd backend

export PYTHONPATH="$(pwd)/..:${PYTHONPATH:-}"

echo "Running migrations..."
uv run python manage.py migrate --noinput

echo "Creating superuser if not exists..."
uv run python manage.py shell << 'PYTHON_EOF'
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser "{username}" created successfully')
else:
    print(f'Superuser "{username}" already exists')
PYTHON_EOF

echo "Starting Gunicorn..."
# PORT автоматически устанавливается Render
exec uv run gunicorn \
    --workers 2 \
    --threads 2 \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    org.entrypoints.main.wsgi:application

