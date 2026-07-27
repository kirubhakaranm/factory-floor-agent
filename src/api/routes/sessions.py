"""Session management endpoints — backed by Postgres conversation_messages table."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends

from src.api.dependencies import get_message_history
from src.api.schemas import SessionDetail, SessionInfo, SessionMessage

router = APIRouter(prefix="/api", tags=["sessions"])
logger = logging.getLogger("primeev.sessions")


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(
    history: dict = Depends(get_message_history),
) -> list[SessionInfo]:
    """List sessions — reads from Postgres, falls back to in-memory for the active session."""
    results: dict[str, SessionInfo] = {}

    # Postgres: all completed sessions
    try:
        from src.db.postgres.queries import sync_list_sessions
        for row in sync_list_sessions(limit=50):
            sid = row["session_id"]
            results[sid] = SessionInfo(
                session_id=sid,
                created_at=row["created_at"],
                message_count=int(row["message_count"]),
            )
    except Exception as exc:
        logger.warning("Could not read sessions from Postgres: %s", exc)

    # In-memory: pick up any session that is currently streaming (not yet committed)
    for sid, messages in history.items():
        if sid not in results and messages:
            results[sid] = SessionInfo(
                session_id=sid,
                created_at=messages[0].get("timestamp", datetime.now()),
                message_count=len(messages),
            )

    return sorted(results.values(), key=lambda s: s.created_at, reverse=True)[:50]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    history: dict = Depends(get_message_history),
) -> SessionDetail | dict:
    """Get full message history for a session — Postgres first, in-memory fallback."""
    messages: list[SessionMessage] = []

    # Try Postgres first
    try:
        from src.db.postgres.queries import sync_get_session_messages
        rows = sync_get_session_messages(session_id)
        if rows:
            messages = [
                SessionMessage(role=r["role"], content=r["content"], timestamp=r["timestamp"])
                for r in rows
            ]
    except Exception as exc:
        logger.warning("Could not read session from Postgres: %s", exc)

    # Fall back to in-memory if Postgres had nothing (e.g. session still streaming)
    if not messages:
        raw = history.get(session_id, [])
        if not raw:
            return {"error": f"Session {session_id} not found"}
        messages = [
            SessionMessage(role=m["role"], content=m["content"], timestamp=m["timestamp"])
            for m in raw
        ]

    created_at = messages[0].timestamp if messages else datetime.now()
    return SessionDetail(
        session_id=session_id,
        created_at=created_at,
        messages=messages,
    )
