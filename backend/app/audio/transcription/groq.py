"""Groq Whisper transcription backend."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import wave
from typing import TYPE_CHECKING, List

import numpy as np

from .base import INDIAN_ENGLISH_PROMPT, TranscriptSegment, Transcriber

if TYPE_CHECKING:
    from groq import Groq

logger = logging.getLogger("webrtc.audio.transcription.groq")

_groq_available = False
try:
    from groq import Groq as GroqClient
    _groq_available = True
except ImportError:
    GroqClient = None


class GroqTranscriber(Transcriber):
    """Transcribe audio using Groq's cloud Whisper API."""

    def __init__(self, model: str = "whisper-large-v3-turbo"):
        self._model = model
        self._api_key = os.environ.get("GROQ_API_KEY")

    @property
    def is_available(self) -> bool:
        return _groq_available and self._api_key is not None

    async def transcribe(self, audio: np.ndarray, sample_rate: int) -> List[TranscriptSegment]:
        if not self.is_available:
            return []

        try:
            audio_int16 = (audio * 32767).astype(np.int16)

            duration_sec = len(audio) / sample_rate
            logger.debug("Sending %.2fs audio to Groq", duration_sec)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                with wave.open(f, 'wb') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(sample_rate)
                    wav.writeframes(audio_int16.tobytes())

            def _call_groq():
                client = GroqClient(api_key=self._api_key)
                with open(temp_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        file=(temp_path, audio_file.read()),
                        model=self._model,
                        temperature=0.0,
                        prompt=INDIAN_ENGLISH_PROMPT,
                        language="en",
                        response_format="verbose_json",
                    )
                return transcription

            result = await asyncio.to_thread(_call_groq)
            os.unlink(temp_path)

            snippets: List[TranscriptSegment] = []
            if hasattr(result, "segments") and result.segments:
                for seg in result.segments:
                    text = seg.get("text", "").strip() if isinstance(seg, dict) else getattr(seg, "text", "").strip()
                    start = seg.get("start", 0.0) if isinstance(seg, dict) else getattr(seg, "start", 0.0)
                    end = seg.get("end", 0.0) if isinstance(seg, dict) else getattr(seg, "end", 0.0)
                    if text:
                        snippets.append(TranscriptSegment(start=start, end=end, text=text))
            elif hasattr(result, "text") and result.text:
                snippets.append(TranscriptSegment(
                    start=0.0,
                    end=len(audio) / sample_rate,
                    text=result.text.strip(),
                ))

            if snippets:
                logger.info("Groq transcription: %s", snippets[0].text[:50] + "..." if len(snippets[0].text) > 50 else snippets[0].text)
            return snippets

        except Exception as exc:
            logger.warning("Groq transcription failed: %s", exc)
            return []
