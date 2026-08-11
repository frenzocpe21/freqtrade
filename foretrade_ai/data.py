"""
ดึงข้อมูลสำหรับป้อนให้ AI วิเคราะห์:
    - snapshot ของคู่เทรด (ราคาล่าสุด + indicator + สภาพคล่อง) ผ่าน ccxt (public, ไม่ต้องใช้คีย์)
    - รายละเอียดทรานแซกชันจากฐานข้อมูล Freqtrade (tradesv3.sqlite)
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------- indicators


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, 1e-12)
    return 100 - (100 / (1 + rs))


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


# ---------------------------------------------------------------- pair snapshot


def fetch_pair_snapshot(
    symbol: str,
    timeframe: str = "5m",
    limit: int = 210,
    breakout_window: int = 25,
) -> dict[str, Any]:
    """
    ดึง OHLCV ล่าสุด + คำนวณ indicator สรุปเป็น dict สำหรับป้อนให้ LLM

    ใช้ ccxt (public endpoint) — ไม่ต้องมี API key
    """
    try:
        import ccxt
    except ImportError as e:  # ccxt เป็น dependency ของ Freqtrade อยู่แล้ว
        raise RuntimeError("ต้องติดตั้ง ccxt ก่อน (มากับ Freqtrade)") from e

    is_futures = ":" in symbol
    exchange = ccxt.binance(
        {"enableRateLimit": True, "options": {"defaultType": "future" if is_futures else "spot"}}
    )

    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    if not ohlcv:
        raise RuntimeError(f"ดึงข้อมูล OHLCV ของ {symbol} ไม่ได้")

    df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["rsi"] = _rsi(df["close"])
    df["atr"] = _atr(df)
    df["don_up"] = df["high"].rolling(breakout_window).max().shift(1)
    df["don_lo"] = df["low"].rolling(breakout_window).min().shift(1)
    df["vol_ma"] = df["volume"].rolling(breakout_window).mean()

    last = df.iloc[-1]
    ticker = exchange.fetch_ticker(symbol)

    # spread โดยประมาณจาก bid/ask
    bid, ask = ticker.get("bid"), ticker.get("ask")
    spread_pct = None
    if bid and ask and ask > 0:
        spread_pct = round((ask - bid) / ask * 100, 4)

    price = float(last["close"])
    atr_pct = round(float(last["atr"]) / price * 100, 3) if price else None

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "as_of": pd.to_datetime(last["ts"], unit="ms", utc=True).isoformat(),
        "price": round(price, 8),
        "change_pct": {
            "last_5_candles": round((price / float(df["close"].iloc[-6]) - 1) * 100, 3)
            if len(df) > 6 else None,
            "last_20_candles": round((price / float(df["close"].iloc[-21]) - 1) * 100, 3)
            if len(df) > 21 else None,
        },
        "rsi14": round(float(last["rsi"]), 2) if pd.notna(last["rsi"]) else None,
        "ema200": round(float(last["ema200"]), 8),
        "above_ema200": bool(price > float(last["ema200"])),
        "atr_pct": atr_pct,
        "donchian": {
            "upper": round(float(last["don_up"]), 8) if pd.notna(last["don_up"]) else None,
            "lower": round(float(last["don_lo"]), 8) if pd.notna(last["don_lo"]) else None,
        },
        "volume_last": round(float(last["volume"]), 4),
        "volume_ma": round(float(last["vol_ma"]), 4) if pd.notna(last["vol_ma"]) else None,
        "volume_vs_ma": round(float(last["volume"]) / float(last["vol_ma"]), 2)
        if pd.notna(last["vol_ma"]) and last["vol_ma"] else None,
        "quote_volume_24h": ticker.get("quoteVolume"),
        "spread_pct": spread_pct,
    }


# ---------------------------------------------------------------- trade lookup


def _db_candidates() -> list[Path]:
    """ตำแหน่งที่ไฟล์ DB อาจอยู่ (เรียงตามลำดับความน่าจะเป็น)."""
    root = Path(__file__).resolve().parents[1]  # repo root (= /app ใน container)
    names = ["tradesv3.dryrun.sqlite", "tradesv3.sqlite", "tradesv3.live.sqlite"]
    dirs = [root / "user_data", root, Path("/freqtrade/user_data")]
    return [d / n for d in dirs for n in names]


def _default_db_path() -> Path:
    """คืน DB ที่มีอยู่จริงตัวแรก (env FORETRADE_DB ชนะทุกอย่าง).

    dry-run/live ของ Freqtrade เขียน DB ตาม --db-url ใน config
    (ของเราอยู่ที่ user_data/) ถ้าตั้ง db_url เองก็ระบุ --db หรือ FORETRADE_DB ได้
    """
    env = os.getenv("FORETRADE_DB")
    if env:
        return Path(env)
    candidates = _db_candidates()
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]  # ไม่เจอ — คืนตัวแรกไว้ให้ error message ชี้ทางถูก


def load_trade(trade_id: int, db_path: str | Path | None = None) -> dict[str, Any]:
    """อ่านทรานแซกชันตาม id จากฐานข้อมูล Freqtrade (tradesv3*.sqlite)."""
    path = Path(db_path) if db_path else _default_db_path()
    if not path.exists():
        searched = "\n  ".join(str(p) for p in _db_candidates())
        raise RuntimeError(
            f"ไม่พบฐานข้อมูล {path} — ระบุ --db / ตั้ง env FORETRADE_DB "
            f"หรือรัน dry-run/live ให้มีเทรดก่อน\nค้นหาที่:\n  {searched}"
        )

    # เปิดแบบ read-only (URI) เผื่อ DB อยู่บน mount ที่ ro — กัน error "readonly database"
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
    finally:
        con.close()

    if row is None:
        raise RuntimeError(f"ไม่พบเทรด id={trade_id} ใน {path.name}")

    d = dict(row)
    # เลือกเฉพาะฟิลด์ที่มีความหมายต่อการวิเคราะห์ (ไม่เอาทั้งหมดให้รก)
    keep = [
        "id", "pair", "is_short", "leverage", "is_open",
        "amount", "stake_amount", "open_rate", "close_rate",
        "open_date", "close_date", "trade_duration",
        "close_profit", "close_profit_abs",
        "enter_tag", "exit_reason", "stop_loss_pct", "initial_stop_loss_pct",
        "max_rate", "min_rate",
    ]
    return {k: d[k] for k in keep if k in d}
