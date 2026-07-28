"""
aegisScout.ai package initialization.
Exports ask_llm and LLMProviderRouter.
"""
from aegisScout.ai.provider_router import ask_llm, ProviderRouter

LLMProviderRouter = ProviderRouter

__all__ = ["ask_llm", "ProviderRouter", "LLMProviderRouter"]
