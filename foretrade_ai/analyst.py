"""
ประกอบ prompt + เรียก LLM + ครอบด้วย disclaimer

เป็นการ "วิเคราะห์/อธิบาย" เชิงข้อมูลเท่านั้น — ไม่ให้คำแนะนำซื้อขาย
และไม่เชื่อมต่อการยิงออเดอร์

รองรับ 2 ภาษา (lang="th" | "en") — ภาษาไทยใช้ศัพท์การเทรดที่ถูกต้อง
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .data import fetch_pair_snapshot, load_trade
from .providers import get_provider
from .providers.base import LLMProvider


def _default_lang() -> str:
    lang = (os.getenv("AI_LANG") or "th").strip().lower()
    return "en" if lang.startswith("en") else "th"


DISCLAIMER = {
    "th": (
        "\n\n———\n"
        "⚠️ บทวิเคราะห์นี้สร้างโดย AI จากข้อมูลในอดีต/ปัจจุบัน เป็นการอธิบายเชิงข้อมูลเท่านั้น "
        "ไม่ใช่คำแนะนำการลงทุน ไม่การันตีความถูกต้องหรือผลลัพธ์ และไม่ควรใช้เป็นเหตุผลเดียว "
        "ในการตัดสินใจด้วยเงินจริง โปรดใช้วิจารณญาณและบริหารความเสี่ยงเอง"
    ),
    "en": (
        "\n\n———\n"
        "Disclaimer: This analysis is AI-generated from historical/current data and is "
        "descriptive information only. It is not investment advice, guarantees nothing, and "
        "should not be your sole basis for real-money decisions. Use your own judgment and "
        "manage risk accordingly."
    ),
}

_SYSTEM = {
    "th": (
        "คุณเป็นนักวิเคราะห์ข้อมูลตลาดคริปโตของเครื่องมือเทรด "
        "หน้าที่คือ 'อธิบายและวิเคราะห์เชิงข้อมูล' จากตัวเลขที่ให้ "
        "ให้สังเกต: แนวโน้ม/โมเมนตัม, ความผันผวน, สภาพคล่อง, และจุดน่าระวัง "
        "ห้าม: บอกให้ซื้อ/ขาย, ตั้งเป้าราคาเพื่อให้ทำตาม, หรือรับปากผลกำไร "
        "ให้พูดเชิงข้อสังเกต/สมมติฐาน ('ข้อมูลชี้ว่า...', 'อาจสะท้อนว่า...') "
        "ใช้ศัพท์การเทรดภาษาไทยที่ถูกต้อง (เช่น แนวโน้มขาขึ้น/ขาลง, โมเมนตัม, ทะลุแนวต้าน/แนวรับ, "
        "สภาพคล่อง, สเปรด, ความผันผวน, จุดตัดขาดทุน) "
        "ตอบเป็นภาษาไทย กระชับ เป็นหัวข้อ อ่านง่าย"
    ),
    "en": (
        "You are a crypto market-data analyst for a trading tool. "
        "Your job is to 'describe and analyze the data' from the numbers provided. "
        "Observe: trend/momentum, volatility, liquidity, and points of caution. "
        "Do NOT: tell the user to buy/sell, set price targets to act on, or promise profit. "
        "Speak in observations/hypotheses ('the data suggests...', 'this may reflect...'). "
        "Use correct trading terminology. Answer in English, concise, in bullet points."
    ),
}

_PAIR_TASK = {
    "th": (
        "ช่วยสรุปเป็นหัวข้อ:\n"
        "1) แนวโน้ม/โมเมนตัมตอนนี้ (เทียบ EMA200, Donchian, การเปลี่ยนแปลงราคา)\n"
        "2) ความผันผวน (ATR%) — เหมาะกับการเทรดสั้นแค่ไหน\n"
        "3) สภาพคล่อง (volume, สเปรด) — เข้า-ออกได้ไวไหม เสี่ยง slippage ไหม\n"
        "4) จุดน่าระวัง/สัญญาณกำกวมที่ควรระวัง\n"
    ),
    "en": (
        "Summarize in bullet points:\n"
        "1) Current trend/momentum (vs EMA200, Donchian, price change)\n"
        "2) Volatility (ATR%) — how suitable for short-term trading\n"
        "3) Liquidity (volume, spread) — fast to enter/exit? slippage risk?\n"
        "4) Points of caution / ambiguous signals to watch\n"
    ),
}

_TRADE_TASK = {
    "th": (
        "ช่วยสรุปเป็นหัวข้อ:\n"
        "1) ไม้นี้กำไรหรือขาดทุน และมากน้อยแค่ไหน (ดู close_profit / close_profit_abs)\n"
        "2) เหตุผลการออก (exit_reason) บอกอะไร — โดน stoploss / ROI / สัญญาณ / trailing\n"
        "3) ข้อสังเกตจาก max_rate/min_rate เทียบ open/close (จับจังหวะได้ดี/พลาดตรงไหน)\n"
        "4) บทเรียนเชิงข้อมูลจากไม้นี้ (เชิงสังเกต ไม่ใช่คำแนะนำ)\n"
    ),
    "en": (
        "Summarize in bullet points:\n"
        "1) Was this trade a win or loss, and by how much (close_profit / close_profit_abs)\n"
        "2) What the exit_reason indicates — stoploss / ROI / signal / trailing\n"
        "3) Observations from max_rate/min_rate vs open/close (good timing / missed where)\n"
        "4) Data-based lessons from this trade (observational, not advice)\n"
    ),
}


def analyze_pair(
    symbol: str,
    provider: LLMProvider | None = None,
    timeframe: str = "5m",
    lang: str | None = None,
) -> str:
    """วิเคราะห์คู่เทรดหนึ่งตัวจาก snapshot ล่าสุด."""
    provider = provider or get_provider()
    lang = lang or _default_lang()
    snapshot = fetch_pair_snapshot(symbol, timeframe=timeframe)

    header = (
        f"วิเคราะห์คู่เทรด {symbol} (timeframe {timeframe}) จากข้อมูลสรุปด้านล่าง"
        if lang == "th"
        else f"Analyze pair {symbol} (timeframe {timeframe}) from the summary below"
    )
    prompt = (
        f"{header}\n\n"
        f"```json\n{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n```\n\n"
        f"{_PAIR_TASK[lang]}"
    )
    return provider.generate(_SYSTEM[lang], prompt).strip() + DISCLAIMER[lang]


def analyze_trade(
    trade_id: int,
    provider: LLMProvider | None = None,
    db_path: str | Path | None = None,
    lang: str | None = None,
) -> str:
    """วิเคราะห์กำไร/ขาดทุนของทรานแซกชันหนึ่งไม้."""
    provider = provider or get_provider()
    lang = lang or _default_lang()
    trade = load_trade(trade_id, db_path=db_path)

    header = (
        "วิเคราะห์ผลของทรานแซกชันนี้จากข้อมูลของ Freqtrade"
        if lang == "th"
        else "Analyze the result of this trade from the Freqtrade data"
    )
    prompt = (
        f"{header}\n\n"
        f"```json\n{json.dumps(trade, ensure_ascii=False, indent=2, default=str)}\n```\n\n"
        f"{_TRADE_TASK[lang]}"
    )
    return provider.generate(_SYSTEM[lang], prompt).strip() + DISCLAIMER[lang]
