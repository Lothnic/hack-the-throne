"""FastAPI application providing WebRTC ingress and audio pipeline stubs."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .audio import AdaptiveDenoiser, AudioPipeline, PipelineConfig
from .core.config import CORS_ORIGINS, ROOT_DIR
from .services.conversation_stream import ConversationEventBus
from .services.convex_client import get_convex_service
from .video.pipeline import VideoPipeline, get_video_pipeline
from .routes import streaming_router, transcription_router, webrtc_router
from .routes.streaming import init_streaming_routes
from .routes.transcription import init_transcription_routes, get_latest_speaker_info
from .routes.webrtc import init_webrtc_routes, close_all_connections

logger = logging.getLogger("webrtc")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

app = FastAPI(title="Multimodal Ingress Prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv(ROOT_DIR / ".env")
os.environ.setdefault("TORCHAUDIO_PYTHON_ONLY", "1")

pipeline_config = PipelineConfig()
conversation_bus = ConversationEventBus()
audio_pipeline = AudioPipeline(
    denoiser=AdaptiveDenoiser(),
    config=pipeline_config,
    conversation_bus=conversation_bus,
)

convex_service = get_convex_service()
video_pipeline = get_video_pipeline(convex_service=convex_service)

init_streaming_routes(conversation_bus, convex_service)
init_transcription_routes(audio_pipeline, conversation_bus, convex_service)
init_webrtc_routes(
    audio_pipeline=audio_pipeline,
    conversation_bus=conversation_bus,
    video_pipeline=video_pipeline,
    convex_service=convex_service,
    latest_speaker_info_getter=get_latest_speaker_info,
)

app.include_router(streaming_router)
app.include_router(transcription_router)
app.include_router(webrtc_router)


@app.on_event("startup")
async def on_startup() -> None:
    """Warm up Whisper model asynchronously."""
    async def _warmup():
        try:
            await audio_pipeline.warm_whisper()
        except Exception as exc:
            logger.warning("Whisper warm-up failed: %s", exc)
    asyncio.create_task(_warmup())


@app.get("/")
async def index():
    """Health check endpoint."""
    return {"status": "ok", "service": "ForgetMeNot Backend"}


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Close all peer connections on shutdown."""
    await close_all_connections()
