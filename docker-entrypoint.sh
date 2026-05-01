#!/bin/sh
# BrainCell entrypoint — runs Alembic migrations before starting the application

set -e

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting application..."
exec "$@"
