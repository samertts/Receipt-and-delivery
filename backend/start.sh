#!/bin/sh
set -eu

ALEMBIC_CONFIG_PATH="${ALEMBIC_CONFIG:-/app/alembic.ini}"
echo "Applying database migrations with Alembic..."
alembic -c "$ALEMBIC_CONFIG_PATH" upgrade head
echo "Database migrations applied"

echo "Starting uvicorn..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${WEB_CONCURRENCY:-1}" \
    --log-level info \
    --proxy-headers \
    --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}"
