"""Transcription backend implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: Optional[str] = None


class Transcriber(ABC):
    """Abstract base class for transcription backends."""

    @abstractmethod
    async def transcribe(self, audio: np.ndarray, sample_rate: int) -> List[TranscriptSegment]:
        """Transcribe audio to text segments.

        Args:
            audio: Float32 audio array normalized to [-1, 1]
            sample_rate: Audio sample rate

        Returns:
            List of transcript segments with timing
        """
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this transcriber is available."""
        pass


INDIAN_ENGLISH_PROMPT = """My name is Mayank. I'm Mayank. Hi, I'm Mayank Joshi. 
Mayank speaking here. This is Mayank. Hello, my name is Mayank.
Other names: Priya, Rahul, Aarav, Ananya, Vikram, Neha, Arjun."""
