"""
CLI สำหรับ AI Analyst (on-demand)

ตัวอย่าง:
    python -m foretrade_ai.cli analyze-pair BTC/USDT:USDT
    python -m foretrade_ai.cli analyze-pair ETH/USDT --provider gemini --timeframe 15m
    python -m foretrade_ai.cli analyze-trade 42
    python -m foretrade_ai.cli analyze-pair BTC/USDT --lang en   # ผลลัพธ์ภาษาอังกฤษ

เลือก provider ได้จาก --provider หรือ env AI_PROVIDER (claude | openai | gemini)
เลือกภาษาได้จาก --lang th|en หรือ env AI_LANG (ค่าเริ่มต้น th)
คีย์ตั้งผ่าน env: ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY
"""

from __future__ import annotations

import argparse
import sys

from .analyst import analyze_pair, analyze_trade
from .providers import get_provider


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="foretrade-ai",
        description="AI วิเคราะห์คู่เทรด/ทรานแซกชัน แบบ on-demand (ไม่ยิงออเดอร์)",
    )
    parser.add_argument(
        "--provider", default=None, help="claude | openai | gemini (ค่าเริ่มต้น: env AI_PROVIDER หรือ claude)"
    )
    parser.add_argument(
        "--lang", default=None, choices=["th", "en"],
        help="ภาษาผลลัพธ์ th | en (ค่าเริ่มต้น: env AI_LANG หรือ th)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pair = sub.add_parser("analyze-pair", help="วิเคราะห์คู่เทรดหนึ่งตัว")
    p_pair.add_argument("symbol", help="เช่น BTC/USDT หรือ BTC/USDT:USDT (futures)")
    p_pair.add_argument("--timeframe", default="5m")

    p_trade = sub.add_parser("analyze-trade", help="วิเคราะห์ทรานแซกชันหนึ่งไม้")
    p_trade.add_argument("trade_id", type=int, help="id ของเทรดใน tradesv3*.sqlite")
    p_trade.add_argument("--db", default=None, help="พาธไฟล์ฐานข้อมูล (ค่าเริ่มต้น: dry-run DB)")

    args = parser.parse_args(argv)

    try:
        provider = get_provider(args.provider)
        if args.command == "analyze-pair":
            out = analyze_pair(
                args.symbol, provider=provider, timeframe=args.timeframe, lang=args.lang
            )
        elif args.command == "analyze-trade":
            out = analyze_trade(
                args.trade_id, provider=provider, db_path=args.db, lang=args.lang
            )
        else:  # pragma: no cover
            parser.error("ไม่รู้จักคำสั่ง")
            return 2
    except Exception as e:  # ให้ error อ่านง่ายบน CLI
        print(f"ผิดพลาด: {e}", file=sys.stderr)
        return 1

    print(f"[provider: {provider.name}]\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
