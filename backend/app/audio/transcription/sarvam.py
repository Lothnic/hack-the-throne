"""Sarvam AI transcription backend (optimized for Indian English)."""

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
    from sarvamai import SarvamAI

logger = logging.getLogger("webrtc.audio.transcription.sarvam")

_sarvam_available = False
try:
    from sarvamai import SarvamAI as SarvamAIClient
    _sarvam_available = True
except ImportError:
    SarvamAIClient = None


class SarvamTranscriber(Transcriber):
    """Transcribe audio using Sarvam AI (optimized for Indian English)."""

    MAX_CHUNK_SEC = 25.0
    OVERLAP_SEC = 1.0

    def __init__(self, model: str = "saarika:v2.5"):
        self._model = model
        self._api_key = os.environ.get("SARVAM_API_KEY")

    @property
    def is_available(self) -> bool:
        return _sarvam_available and self._api_key is not None

    async def transcribe(self, audio: np.ndarray, sample_rate: int) -> List[TranscriptSegment]:
        if not self.is_available:
            return []

        try:
            duration_sec = len(audio) / sample_rate

            if duration_sec <= self.MAX_CHUNK_SEC:
                chunks = [(audio, 0.0)]
            else:
                chunks = self._split_into_chunks(audio, sample_rate)
                logger.info("Splitting %.2fs audio into %d chunks for Sarvam", duration_sec, len(chunks))

            all_segments: List[TranscriptSegment] = []

            for chunk_audio, chunk_offset in chunks:
                audio_int16 = (chunk_audio * 32767).astype(np.int16)

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_path = f.name
                    with wave.open(f, 'wb') as wav:
                        wav.setnchannels(1)
                        wav.setsampwidth(2)
                        wav.setframerate(sample_rate)
                        wav.writeframes(audio_int16.tobytes())

                def _call_sarvam():
                    client = SarvamAIClient(api_subscription_key=self._api_key)
                    with open(temp_path, "rb") as audio_file:
                        response = client.speech_to_text.transcribe(
                            file=audio_file,
                            language_code="en-IN",
                            model=self._model
                        )
                    return response

                result = await asyncio.to_thread(_call_sarvam)
                os.unlink(temp_path)

                if result and hasattr(result, 'transcript') and result.transcript:
                    chunk_duration = len(chunk_audio) / sample_rate
                    all_segments.append(TranscriptSegment(
                        start=chunk_offset,
                        end=chunk_offset + chunk_duration,
                        text=result.transcript.strip(),
                    ))

            if all_segments:
                full_text = " ".join(seg.text for seg in all_segments)
                logger.info("Sarvam transcription: %s", full_text[:100] + "..." if len(full_text) > 100 else full_text)

            return all_segments

        except Exception as exc:
            logger.warning("Sarvam transcription failed: %s", exc)
            return []

    def _split_into_chunks(self, audio: np.ndarray, sample_rate: int) -> List[tuple]:
        """Split audio into overlapping chunks for Sarvam's 30s limit."""
        chunks = []
        chunk_samples = int(self.MAX_CHUNK_SEC * sample_rate)
        overlap_samples = int(self.OVERLAP_SEC * sample_rate)
        step_samples = chunk_samples - overlap_samples

        offset = 0
        while offset < len(audio):
            chunk_end = min(offset + chunk_samples, len(audio))
            chunk_audio = audio[offset:chunk_end]
            chunk_start_time = offset / sample_rate
            chunks.append((chunk_audio, chunk_start_time))
            offset += step_samples

        return chunks
