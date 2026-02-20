"""WebRTC routes for video/audio streaming."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Set
from uuid import uuid4

from aiortc import RTCPeerConnection, RTCSessionDescription
from fastapi import APIRouter
from pydantic import BaseModel

from ..core import ConversationEvent, ConversationUtterance
from ..core.config import FACE_REPUBLISH_INTERVAL_SECONDS, SPEAKER_ASSOCIATION_WINDOW_SECONDS

if TYPE_CHECKING:
    from ..audio import AudioPipeline
    from ..services.conversation_stream import ConversationEventBus
    from ..services.convex_client import ConvexService
    from ..video.pipeline import VideoPipeline

logger = logging.getLogger("webrtc.webrtc")

router = APIRouter(tags=["webrtc"])

pcs: Set[RTCPeerConnection] = set()

_audio_pipeline: "AudioPipeline | None" = None
_conversation_bus: "ConversationEventBus | None" = None
_video_pipeline: "VideoPipeline | None" = None
_convex_service: "ConvexService | None" = None
_latest_speaker_info_getter = None


class SDPModel(BaseModel):
    sdp: str
    type: str


def init_webrtc_routes(
    audio_pipeline: "AudioPipeline",
    conversation_bus: "ConversationEventBus",
    video_pipeline: "VideoPipeline",
    convex_service: "ConvexService",
    latest_speaker_info_getter=None,
) -> None:
    """Initialize WebRTC routes with required services."""
    global _audio_pipeline, _conversation_bus, _video_pipeline, _convex_service, _latest_speaker_info_getter
    _audio_pipeline = audio_pipeline
    _conversation_bus = conversation_bus
    _video_pipeline = video_pipeline
    _convex_service = convex_service
    _latest_speaker_info_getter = latest_speaker_info_getter


@router.post("/offer", response_model=SDPModel)
async def offer(session: SDPModel) -> SDPModel:
    """Handle WebRTC SDP offer and return answer."""
    logger.info("Received SDP offer payload length=%d", len(session.sdp))
    pc = RTCPeerConnection()
    pcs.add(pc)
    session_id = f"sess-{uuid4().hex[:8]}"

    @pc.on("track")
    def on_track(track) -> None:
        if track.kind == "audio":
            logger.info("Session %s audio track ready", session_id)

        if track.kind == "audio":
            asyncio.create_task(_consume_audio(track, session_id))
        else:
            asyncio.create_task(_consume_video(track, session_id))

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        if pc.connectionState in {"failed", "closed"}:
            await pc.close()
            pcs.discard(pc)

    logger.info("Processing SDP offer for %s", session_id)
    offer_sdp = RTCSessionDescription(sdp=session.sdp, type=session.type)
    await pc.setRemoteDescription(offer_sdp)

    for transceiver in pc.getTransceivers():
        if transceiver.kind in {"audio", "video"}:
            transceiver.direction = "recvonly"

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    while pc.iceGatheringState != "complete":
        await asyncio.sleep(0.1)

    logger.info("Returning answer for PeerConnection %s", id(pc))
    return SDPModel(sdp=pc.localDescription.sdp, type=pc.localDescription.type)


async def _consume_audio(track, session_id: str) -> None:
    """Consume audio track from WebRTC."""
    from datetime import datetime

    from ..core import AudioChunk

    last_sample_rate: int | None = None
    while True:
        try:
            frame = await track.recv()
            if not frame.planes:
                continue
            plane = frame.planes[0]
            try:
                data = plane.to_bytes()
            except AttributeError:
                data = bytes(plane)
            sample_rate = getattr(frame, "sample_rate", None) or 16000
            last_sample_rate = sample_rate
            chunk = AudioChunk(
                session_id=session_id,
                data=data,
                sample_rate=sample_rate,
                timestamp=datetime.utcnow(),
            )
        except Exception:
            break

        if last_sample_rate:
            try:
                if _audio_pipeline is not None:
                    await _audio_pipeline.flush_session(session_id, last_sample_rate)
            except Exception as exc:
                logger.exception(
                    "Error flushing audio buffer for session %s: %s",
                    session_id,
                    exc,
                )


async def _consume_video(track, session_id: str) -> None:
    """Consume video track for face recognition."""
    import numpy as np

    if _video_pipeline is None or _conversation_bus is None:
        return

    frame_count = 0
    last_face_id = None
    last_publish_ts = 0.0

    while True:
        try:
            frame = await track.recv()
            frame_count += 1

            if frame_count % 30 != 0:
                continue

            if not _video_pipeline.is_available:
                continue

            try:
                img = frame.to_ndarray(format="bgr24")
                timestamp = time.time()

                detections = await _video_pipeline.process_frame(img, timestamp)

                if detections:
                    face = detections[0]
                    result = await _video_pipeline.match_face_to_speaker(face.embedding)

                    if result and result.get("found"):
                        speaker_id = result.get("speakerId")
                        name = result.get("speaker", {}).get("name", "Unknown")

                        now = time.time()
                        if speaker_id != last_face_id or (now - last_publish_ts > FACE_REPUBLISH_INTERVAL_SECONDS):
                            logger.info(
                                "Face recognized: %s (score=%.2f)",
                                name,
                                result.get("score", 0)
                            )
                            last_face_id = speaker_id
                            last_publish_ts = now

                            try:
                                event = ConversationEvent(
                                    event_type="FACE_DETECTED",
                                    person_id=speaker_id,
                                    conversation_id=uuid4().hex,
                                    session_id=session_id,
                                    conversation=[ConversationUtterance(speaker=name, text="")]
                                )
                                await _conversation_bus.publish(event)
                            except Exception as e:
                                logger.warning("Failed to publish face event: %s", e)

                    else:
                        latest_speaker_info = _latest_speaker_info_getter() if _latest_speaker_info_getter else {"ts": 0}
                        now = time.time()
                        last_active_ts = latest_speaker_info.get("ts", 0)

                        if now - last_active_ts < SPEAKER_ASSOCIATION_WINDOW_SECONDS and latest_speaker_info.get("id"):
                            active_id = latest_speaker_info["id"]
                            active_name = latest_speaker_info["name"]

                            logger.info("Associating unknown face with active speaker: %s", active_name)
                            success = await _video_pipeline.update_speaker_face(
                                active_id,
                                face.embedding
                            )
                            if success:
                                logger.info("Learned face for %s!", active_name)
                                last_face_id = active_id
                                try:
                                    event = ConversationEvent(
                                        event_type="FACE_DETECTED",
                                        person_id=active_id,
                                        conversation_id=uuid4().hex,
                                        session_id=session_id,
                                        conversation=[ConversationUtterance(speaker=active_name, text="")]
                                    )
                                    await _conversation_bus.publish(event)
                                except Exception:
                                    pass
                        else:
                            last_face_id = None
            except Exception as exc:
                logger.debug("Video frame processing error: %s", exc)
                continue

        except Exception:
            break


async def close_all_connections() -> None:
    """Close all peer connections on shutdown."""
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros, return_exceptions=True)
    pcs.clear()
    logger.info("Shutdown complete; closed all peer connections")
