#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ForeTrade — เครื่องมือหากลยุทธ์ (Strategy Catalog)

แสดงรายชื่อกลยุทธ์ยอดนิยมจากคลังทางการของ Freqtrade ให้เลือกกดเลข
แล้วดาวน์โหลดไฟล์ .py เข้า user_data/strategies/ อัตโนมัติ — พร้อมเอาไป
backtest / compare กับ MomentumBreakout ได้ทันที

รันผ่าน foretrade_docker.bat -> เมนู 12 (catalog)
หรือสั่งตรง:
    docker compose -f docker-compose.foretrade.yml run --rm \
        --entrypoint python foretrade /freqtrade/user_data/foretrade_catalog.py

ความปลอดภัย: กลยุทธ์คือโค้ด Python ที่รันจริง — ดาวน์โหลดเฉพาะจาก repo ทางการ
เท่านั้น และควรเปิดไฟล์อ่านก่อนนำไปรัน (รันใน Docker แยกจากเครื่องหลักอยู่แล้ว)
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "strategies_catalog.json"
DEST_DIR = HERE / "strategies"


def load_catalog() -> dict:
    with open(CATALOG, encoding="utf-8") as f:
        return json.load(f)


def print_menu(cat: dict) -> list[dict]:
    items = cat["strategies"]
    print()
    print("=" * 64)
    print("  ForeTrade — คลังกลยุทธ์ (เลือกมา backtest เทียบกันได้)")
    print(f"  ที่มา: {cat['source']}")
    print("=" * 64)
    for i, s in enumerate(items, 1):
        flag = "  [ต้องลง dep เพิ่ม]" if s.get("needs") else ""
        print(f"  {i:>2}) {s['class']:<18} {s['style']}{flag}")
        print(f"      {s['desc']}")
    print("-" * 64)
    print("  พิมพ์เลขที่ต้องการ (คั่นด้วยช่องว่าง เช่น  1 6 7),")
    print("  พิมพ์ 'all' เพื่อโหลดทั้งหมด, หรือ Enter เปล่าเพื่อยกเลิก")
    print("=" * 64)
    return items


def parse_selection(raw: str, n: int) -> list[int]:
    raw = raw.strip().lower()
    if not raw:
        return []
    if raw == "all":
        return list(range(n))
    idxs: list[int] = []
    for tok in raw.replace(",", " ").split():
        if tok.isdigit():
            k = int(tok) - 1
            if 0 <= k < n and k not in idxs:
                idxs.append(k)
        else:
            print(f"  (ข้าม '{tok}' — ไม่ใช่ตัวเลขในรายการ)")
    return idxs


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "ForeTrade-catalog"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    dest.write_bytes(data)


def main() -> int:
    if not CATALOG.exists():
        print(f"[ERROR] ไม่พบไฟล์แคตตาล็อก: {CATALOG}")
        return 1

    cat = load_catalog()
    base = cat["base_url"].rstrip("/") + "/"
    items = print_menu(cat)

    try:
        raw = input("เลือก: ")
    except EOFError:
        print("\n(ไม่มี input — ต้องรันแบบ interactive: docker compose run ... ไม่ใช่ -T)")
        return 1

    picks = parse_selection(raw, len(items))
    if not picks:
        print("ยกเลิก ไม่ได้โหลดอะไร")
        return 0

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    ok, fail, need_dep = [], [], set()

    for k in picks:
        s = items[k]
        url = base + s["file"]
        dest = DEST_DIR / s["file"]
        print(f"-> โหลด {s['class']} ...", end=" ", flush=True)
        try:
            download(url, dest)
            print(f"OK ({dest.name})")
            ok.append(s["class"])
            for d in s.get("needs", []):
                need_dep.add(d)
        except Exception as e:  # noqa: BLE001
            print(f"ล้มเหลว: {e}")
            fail.append(s["class"])

    print()
    print("=" * 64)
    if ok:
        print("โหลดสำเร็จ:", ", ".join(ok))
    if fail:
        print("ล้มเหลว:", ", ".join(fail))
    if need_dep:
        print(f"\n[หมายเหตุ] บางตัวต้องลงไลบรารีเพิ่ม: {', '.join(sorted(need_dep))}")
        print("  ตัวอย่าง (รันครั้งเดียว):")
        print("    docker compose -f docker-compose.foretrade.yml run --rm \\")
        print(f"      --entrypoint pip foretrade install {' '.join(sorted(need_dep))}")
    print("\nขั้นต่อไป:")
    print("  - เมนู 8 (list)    ดูชื่อคลาสจริงของกลยุทธ์ที่เพิ่งโหลด")
    print("  - เมนู 10 (compare) พิมพ์ชื่อคลาสหลายตัวคั่นช่องว่าง เพื่อ backtest เทียบกัน")
    print(f"     เช่น:  MomentumBreakout {' '.join(ok) if ok else 'Strategy001'}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
