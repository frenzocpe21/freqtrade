"""
ประกอบ prompt + เรียก LLM + ครอบด้วย disclaimer

เป็นการ "วิเคราะห์/อธิบาย" เชิงข้อมูลเท่านั้น — ไม่ให้คำแนะนำซื้อขาย
และไม่เชื่อมต่อการยิงออเดอร์
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data import fetch_pair_snapshot, load_trade
from .providers import get_provider
from .providers.base import LLMProvider

DISCLAIMER = (
    "\n\n———\n"
    "⚠️ บทวิเคราะห์นี้สร้างโดย AI จากข้อมูลในอดีต/ปัจจุบัน เป็นการอธิบายเชิงข้อมูลเท่านั้น "
    "ไม่ใช่คำแนะนำการลงทุน ไม่การันตีความถูกต้องหรือผลลัพธ์ และไม่ควรใช้เป็นเหตุผลเดียว "
    "ในการตัดสินใจด้วยเงินจริง โปรดใช้วิจารณญาณและบริหารความเสี่ยงเอง"
)

_SYSTEM = (
    "คุณเป็นนักวิเคราะห์ข้อมูลตลาดคริปโตของเครื่องมือเทรดตัวหนึ่ง "
    "หน้าที่คือ 'อธิบายและวิเคราะห์เชิงข้อมูล' จากตัวเลขที่ให้ "
    "ทำสิ่งต่อไปนี้: สังเกตแนวโน้ม/โมเมนตัม, ความผันผวน, สภาพคล่อง, และจุดน่าระวัง "
    "ห้าม: บอกให้ซื้อ/ขาย, ตั้งเป้าราคาเพื่อให้ทำตาม, หรือรับปากผลกำไร "
    "ให้พูดในเชิงข้อสังเกต/สมมติฐาน ('ข้อมูลชี้ว่า...', 'อาจสะท้อนว่า...') "
    "ตอบเป็นภาษาไทย กระชับ เป็นหัวข้อ อ่านง่าย"
)


def analyze_pair(
    symbol: str,
    provider: LLMProvider | None = None,
    timeframe: str = "5m",
) -> str:
    """วิเคราะห์คู่เทรดหนึ่งตัวจาก snapshot ล่าสุด."""
    provider = provider or get_provider()
    snapshot = fetch_pair_snapshot(symbol, timeframe=timeframe)

    prompt = (
        f"วิเคราะห์คู่เทรด {symbol} (timeframe {timeframe}) จากข้อมูลสรุปด้านล่าง\n\n"
        f"```json\n{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n```\n\n"
        "ช่วยสรุปเป็นหัวข้อ:\n"
        "1) แนวโน้ม/โมเมนตัมตอนนี้ (เทียบ EMA200, Donchian, การเปลี่ยนแปลงราคา)\n"
        "2) ความผันผวน (ATR%) — เหมาะกับการเทรดสั้นแค่ไหน\n"
        "3) สภาพคล่อง (volume, spread) — เข้า-ออกได้ไวไหม เสี่ยง slippage ไหม\n"
        "4) จุดน่าระวัง/สัญญาณกำกวมที่ควรระวัง\n"
    )
    return provider.generate(_SYSTEM, prompt).strip() + DISCLAIMER


def analyze_trade(
    trade_id: int,
    provider: LLMProvider | None = None,
    db_path: str | Path | None = None,
) -> str:
    """วิเคราะห์กำไร/ขาดทุนของทรานแซกชันหนึ่งไม้."""
    provider = provider or get_provider()
    trade = load_trade(trade_id, db_path=db_path)

    prompt = (
        f"วิเคราะห์ผลของทรานแซกชันนี้จากข้อมูลของ Freqtrade\n\n"
        f"```json\n{json.dumps(trade, ensure_ascii=False, indent=2, default=str)}\n```\n\n"
        "ช่วยสรุปเป็นหัวข้อ:\n"
        "1) ไม้นี้กำไรหรือขาดทุน และมากน้อยแค่ไหน (ดู close_profit / close_profit_abs)\n"
        "2) เหตุผลการออก (exit_reason) บอกอะไร — โดน stoploss / ROI / สัญญาณ / trailing\n"
        "3) ข้อสังเกตจาก max_rate/min_rate เทียบ open/close (จับจังหวะได้ดี/พลาดตรงไหน)\n"
        "4) บทเรียนเชิงข้อมูลจากไม้นี้ (เชิงสังเกต ไม่ใช่คำแนะนำ)\n"
    )
    return provider.generate(_SYSTEM, prompt).strip() + DISCLAIMER
