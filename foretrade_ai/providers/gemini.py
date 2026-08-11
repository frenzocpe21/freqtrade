"""Provider: Gemini (Google)."""

import os

from .base import LLMProvider

# เปลี่ยนรุ่นได้ผ่าน env GEMINI_MODEL
DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("ยังไม่ได้ตั้ง GEMINI_API_KEY (หรือ GOOGLE_API_KEY)")
        try:
            from google import genai
        except ImportError as e:
            raise RuntimeError("ต้องติดตั้งก่อน:  pip install google-genai") from e

        self._genai = genai
        self._model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        self._client = genai.Client(api_key=api_key)

    def generate(self, system: str, prompt: str) -> str:
        resp = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=self._genai.types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=3000,
            ),
        )
        return (resp.text or "").strip()
