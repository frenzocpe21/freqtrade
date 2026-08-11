"""Provider: ChatGPT (OpenAI)."""

import os

from .base import LLMProvider

# เปลี่ยนรุ่นได้ผ่าน env OPENAI_MODEL
DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self) -> None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("ยังไม่ได้ตั้ง OPENAI_API_KEY")
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError("ต้องติดตั้งก่อน:  pip install openai") from e

        self._model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
        self._client = OpenAI()

    def generate(self, system: str, prompt: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            max_tokens=3000,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return (resp.choices[0].message.content or "").strip()
