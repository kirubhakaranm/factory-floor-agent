-- PrimeEV Motors — Postgres schema initialization
-- This runs on first docker compose up via docker-entrypoint-initdb.d

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tables are created via Alembic migrations in production.
-- This file ensures the database exists and extensions are loaded.

-- Conversation history (durable, survives API restarts)
CREATE TABLE IF NOT EXISTS conversation_messages (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_conv_msgs_session ON conversation_messages(session_id, created_at);

