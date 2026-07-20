"""
AI-Powered Outbound Reply Classifier for aegisScout (N6).
Categorizes incoming prospect replies to suggest automated next actions.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from aegisScout.ai.provider_router import ProviderRouter
from aegisScout.utils.json_helper import extract_json
from aegisScout.utils.logger import get_logger

logger = get_logger("ai.reply_classifier")

_router: Optional[ProviderRouter] = None

def _get_router() -> ProviderRouter:
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router

@dataclass
class ReplyClassification:
    category: str       # INTERESTED | NOT_INTERESTED | QUESTION | AUTO_REPLY | OUT_OF_OFFICE
    confidence: float   # 0.0 - 1.0
    next_action: str

async def classify_reply(reply_text: str) -> ReplyClassification:
    """Classify incoming business reply using LLM router."""
    if not reply_text or not reply_text.strip():
        return ReplyClassification(category="AUTO_REPLY", confidence=1.0, next_action="Ignore empty reply")

    prompt = f"""Classify the following business response into exactly ONE of these categories:
- INTERESTED: Prospect expresses interest in sales/meeting/collaboration.
- NOT_INTERESTED: Prospect declines offer or asks to stop contact.
- QUESTION: Prospect asks for more info or pricing.
- AUTO_REPLY: Automated system message or delivery notice.
- OUT_OF_OFFICE: Vacation or temporary absence response.

Prospect Reply:
"{reply_text}"

Return strictly valid JSON in this format:
{{
  "category": "INTERESTED",
  "confidence": 0.95,
  "next_action": "Schedule follow-up meeting or send calendar link"
}}"""

    try:
        router = _get_router()
        raw_resp = await router.generate(prompt=prompt, system_prompt="You are an expert sales inbox reply analyzer.")
        data = extract_json(raw_resp)
        if isinstance(data, dict) and "category" in data:
            return ReplyClassification(
                category=str(data.get("category", "QUESTION")).upper(),
                confidence=float(data.get("confidence", 0.8)),
                next_action=str(data.get("next_action", "Follow up manually"))
            )
    except Exception as e:
        logger.error(f"Failed to classify reply with LLM: {e}")

    # Fallback heuristic rules
    text_lower = reply_text.lower()
    if any(word in text_lower for word in ["istemiyorum", "çıkarın", "silin", "no thanks", "unsubscribe"]):
        return ReplyClassification(category="NOT_INTERESTED", confidence=0.85, next_action="Add to DNC list")
    elif any(word in text_lower for word in ["fiyat", "ücret", "detay", "nasıl", "bilgi", "how much"]):
        return ReplyClassification(category="QUESTION", confidence=0.85, next_action="Send pricing deck and details")
    elif any(word in text_lower for word in ["evet", "olur", "görüşelim", "uygun", "yes", "sure"]):
        return ReplyClassification(category="INTERESTED", confidence=0.85, next_action="Send booking calendar link")
    
    return ReplyClassification(category="QUESTION", confidence=0.5, next_action="Review manually")
