#!/bin/sh
set -e

echo "Initializing database..."
python -c "from app.db.session import init_db; init_db()"
echo "Database initialized"

echo "Starting uvicorn..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --proxy-headers \
    --forwarded-allow-ips='*'
