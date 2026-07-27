"""Chat endpoint — SSE streaming of agent responses with citation extraction."""

import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_message_history, get_runner, get_session_service
from src.api.schemas import ChatRequest, ReformatRequest
from src.monitoring.metrics import (
    AGENT_ERRORS,
    AGENT_REQUEST_DURATION,
    AGENT_REQUESTS,
    AGENT_TOOL_CALLS,
)

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger("primeev.chat")

# Claude Sonnet 4 pricing per token
_INPUT_RATE = 3.0e-6
_OUTPUT_RATE = 15.0e-6
_CACHE_RATE = 0.3e-6

# RAG tool names whose responses contain citable source chunks
_RAG_TOOLS = {
    "search_sop",
    "search_equipment_manual",
    "search_specification",
    "search_past_issues",
    "search_fmea_risks",
    "search_case_study",
}

_MODE_INSTRUCTIONS: dict[str, str] = {
    "concise": (
        "\n\n[RESPONSE FORMAT: Concise mode. "
        "Reply with one short bullet per key finding. No elaboration. Max 8 bullets.]"
    ),
    "summarized": (
        "\n\n[RESPONSE FORMAT: Summarized mode. "
        "Reply in 3-4 lines of prose covering only the most critical findings. No bullet points.]"
    ),
}

_DOC_TYPE_LABELS = {
    "sop": "Standard Operating Procedure",
    "manual": "Equipment Manual",
    "spec": "Specification",
    "troubleshooting": "Troubleshooting Record",
    "fmea": "FMEA",
    "case_study": "Case Study",
}


def _extract_citations(tool_name: str, response: dict, counter: int) -> list[dict]:
    """Pull citation metadata out of a RAG tool's function_response."""
    if tool_name not in _RAG_TOOLS:
        return []

    raw = response.get("result", response) if isinstance(response, dict) else response
    chunks = raw if isinstance(raw, list) else []

    citations = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        meta = chunk.get("metadata") or {}
        source_path = meta.get("source", "")
        doc_type = meta.get("doc_type", "")

        title = (
            meta.get("title")
            or meta.get("section")
            or (Path(source_path).stem.replace("-", " ").replace("_", " ").title() if source_path else "")
            or _DOC_TYPE_LABELS.get(doc_type, "Document")
        )

        counter += 1
        citations.append({
            "id": counter,
            "source_type": "rag",
            "doc_type": doc_type,
            "doc_type_label": _DOC_TYPE_LABELS.get(doc_type, doc_type.title()),
            "title": title,
            "path": source_path,
            "excerpt": chunk.get("text", "")[:300].strip(),
            "station_id": meta.get("station_id") or None,
            "relevance": round(1 - (chunk.get("distance") or 0), 3),
        })

    return citations


def _extract_usage(event) -> tuple[int, int, int]:
    """Extract (input_tokens, output_tokens, cache_read_tokens) from an ADK event."""
    usage = getattr(event, "usage_metadata", None)
    if usage is None:
        return 0, 0, 0
    # Gemini-style field names (ADK wraps these)
    inp = getattr(usage, "prompt_token_count", 0) or getattr(usage, "input_tokens", 0) or 0
    out = getattr(usage, "candidates_token_count", 0) or getattr(usage, "output_tokens", 0) or 0
    cache = getattr(usage, "cached_content_token_count", 0) or getattr(usage, "cache_read_input_tokens", 0) or 0
    return int(inp), int(out), int(cache)


