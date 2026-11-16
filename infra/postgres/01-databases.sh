#!/usr/bin/env bash
set -euo pipefail
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${POSTGRES_DB:-postgres}" \
  --set=career_password="$CAREER_DB_PASSWORD" --set=n8n_password="$N8N_DB_PASSWORD" <<'SQL'
CREATE ROLE career LOGIN PASSWORD :'career_password';
CREATE ROLE n8n LOGIN PASSWORD :'n8n_password';
CREATE DATABASE career OWNER career;
CREATE DATABASE n8n OWNER n8n;
REVOKE CONNECT ON DATABASE career FROM PUBLIC;
REVOKE CONNECT ON DATABASE n8n FROM PUBLIC;
GRANT CONNECT ON DATABASE career TO career;
GRANT CONNECT ON DATABASE n8n TO n8n;
SQL
