"""Local faster-whisper transcription backend."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, List

import numpy as np

from .base import INDIAN_ENGLISH_PROMPT, TranscriptSegment, Transcriber

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

logger = logging.getLogger("webrtc.audio.transcription.local")

_faster_whisper_available = False
try:
    from faster_whisper import WhisperModel as WhisperModelClass
    _faster_whisper_available = True
except ImportError:
    WhisperModelClass = None


class LocalWhisperTranscriber(Transcriber):
    """Transcribe audio using local faster-whisper model."""

    def __init__(self, model: str = "large-v3", device: str = "cuda", compute_type: str = "int8_float16"):
        self._model_name = model
        self._device = device
        self._compute_type = compute_type
        self._model: WhisperModel | None = None
        self._lock = asyncio.Lock()

    @property
    def is_available(self) -> bool:
        return _faster_whisper_available

    async def _load_model(self) -> WhisperModel | None:
        async with self._lock:
            if self._model is not None:
                return self._model

            if not _faster_whisper_available:
                logger.warning("faster-whisper not installed; cannot load model")
                return None

            try:
                def _load():
                    return WhisperModelClass(
                        self._model_name,
                        device=self._device,
                        compute_type=self._compute_type,
                    )
                self._model = await asyncio.to_thread(_load)
                logger.info(
                    "Loaded faster-whisper model '%s' (%s, %s)",
                    self._model_name,
                    self._device,
                    self._compute_type,
                )
                return self._model
            except Exception as exc:
                logger.warning("Failed to load faster-whisper model '%s': %s", self._model_name, exc)
                return None

    async def transcribe(self, audio: np.ndarray, sample_rate: int) -> List[TranscriptSegment]:
        if not _faster_whisper_available:
            logger.warning("No transcription backend available")
            return []

        model = await self._load_model()
        if model is None:
            return []

        try:
            def _transcribe():
                segments, info = model.transcribe(
                    audio,
                    language="en",
                    task="transcribe",
                    beam_size=5,
                    best_of=5,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    condition_on_previous_text=False,
                    initial_prompt=INDIAN_ENGLISH_PROMPT,
                )
                return list(segments), info

            segments, info = await asyncio.to_thread(_transcribe)
        except Exception as exc:
            logger.warning("Local Whisper transcription failed: %s", exc)
            return []

        snippets: List[TranscriptSegment] = []
        for seg in segments:
            text = seg.text.strip() if seg.text else ""
            if text:
                snippets.append(TranscriptSegment(
                    start=seg.start,
                    end=seg.end,
                    text=text,
                ))

        return snippets