@router.post("/chat")
async def chat(
    request: ChatRequest,
    runner: Runner = Depends(get_runner),
    session_service: InMemorySessionService = Depends(get_session_service),
    history: dict = Depends(get_message_history),
) -> EventSourceResponse:
    """Send a message to the factory floor agent and stream the response via SSE.

    SSE event types:
      session     — {"session_id": str}
      token       — {"text": str, "agent": str, "final": bool}
      tool_call   — {"tool": str, "args": dict, "agent": str}
      tool_result — {"tool": str, "agent": str, "result_snippet": str, "latency_ms": int}
      citation    — {"id": int, "title": str, "doc_type": str, "path": str,
                     "excerpt": str, "station_id": str|null, "relevance": float}
      usage       — {"input_tokens": int, "output_tokens": int, "cache_read_tokens": int,
                     "cost_usd": float, "total_latency_ms": int, "ttft_ms": int|null,
                     "tool_call_count": int, "llm_reentry_count": int, "context_tokens_used": int}
      done        — {"session_id": str, "response_length": int, "citation_count": int,
                     "elapsed_s": float}
      error       — {"message": str}
    """
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

    mode_suffix = _MODE_INSTRUCTIONS.get(request.response_mode, "")
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=request.message + mode_suffix)],
    )

    async def event_stream() -> AsyncGenerator[dict, None]:
        """Stream SSE events for the agent run: session, token, tool_call, tool_result, usage, done."""
        yield {"event": "session", "data": json.dumps({"session_id": session_id})}

        full_response = ""
        all_citations: list[dict] = []
        citation_counter = 0
        start_time = time.monotonic()
        start_dt = datetime.utcnow()
        agent_label = "root_agent"

        # ── Telemetry accumulators ────────────────────────────────────────────
        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_tokens = 0
        llm_reentry_count = 0
        ttft_ms: int | None = None
        # tool_trace: one entry per non-routing tool response
        tool_trace: list[dict] = []
        # buffer args keyed by tool name for pairing call→response
        _tool_args: dict[str, dict] = {}
        _tool_call_time: dict[str, float] = {}

        AGENT_REQUESTS.labels(agent_name=agent_label).inc()

        # Store user turn in history
        history.setdefault(session_id, []).append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now(),
        })

        error_type: str | None = None

        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message,
            ):
                author = event.author or agent_label

                # Accumulate token usage from each model event
                inp, out, cache = _extract_usage(event)
                total_input_tokens += inp
                total_output_tokens += out
                total_cache_tokens += cache

                # Count LLM re-entries (each event with model-generated content)
                if event.get_function_calls() or (event.content and event.content.parts):
                    llm_reentry_count += 1

                # ── Tool calls ────────────────────────────────────────────────
                for fc in (event.get_function_calls() or []):
                    args = dict(fc.args) if fc.args else {}

                    if fc.name == "transfer_to_agent":
                        target = (
                            args.get("agent_name")
                            or args.get("agent")
                            or next((v for v in args.values() if isinstance(v, str)), "")
                        )
                        AGENT_TOOL_CALLS.labels(agent_name=author, tool_name="transfer_to_agent").inc()
                        yield {
                            "event": "tool_call",
                            "data": json.dumps({"tool": "route", "args": {"target": target}, "agent": author}),
                        }
                        continue

                    AGENT_TOOL_CALLS.labels(agent_name=author, tool_name=fc.name).inc()
                    _tool_args[fc.name] = args
                    _tool_call_time[fc.name] = time.monotonic()
                    yield {
                        "event": "tool_call",
                        "data": json.dumps({"tool": fc.name, "args": args, "agent": author}),
                    }

                # ── Tool responses ────────────────────────────────────────────
                for fr in (event.get_function_responses() or []):
                    tool_name = fr.name
                    response_data = fr.response or {}
                    result_text = str(response_data)

                    call_time = _tool_call_time.pop(tool_name, start_time)
                    latency_ms = int((time.monotonic() - call_time) * 1000)
                    had_error = "TERMINAL" in result_text
                    result_snippet = result_text[:300]

                    tool_trace.append({
                        "seq": len(tool_trace) + 1,
                        "tool": tool_name,
                        "agent": author,
                        "args": _tool_args.pop(tool_name, {}),
                        "latency_ms": latency_ms,
                        "result_snippet": result_snippet,
                        "result_token_count": len(result_text) // 4,
                        "had_error": had_error,
                    })

                    new_citations = _extract_citations(tool_name, response_data, citation_counter)
                    if new_citations:
                        citation_counter += len(new_citations)
                        all_citations.extend(new_citations)

                    yield {
                        "event": "tool_result",
                        "data": json.dumps({
                            "tool": tool_name,
                            "agent": author,
                            "result_snippet": result_snippet,
                            "latency_ms": latency_ms,
                            "had_error": had_error,
                        }),
                    }

                # ── Text output ───────────────────────────────────────────────
                if event.content and event.content.parts:
                    is_final = event.is_final_response()
                    for part in event.content.parts:
                        if part.text:
                            if ttft_ms is None:
                                ttft_ms = int((time.monotonic() - start_time) * 1000)
                            full_response += part.text
                            yield {
                                "event": "token",
                                "data": json.dumps({"text": part.text, "agent": author, "final": is_final}),
                            }

        except Exception as exc:
            error_type = type(exc).__name__
            AGENT_ERRORS.labels(agent_name=agent_label, error_type=error_type).inc()
            yield {"event": "error", "data": json.dumps({"message": str(exc)[:200]})}
            return

        finally:
            elapsed = time.monotonic() - start_time
            AGENT_REQUEST_DURATION.labels(agent_name=agent_label).observe(elapsed)

        # Store assistant turn in history
        if full_response:
            history[session_id].append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now(),
            })

        for cit in all_citations:
            yield {"event": "citation", "data": json.dumps(cit)}

        # ── Usage event ───────────────────────────────────────────────────────
        total_latency_ms = int(elapsed * 1000)
        tool_latency_ms = sum(t["latency_ms"] for t in tool_trace)
        cost_usd = (
            total_input_tokens * _INPUT_RATE
            + total_output_tokens * _OUTPUT_RATE
            + total_cache_tokens * _CACHE_RATE
        )
        context_tokens_used = total_input_tokens  # best available proxy

        yield {
            "event": "usage",
            "data": json.dumps({
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "cache_read_tokens": total_cache_tokens,
                "cost_usd": round(cost_usd, 6),
                "total_latency_ms": total_latency_ms,
                "ttft_ms": ttft_ms,
                "tool_call_count": len(tool_trace),
                "llm_reentry_count": llm_reentry_count,
                "context_tokens_used": context_tokens_used,
                "tool_latency_ms": tool_latency_ms,
            }),
        }

        yield {
            "event": "done",
            "data": json.dumps({
                "session_id": session_id,
                "response_length": len(full_response),
                "citation_count": len(all_citations),
                "elapsed_s": round(elapsed, 2),
            }),
        }

        # ── Persist messages to Postgres (durable conversation history) ─────────
        try:
            from src.db.postgres.queries import sync_write_message
            sync_write_message(session_id, "user", request.message, start_dt)
            if full_response:
                sync_write_message(session_id, "assistant", full_response, datetime.utcnow())
        except Exception as msg_exc:
            logger.warning("Failed to persist conversation messages: %s", msg_exc)

        # ── Persist to ClickHouse (for Grafana time-series analytics) ─────────
        try:
            import uuid as _uuid
            from src.db.clickhouse.client import get_clickhouse_client
            ch = get_clickhouse_client()
            ch.insert(
                "primeev_telemetry.agent_interactions",
                [[
                    datetime.utcnow(),
                    str(_uuid.uuid4()),
                    session_id,
                    agent_label,
                    total_input_tokens,
                    total_output_tokens,
                    total_cache_tokens,
                    cost_usd,
                    ttft_ms or 0,
                    total_latency_ms,
                    len(tool_trace),
                    1 if error_type else 0,
                    len(full_response),
                ]],
                column_names=[
                    "timestamp", "interaction_id", "session_id", "sub_agent",
                    "input_tokens", "output_tokens", "cache_read_tokens", "cost_usd",
                    "ttft_ms", "total_latency_ms", "tool_call_count", "had_error",
                    "response_length_chars",
                ],
            )
        except Exception as ch_exc:
            logger.warning("Failed to persist interaction to ClickHouse: %s", ch_exc)

    return EventSourceResponse(event_stream())


