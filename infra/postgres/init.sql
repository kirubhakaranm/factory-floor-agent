-- PrimeEV Motors — Postgres schema initialization
-- This runs on first docker compose up via docker-entrypoint-initdb.d

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tables are created via Alembic migrations in production.
-- This file ensures the database exists and extensions are loaded.
