#!/bin/sh
set -e

# Run Alembic migrations before starting the server
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

exec "$@"