class FollowUpsRequest(BaseModel):
    """Request body for the follow-up questions generation endpoint."""

    response_text: str


@router.post("/chat/follow-ups")
async def generate_follow_ups(request: FollowUpsRequest) -> dict:
    """Generate 3 contextual follow-up questions for the last agent response using Haiku."""
    import anthropic
    from src.config.settings import settings

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": (
                "You are an assistant for a manufacturing factory floor AI agent used by engineers. "
                "Based on the following agent response, suggest exactly 3 concise follow-up questions "
                "an engineer would naturally ask next. Each question should be specific to the content "
                "of the response — not generic. Return only a JSON array of 3 short question strings, "
                "no explanation, no markdown.\n\n"
                f"Agent response:\n{request.response_text[:1500]}"
            ),
        }],
    )
    import json as _json
    import re as _re
    raw = message.content[0].text.strip()
    logger.info("follow-ups raw Haiku output: %s", raw[:300])
    try:
        # Strip markdown code fences if Haiku wrapped the JSON
        match = _re.search(r"\[.*?\]", raw, _re.DOTALL)
        parsed = _json.loads(match.group(0)) if match else _json.loads(raw)
        if isinstance(parsed, list):
            suggestions = [s for s in parsed if isinstance(s, str)][:3]
        else:
            suggestions = []
    except Exception:
        logger.warning("Failed to parse follow-up suggestions from: %s", raw[:200])
        suggestions = []
    logger.info("follow-ups returning %d suggestions", len(suggestions))
    return {"suggestions": suggestions}


_REFORMAT_PROMPTS = {
    "summarized": (
        "Compress the following agent response into 3-4 lines of prose. "
        "Keep only the most critical findings and any recommended actions. "
        "No bullet points, no headers — just concise prose."
    ),
    "concise": (
        "Reformat the following agent response as a bullet list. "
        "One short line per key finding, maximum 8 bullets. No elaboration."
    ),
    "detailed": (
        "Expand the following agent response with more supporting detail, "
        "data context, and reasoning for each finding."
    ),
}


@router.post("/chat/reformat")
async def reformat_response(request: ReformatRequest) -> dict:
    """Reformat an existing response to a different verbosity level using Haiku."""
    import anthropic
    from src.config.settings import settings

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    instruction = _REFORMAT_PROMPTS[request.target_mode]

    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"{instruction}\n\n---\n\n{request.original_text}",
        }],
    )
    return {"text": message.content[0].text, "mode": request.target_mode}
