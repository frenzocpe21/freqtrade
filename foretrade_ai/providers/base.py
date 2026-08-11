"""Interface กลางของ LLM provider."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    provider ทุกตัวรับ system prompt + user prompt แล้วคืนข้อความวิเคราะห์ (str)

    การใส่คีย์ทำผ่าน environment variable ของแต่ละเจ้า —
    โมดูลนี้จะไม่เก็บ/พิมพ์คีย์ออกมา
    """

    #: ชื่อผู้ให้บริการ (ไว้แสดงผล)
    name: str = "llm"

    @abstractmethod
    def generate(self, system: str, prompt: str) -> str:
        """ส่ง prompt ไปยังโมเดล แล้วคืนคำตอบเป็นข้อความ."""
        raise NotImplementedError
