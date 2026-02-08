
import os
import json
import logging
from typing import List, Optional, Dict, Any
from groq import AsyncGroq
from ..core import ConversationUtterance

logger = logging.getLogger("webrtc.llm")

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            self.client = AsyncGroq(api_key=self.api_key)
        else:
            logger.warning("GROQ_API_KEY not found. LLM service disabled.")

    async def extract_relationship_info(self, conversation: List[ConversationUtterance]) -> Optional[Dict[str, Any]]:
        """
        Analyze conversation to extract name and relationship updates.
        Returns a dict with 'name' and 'relationship' if found, else None.
        """
        if not self.client or not conversation:
            return None

        # Format conversation
        transcript = "\n".join([f"{u.speaker}: {u.text}" for u in conversation])

        system_prompt = """You are an AI assistant for a memory care system.
Your goal is to extract the speaker's NAME and RELATIONSHIP to the user (the patient) from the conversation.

Return JSON format:
{
  "name": "extracted name or null",
  "relationship": "extracted relationship (e.g. 'Your son', 'Your doctor') or null"
}

Rules:
- Only extract if explicitly mentioned or strongly implied.
- If the speaker says "I am your son", relationship is "Your son".
- If the speaker says "My name is David", name is "David".
- If nothing relevant is found, return null values.
- Relationship must start with 'Your' if applicable.
"""

        user_prompt = f"""Analyze this conversation:
{transcript}

Extract name and relationship:"""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return None
                
            data = json.loads(content)
            
            # Filter nulls
            updates = {}
            if data.get("name"):
                updates["name"] = data["name"]
            if data.get("relationship"):
                updates["relationship"] = data["relationship"]
                
            return updates if updates else None

        except Exception as e:
            logger.error("Error calling Groq for relationship extraction: %s", e)
            return None

# Global instance
_llm_service = None

def get_llm_service():
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
