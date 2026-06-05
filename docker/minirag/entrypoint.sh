#!/bin/bash

set -e

echo "Running database migrations..."
cd /app/models/db_schemes/minirag
alembic upgrade head

cd /app

if [ "$#" -eq 0 ]; then
    set -- uvicorn main:app --host 0.0.0.0 --port 8000
fi

exec "$@"
