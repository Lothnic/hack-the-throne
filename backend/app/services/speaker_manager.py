"""Speaker management service for handling speaker lookup and creation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..services.convex_client import ConvexService

logger = logging.getLogger("webrtc.speaker")


class SpeakerManager:
    """Manages speaker lookup, creation, and association logic."""

    def __init__(self, convex_service: ConvexService) -> None:
        self._convex = convex_service

    async def find_or_create_by_name(
        self,
        name: str,
        relationship: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Find existing speaker by name or create new one.

        Args:
            name: Speaker name to search/create
            relationship: Optional relationship to set

        Returns:
            Speaker dict with _id, name, etc. or None on failure
        """
        if not name or name in ["Unknown", "New Person"]:
            return None

        try:
            existing = await self._convex.get_speaker_by_name(name)
            if existing:
                logger.info("Found existing speaker: %s", existing.get("_id"))
                return existing

            result = await self._convex.find_or_create_speaker(
                embedding=[0.0] * 512,
                name=name,
            )
            if result:
                speaker_id = result.get("speakerId")
                logger.info("Created new speaker: %s (%s)", name, speaker_id)
                return {"_id": speaker_id, "name": name}
        except Exception as exc:
            logger.warning("Speaker lookup/create failed: %s", exc)

        return None

    async def get_or_create_default_speaker(self) -> Optional[dict[str, Any]]:
        """Get most recent speaker or create anonymous one.

        Returns:
            Speaker dict or None on failure
        """
        try:
            recent = await self._convex.list_speakers()
            if recent and len(recent) > 0:
                return recent[0]

            result = await self._convex.find_or_create_speaker(
                embedding=[0.0] * 512,
                name="Unknown Person",
            )
            if result:
                return {"_id": result.get("speakerId"), "name": "Unknown Person"}
        except Exception as exc:
            logger.warning("Default speaker creation failed: %s", exc)

        return None

    async def save_conversation(
        self,
        speaker_id: str,
        transcript: str,
        summary: str,
        duration_seconds: float = 10.0,
    ) -> bool:
        """Save conversation to Convex for a speaker.

        Returns:
            True on success, False on failure
        """
        if not speaker_id:
            return False

        try:
            await self._convex.save_conversation(
                speaker_id=speaker_id,
                transcript=transcript,
                duration_seconds=duration_seconds,
                summary=summary,
            )
            return True
        except Exception as exc:
            logger.warning("Failed to save conversation: %s", exc)
            return False

    async def update_relationship(
        self,
        speaker_id: str,
        relationship: str,
    ) -> bool:
        """Update speaker relationship if meaningful.

        Returns:
            True if updated, False otherwise
        """
        if not speaker_id or relationship in ["Someone you know", "Guest"]:
            return False

        try:
            await self._convex.update_speaker_profile(
                speaker_id=speaker_id,
                relationship=relationship,
            )
            logger.info("Updated speaker %s relationship to: %s", speaker_id, relationship)
            return True
        except Exception as exc:
            logger.warning("Failed to update relationship: %s", exc)
            return False


_speaker_manager: Optional[SpeakerManager] = None


def get_speaker_manager() -> SpeakerManager:
    """Get or create the global SpeakerManager instance."""
    global _speaker_manager
    if _speaker_manager is None:
        from ..services.convex_client import get_convex_service
        _speaker_manager = SpeakerManager(get_convex_service())
    return _speaker_manager
