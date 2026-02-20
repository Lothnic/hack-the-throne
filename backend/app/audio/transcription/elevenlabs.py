"""ElevenLabs Scribe transcription backend."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import wave
from typing import TYPE_CHECKING, List

import numpy as np

from .base import TranscriptSegment, Transcriber

if TYPE_CHECKING:
    from elevenlabs.client import ElevenLabs

logger = logging.getLogger("webrtc.audio.transcription.elevenlabs")

_elevenlabs_available = False
try:
    from elevenlabs.client import ElevenLabs as ElevenLabsClient
    _elevenlabs_available = True
except ImportError:
    ElevenLabsClient = None


class ElevenLabsTranscriber(Transcriber):
    """Transcribe audio using ElevenLabs Scribe v2."""

    def __init__(self, model: str = "scribe_v2"):
        self._model = model
        self._api_key = os.environ.get("ELEVENLABS_API_KEY")

    @property
    def is_available(self) -> bool:
        return _elevenlabs_available and self._api_key is not None

    async def transcribe(self, audio: np.ndarray, sample_rate: int) -> List[TranscriptSegment]:
        if not self.is_available:
            return []

        try:
            audio_rms = np.sqrt(np.mean(audio ** 2))
            if audio_rms > 0.001:
                target_rms = 0.1
                gain = min(target_rms / audio_rms, 10.0)
                audio = np.clip(audio * gain, -1.0, 1.0)

            audio_int16 = (audio * 32767).astype(np.int16)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                with wave.open(f, 'wb') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(sample_rate)
                    wav.writeframes(audio_int16.tobytes())

            def _call_scribe():
                client = ElevenLabsClient(api_key=self._api_key)
                with open(temp_path, "rb") as audio_file:
                    return client.speech_to_text.convert(
                        file=audio_file,
                        model_id=self._model
                    )

            result = await asyncio.to_thread(_call_scribe)
            os.unlink(temp_path)

            if result and hasattr(result, "text"):
                logger.info("ElevenLabs transcription: %s", result.text)
                return [TranscriptSegment(
                    start=0.0,
                    end=len(audio) / sample_rate,
                    text=result.text.strip()
                )]
            return []

        except Exception as exc:
            logger.warning("ElevenLabs transcription failed: %s", exc)
            return []
