"""SSE streaming routes for real-time updates."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..core import ConversationEvent

if TYPE_CHECKING:
    from ..services.conversation_stream import ConversationEventBus
    from ..services.convex_client import ConvexService

logger = logging.getLogger("webrtc.streaming")

router = APIRouter(prefix="/stream", tags=["streaming"])

_event_bus: "ConversationEventBus | None" = None
_convex_service: "ConvexService | None" = None


def init_streaming_routes(
    event_bus: "ConversationEventBus",
    convex_service: "ConvexService",
) -> None:
    """Initialize streaming routes with required services."""
    global _event_bus, _convex_service
    _event_bus = event_bus
    _convex_service = convex_service


@router.get("/conversation")
async def stream_conversation() -> StreamingResponse:
    """Server-Sent Events stream of conversation metadata events."""
    if _event_bus is None:
        raise RuntimeError("Streaming routes not initialized")

    async def event_generator():
        queue = await _event_bus.subscribe()
        try:
            while True:
                try:
                    event = await queue.get()
                except asyncio.CancelledError:
                    break
                payload = event.model_dump_json()
                yield f"event: conversation\ndata: {payload}\n\n"
        finally:
            await _event_bus.unsubscribe(queue)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)


@router.get("/inference")
async def stream_inference() -> StreamingResponse:
    """SSE endpoint for streaming inference events to the frontend."""
    if _event_bus is None or _convex_service is None:
        raise RuntimeError("Streaming routes not initialized")

    async def event_generator():
        queue = await _event_bus.subscribe()
        try:
            while True:
                try:
                    event = await queue.get()
                except asyncio.CancelledError:
                    break

                display_name = "Unknown"
                if event.conversation and len(event.conversation) > 0:
                    display_name = event.conversation[0].speaker or "Unknown"

                description = " ".join(u.text for u in event.conversation) if event.conversation else ""
                relationship = "Guest"

                if event.person_id and not event.person_id.startswith("speaker_record_"):
                    try:
                        ctx = await _convex_service.get_person_context(event.person_id)
                        if ctx:
                            if ctx.get("relationship"):
                                relationship = ctx.get("relationship")

                            parts = []
                            if ctx.get("lastSeenText"):
                                parts.append(f"Last visited: {ctx['lastSeenText']}.")

                            if ctx.get("recentConversations") and len(ctx["recentConversations"]) > 0:
                                last_topic = ctx["recentConversations"][0].get("summary")
                                if last_topic:
                                    parts.append(f"Ask about: {last_topic}")
                            else:
                                parts.append("Ask about their day.")

                            if parts:
                                description = " ".join(parts)

                    except Exception as e:
                        logger.warning("Error fetching person context: %s", e)

                payload = {
                    "name": display_name,
                    "description": description,
                    "relationship": relationship,
                    "person_id": event.person_id,
                }
                yield f"event: inference\ndata: {json.dumps(payload)}\n\n"
        finally:
            await _event_bus.unsubscribe(queue)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)
