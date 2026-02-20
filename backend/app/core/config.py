"""Application configuration and constants."""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

FACE_REPUBLISH_INTERVAL_SECONDS = 4.0
SPEAKER_ASSOCIATION_WINDOW_SECONDS = 15.0

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

MIN_CONVERSATION_SECONDS = 2.0
VAD_AGGRESSIVENESS = 2
MIN_SPEECH_RMS = 0.05
SPEAKER_MATCH_THRESHOLD = 0.25
