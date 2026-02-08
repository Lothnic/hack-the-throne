
import asyncio
import os
import logging
from dotenv import load_dotenv

# Load env from backend/.env if existing, or system
load_dotenv("backend/.env")

# Mock classes
class ConversationUtterance:
    def __init__(self, speaker, text):
        self.speaker = speaker
        self.text = text

async def test_llm():
    try:
        from backend.app.services.llm_service import get_llm_service
    except ImportError:
        import sys
        sys.path.append(os.getcwd())
        from backend.app.services.llm_service import get_llm_service

    llm = get_llm_service()
    if not llm.client:
        print("LLM Client NOT initialized (check API key)")
        return

    test_conversations = [
        [ConversationUtterance("User", "Hi, I am Mayank, your son.")],
        [ConversationUtterance("User", "Hello, I am Sarah.")],
        [ConversationUtterance("User", "Just visiting today.")],
    ]

    for i, conv in enumerate(test_conversations):
        print(f"\nTest {i+1}: {conv[0].text}")
        result = await llm.extract_relationship_info(conv)
        print(f"Result: {result}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_llm())
