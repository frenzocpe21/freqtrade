"""Provider: Claude (Anthropic)."""

import os

from .base import LLMProvider

# ค่าเริ่มต้นเป็นรุ่นล่าสุด เปลี่ยนได้ผ่าน env ANTHROPIC_MODEL
DEFAULT_MODEL = "claude-opus-5"


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self) -> None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("ยังไม่ได้ตั้ง ANTHROPIC_API_KEY")
        try:
            import anthropic  # noqa: F401
        except ImportError as e:
            raise RuntimeError("ต้องติดตั้งก่อน:  pip install anthropic") from e

        self._model = os.getenv("ANTHROPIC_MODEL") or DEFAULT_MODEL
        self._anthropic = __import__("anthropic")
        self._client = self._anthropic.Anthropic()

    def generate(self, system: str, prompt: str) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=3000,
            system=system,
            # adaptive thinking + effort ต่ำ: วิเคราะห์กระชับ ประหยัด token
            thinking={"type": "adaptive"},
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": prompt}],
        )
        # เก็บเฉพาะ text block (ข้าม thinking block ที่ text ว่าง)
        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return "\n".join(parts).strip()
