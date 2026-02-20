"""Route modules for the FastAPI application."""

from .streaming import router as streaming_router
from .transcription import router as transcription_router
from .webrtc import router as webrtc_router

__all__ = ["streaming_router", "transcription_router", "webrtc_router"]
