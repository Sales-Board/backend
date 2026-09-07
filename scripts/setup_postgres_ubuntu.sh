#!/usr/bin/env bash
set -euo pipefail

DB_NAME="lead_intelligence"
DB_USER="postgres"
DB_PASS="postgres"

echo "[1/5] Installing PostgreSQL packages"
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

echo "[2/5] Enabling and starting PostgreSQL service"
sudo systemctl enable postgresql
sudo systemctl start postgresql

echo "[3/5] Ensuring postgres password"
sudo -u postgres psql -v ON_ERROR_STOP=1 -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"

echo "[4/5] Creating database if missing"
sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || \
  sudo -u postgres createdb -O "${DB_USER}" "${DB_NAME}"

echo "[5/5] Verifying connectivity"
PGPASSWORD="${DB_PASS}" psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT current_database(), current_user;"

echo "PostgreSQL setup complete."
