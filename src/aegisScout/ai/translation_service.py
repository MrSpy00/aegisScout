"""
MyMemory Free Translation Service (Zero-Config / Keyless).
Provides instant keyless translation between English, Turkish, and other supported languages.
"""

from typing import Dict, Any, Optional
import urllib.parse
import httpx
from aegisScout.utils.logger import get_logger, log_execution_time

logger = get_logger("ai.translation_service")

_MYMEMORY_TRANSLATION_URL = "https://api.mymemory.translated.net/get"
_TIMEOUT = 10.0


class MyMemoryTranslator:
    """
    Zero-config translation service for business descriptions and outreach messages.
    """

    @staticmethod
    async def translate_text(text: str, source_lang: str = "en", target_lang: str = "tr") -> Dict[str, Any]:
        """
        Translate text via MyMemory Free Translation API.
        %100 Free, Zero API Key required.
        """
        if not text or not text.strip():
            return {"translated_text": "", "match": 0}

        clean_text = text.strip()
        langpair = f"{source_lang}|{target_lang}"
        logger.info(f"Translating text ({len(clean_text)} chars) from {source_lang} to {target_lang} via MyMemory...")

        params = {
            "q": clean_text,
            "langpair": langpair,
        }

        result = {
            "original_text": clean_text,
            "translated_text": clean_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "match_quality": 0,
        }

        with log_execution_time(logger, f"MyMemory Translate ({langpair})"):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(_MYMEMORY_TRANSLATION_URL, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        response_data = data.get("responseData", {})
                        result["translated_text"] = response_data.get("translatedText", clean_text)
                        result["match_quality"] = response_data.get("match", 0)
                        logger.info(f"MyMemory translation complete (Match quality: {result['match_quality']})")
                    else:
                        logger.warning(f"MyMemory API returned status {resp.status_code}")
            except Exception as e:
                logger.error(f"MyMemory translation failed: {e}")

        return result
