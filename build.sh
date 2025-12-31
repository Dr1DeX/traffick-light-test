#!/usr/bin/env bash
# Build script for Render

set -e

echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:/opt/render/.local/bin:$PATH"

# Проверяем установку
if ! command -v uv &> /dev/null; then
    echo "Error: uv not found after installation"
    exit 1
fi

echo "uv version: $(uv --version)"

echo "Installing dependencies..."
cd backend

export PYTHONPATH="$(pwd)/..:${PYTHONPATH:-}"

uv sync --frozen

echo "Collecting static files..."
uv run python manage.py collectstatic --noinput

echo "Build completed successfully!"

