"""Transcription route for audio processing."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import time
from typing import TYPE_CHECKING

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

from ..core import ConversationEvent, ConversationUtterance
from ..core.config import SPEAKER_ASSOCIATION_WINDOW_SECONDS

if TYPE_CHECKING:
    from ..audio import AudioPipeline
    from ..services.conversation_stream import ConversationEventBus
    from ..services.convex_client import ConvexService

logger = logging.getLogger("webrtc.transcription")

router = APIRouter(tags=["transcription"])

_audio_pipeline: "AudioPipeline | None" = None
_conversation_bus: "ConversationEventBus | None" = None
_convex_service: "ConvexService | None" = None
_latest_speaker_info: dict = {"id": None, "name": None, "ts": 0}


def init_transcription_routes(
    audio_pipeline: "AudioPipeline",
    conversation_bus: "ConversationEventBus",
    convex_service: "ConvexService",
) -> None:
    """Initialize transcription routes with required services."""
    global _audio_pipeline, _conversation_bus, _convex_service
    _audio_pipeline = audio_pipeline
    _conversation_bus = conversation_bus
    _convex_service = convex_service


def get_latest_speaker_info() -> dict:
    """Get the latest speaker info for video correlation."""
    return _latest_speaker_info.copy()


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio file and publish to conversation bus."""
    from uuid import uuid4

    from openai import AsyncOpenAI

    if _audio_pipeline is None:
        raise RuntimeError("Transcription routes not initialized")

    logger.info("Received audio upload: %s (%s)", audio.filename, audio.content_type)

    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            input_path = tmp.name

        output_path = input_path.replace(".webm", ".wav")
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "quiet", "-i", input_path,
                    "-ar", "16000", "-ac", "1", "-f", "wav", output_path
                ],
                capture_output=True,
                timeout=30,
                stdin=subprocess.DEVNULL,
            )
            if result.returncode != 0:
                logger.error("FFmpeg error: %s", result.stderr.decode())
                raise HTTPException(status_code=500, detail="Audio conversion failed")
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="FFmpeg not installed")

        import wave
        with wave.open(output_path, "rb") as wav:
            frames = wav.readframes(wav.getnframes())
            audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32767.0

        os.unlink(input_path)
        os.unlink(output_path)

        segments = await _audio_pipeline._transcribe_audio(audio_data)

        if segments:
            text = " ".join(seg.text for seg in segments)
            logger.info("Transcription result: %s", text[:100])

            session_id = f"record-{uuid4().hex[:8]}"
            conversation_id = f"{session_id}-conv{uuid4().hex[:6]}"

            extracted_name = "New Person"
            relationship = "Someone you know"
            summary = text[:200] if len(text) > 200 else text

            try:
                groq_client = AsyncOpenAI(
                    api_key=os.getenv("GROQ_API_KEY"),
                    base_url="https://api.groq.com/openai/v1"
                )

                llm_response = await groq_client.chat.completions.create(
                    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    messages=[
                        {"role": "system", "content": """You are a person identification AI. Extract the person's name from the conversation.
Return ONLY JSON: {"name": "extracted name or 'Unknown'", "relationship": "relationship like 'Your friend' or 'Visitor'", "summary": "brief summary"}
If no name is mentioned, return "Unknown"."""},
                        {"role": "user", "content": f"Extract person details from: {text}"}
                    ],
                    temperature=0.2,
                    max_tokens=150
                )

                result = json.loads(llm_response.choices[0].message.content.strip())
                extracted_name = result.get("name", "Unknown")
                relationship = result.get("relationship", "Visitor")
                summary = result.get("summary", text[:100])
                logger.info("LLM extracted name: %s (%s)", extracted_name, relationship)
            except Exception as e:
                logger.warning("LLM name extraction failed: %s", e)

            speaker_id = None
            final_name = extracted_name

            try:
                from ..services.llm_service import get_llm_service
                llm_service = get_llm_service()

                logger.info("Processing transcript for LLM: '%s'", text)

                updates = await llm_service.extract_relationship_info([ConversationUtterance(speaker="User", text=text)])
                if updates:
                    logger.info("LLM Raw Updates: %s", updates)
                    if updates.get("name"):
                        extracted_name = updates["name"]
                    if updates.get("relationship"):
                        relationship = updates["relationship"]
                else:
                    logger.info("LLM returned no updates.")

                if extracted_name and extracted_name not in ["Unknown", "New Person"]:
                    existing_speaker = await _convex_service.get_speaker_by_name(extracted_name)
                    if existing_speaker:
                        speaker_id = existing_speaker.get("_id")
                        final_name = existing_speaker.get("name", extracted_name)
                        logger.info("Found existing speaker: %s (%s)", final_name, speaker_id)

                        await _convex_service.save_conversation(
                            speaker_id=speaker_id,
                            transcript=text,
                            duration_seconds=10.0,
                            summary=summary,
                        )

                        if relationship and relationship != "Someone you know":
                            logger.info("Updating existing speaker relationship to: %s", relationship)
                            await _convex_service.update_speaker_profile(
                                speaker_id=speaker_id,
                                relationship=relationship
                            )
                        else:
                            logger.info("Skipping relationship update (Current: %s)", relationship)

                    else:
                        speaker_result = await _convex_service.find_or_create_speaker(
                            embedding=[0.0] * 512,
                            name=extracted_name,
                        )
                        if speaker_result:
                            speaker_id = speaker_result.get("speakerId")
                            logger.info("Created new speaker: %s (%s)", extracted_name, speaker_id)
                            await _convex_service.save_conversation(
                                speaker_id=speaker_id,
                                transcript=text,
                                duration_seconds=10.0,
                                summary=summary,
                            )
                            if relationship and relationship != "Someone you know":
                                logger.info("Setting new speaker relationship to: %s", relationship)
                                await _convex_service.update_speaker_profile(
                                    speaker_id=speaker_id,
                                    relationship=relationship
                                )
                else:
                    logger.info("No name extracted (got '%s'), looking up recent speakers...", extracted_name)
                    recent_speakers = await _convex_service.list_speakers()

                    if recent_speakers and len(recent_speakers) > 0:
                        recent = recent_speakers[0]
                        speaker_id = recent.get("_id")
                        final_name = recent.get("name", "Unknown")
                        logger.info("Using most recent speaker: %s (%s)", final_name, speaker_id)

                        await _convex_service.save_conversation(
                            speaker_id=speaker_id,
                            transcript=text,
                            duration_seconds=10.0,
                            summary=summary,
                        )

                        if relationship and relationship != "Someone you know":
                            logger.info("Updating recent speaker relationship to: %s", relationship)
                            await _convex_service.update_speaker_profile(
                                speaker_id=speaker_id,
                                relationship=relationship
                            )
                    else:
                        logger.info("No speakers found, creating Unknown Person")
                        speaker_result = await _convex_service.find_or_create_speaker(
                            embedding=[0.0] * 512,
                            name="Unknown Person",
                        )
                        if speaker_result:
                            speaker_id = speaker_result.get("speakerId")
                            final_name = "Unknown Person"
                            await _convex_service.save_conversation(
                                speaker_id=speaker_id,
                                transcript=text,
                                duration_seconds=10.0,
                                summary=summary,
                            )
                            if relationship and relationship != "Someone you know":
                                logger.info("Setting anonymous speaker relationship to: %s", relationship)
                                await _convex_service.update_speaker_profile(
                                    speaker_id=speaker_id,
                                    relationship=relationship
                                )

            except Exception as e:
                logger.warning("Convex speaker operations failed: %s", e)

            event = ConversationEvent(
                event_type="CONVERSATION_END",
                person_id=speaker_id or f"speaker_record_{uuid4().hex[:6]}",
                conversation_id=conversation_id,
                session_id=session_id,
                conversation=[ConversationUtterance(speaker=final_name, text=text)],
            )

            try:
                await _conversation_bus.publish(event)
                logger.info("Published CONVERSATION_END for %s (session=%s)", final_name, session_id)

                if speaker_id:
                    global _latest_speaker_info
                    _latest_speaker_info = {
                        "id": speaker_id,
                        "name": final_name,
                        "ts": time.time()
                    }
                    logger.info("Updated active speaker: %s (%s)", final_name, speaker_id)

            except Exception as e:
                logger.warning("Failed to publish conversation event: %s", e)

            return {
                "text": text,
                "segments": len(segments),
                "speaker_id": speaker_id,
                "name": final_name,
                "relationship": relationship,
            }
        else:
            return {"text": "", "segments": 0}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Transcription failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
