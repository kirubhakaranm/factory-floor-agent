"""Session management endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter

from src.api.schemas import SessionDetail, SessionInfo

router = APIRouter(prefix="/api", tags=["sessions"])

_sessions: dict[str, SessionInfo] = {}


@router.post("/sessions", response_model=SessionInfo)
async def create_session() -> SessionInfo:
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    info = SessionInfo(
        session_id=session_id,
        created_at=datetime.now(),
        message_count=0,
    )
    _sessions[session_id] = info
    return info


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions() -> list[SessionInfo]:
    """List recent sessions."""
    return sorted(_sessions.values(), key=lambda s: s.created_at, reverse=True)[:20]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str) -> SessionDetail | dict:
    """Get session details and message history."""
    if session_id not in _sessions:
        return {"error": f"Session {session_id} not found"}

    info = _sessions[session_id]
    return SessionDetail(
        session_id=info.session_id,
        created_at=info.created_at,
        messages=[],
    )
