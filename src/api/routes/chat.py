"""Chat endpoint — SSE streaming of agent responses."""

import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_runner, get_session_service
from src.api.schemas import ChatRequest

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(
    request: ChatRequest,
    runner: Runner = Depends(get_runner),
    session_service: InMemorySessionService = Depends(get_session_service),
) -> EventSourceResponse:
    """Send a message to the factory floor agent and stream the response via SSE."""
    session_id = request.session_id or str(uuid.uuid4())
    user_id = "factory_user"

    session = await session_service.get_session(
        app_name="primeev_factory",
        user_id=user_id,
        session_id=session_id,
    )
    if session is None:
        session = await session_service.create_session(
            app_name="primeev_factory",
            user_id=user_id,
            session_id=session_id,
        )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=request.message)],
    )

    async def event_stream() -> AsyncGenerator[dict, None]:
        yield {
            "event": "session",
            "data": json.dumps({"session_id": session_id}),
        }

        full_response = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        full_response += part.text
                        yield {
                            "event": "token",
                            "data": json.dumps({
                                "text": part.text,
                                "agent": event.author,
                            }),
                        }

                    if part.function_call:
                        yield {
                            "event": "tool_call",
                            "data": json.dumps({
                                "tool": part.function_call.name,
                                "args": dict(part.function_call.args) if part.function_call.args else {},
                                "agent": event.author,
                            }),
                        }

                    if part.function_response:
                        yield {
                            "event": "tool_result",
                            "data": json.dumps({
                                "tool": part.function_response.name,
                                "agent": event.author,
                            }),
                        }

        yield {
            "event": "done",
            "data": json.dumps({
                "session_id": session_id,
                "response_length": len(full_response),
            }),
        }

    return EventSourceResponse(event_stream())
