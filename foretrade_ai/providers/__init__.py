"""ผู้ให้บริการ LLM แบบถอด-สลับได้ (claude / openai / gemini)."""

import os

from .base import LLMProvider


def get_provider(name: str | None = None) -> LLMProvider:
    """
    คืน provider ตามชื่อ (หรือจาก env AI_PROVIDER, ค่าเริ่มต้น 'claude').

    รองรับ: claude | openai | gemini
    """
    name = (name or os.getenv("AI_PROVIDER") or "claude").strip().lower()

    if name in ("claude", "anthropic"):
        from .claude import ClaudeProvider
        return ClaudeProvider()
    if name in ("openai", "chatgpt", "gpt"):
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()
    if name in ("gemini", "google"):
        from .gemini import GeminiProvider
        return GeminiProvider()

    raise ValueError(
        f"ไม่รู้จัก provider '{name}' — เลือก claude / openai / gemini "
        f"(ตั้งผ่าน --provider หรือ env AI_PROVIDER)"
    )
