#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -x ./.venv/bin/python ]]; then
  echo "Missing backend virtual environment at .venv"
  exit 1
fi

echo "[1/4] Running Alembic migrations"
./.venv/bin/alembic upgrade head

echo "[2/4] Checking database connectivity via psycopg"
./.venv/bin/python - <<'PY'
import psycopg
from app.core.config import settings

with psycopg.connect(settings.database_url.replace('+psycopg', '')) as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT 1')
        print('db-check:', cur.fetchone()[0])
PY

echo "[3/4] Running fast sanity tests"
./.venv/bin/pytest -q tests/test_health.py tests/test_customers.py --disable-warnings --maxfail=1

echo "[4/4] Backend DB bootstrap completed"
