# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
"""
MomentumBreakout — กลยุทธ์เริ่มต้นของ ForeTrade

แนวคิด: "ถี่แต่ไม่แข่งความเร็วดิบ"
    - เข้าเมื่อราคาทะลุกรอบสูงสุด/ต่ำสุด N แท่ง (Donchian breakout)
      พร้อม volume ยืนยันว่าแรงจริง
    - ออกด้วย ROI / trailing stop / stoploss (บังคับทุกไม้) และเมื่อโมเมนตัมหมด
    - พารามิเตอร์เปิดให้ hyperopt จูนได้

รองรับทั้ง spot และ futures (long + short) — เปิด/ปิด short ผ่าน can_short ใน config
กลยุทธ์นี้ออกแบบให้ "ถอด-สลับได้": เพิ่มไฟล์กลยุทธ์อื่นในโฟลเดอร์เดียวกันได้เลย
โครง Execution/Risk/Config ของ Freqtrade ใช้ร่วมกันหมด
"""

from datetime import datetime
from pandas import DataFrame

from freqtrade.strategy import (
    IStrategy,
    DecimalParameter,
    IntParameter,
    BooleanParameter,
)

import talib.abstract as ta
from technical import qtpylib


class MomentumBreakout(IStrategy):
    INTERFACE_VERSION = 3

    # เปิด short ได้ (ใช้ได้เฉพาะ futures/margin; ถ้าเป็น spot Freqtrade จะข้าม short ให้เอง)
    can_short: bool = True

    timeframe = "15m"

    # รันคำนวณ indicator เฉพาะแท่งใหม่ (เร็วขึ้น)
    process_only_new_candles = True

    # ออกด้วยสัญญาณกลยุทธ์ + ROI/trailing/stoploss
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # --- Risk: บังคับ SL ทุกไม้ + trailing กันกำไรหลุด ---
    # ROI แบบ time-based (นาที) — ตั้งเป้าใหญ่ขึ้น/ยาวขึ้นสำหรับ 15m
    # เพื่อ "ปล่อยไม้ชนะวิ่ง" ไม่รีบเก็บกำไรเล็กจนโดน fee กิน
    minimal_roi = {
        "0": 0.05,    # เป้ากำไร 5% ทันที
        "60": 0.03,   # หลัง 1 ชม. รับ 3%
        "180": 0.015,  # หลัง 3 ชม. รับ 1.5%
        "360": 0.0,   # หลัง 6 ชม. ออกที่เท่าทุน
    }

    stoploss = -0.03  # ตัดขาดทุนที่ -3% (จะถูก override ได้จาก config)

    trailing_stop = True
    trailing_stop_positive = 0.012          # ลาก stop ตามห่าง ~1.2%
    trailing_stop_positive_offset = 0.03    # เริ่มลากเมื่อกำไรแตะ 3% (ปล่อยวิ่งก่อน)
    trailing_only_offset_is_reached = True

    # ต้องมีแท่งย้อนหลังพอสำหรับ Donchian + EMA เทรนด์
    startup_candle_count: int = 210

    # Order types — ใช้ limit เข้า/ออกเพื่อคุมราคา (กันราคาไหล), stoploss เป็น market ให้ตัดทันเวลา
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    # --- Protections: กันขาดทุนหนัก (ต้องกำหนดในกลยุทธ์ — config key 'protections' ถูก deprecated) ---
    protections = [
        {
            "method": "StoplossGuard",
            "lookback_period_candles": 24,
            "trade_limit": 4,
            "stop_duration_candles": 12,
            "only_per_pair": False,
        },
        {
            "method": "MaxDrawdown",
            "lookback_period_candles": 288,
            "trade_limit": 10,
            "stop_duration_candles": 48,
            "max_allowed_drawdown": 0.1,
        },
        {"method": "CooldownPeriod", "stop_duration_candles": 2},
    ]

    # --- plot_config: วาดอินดิเคเตอร์ของเราทับบนกราฟ FreqUI ---
    plot_config = {
        "main_plot": {
            "donchian_upper": {"color": "#26a69a"},   # กรอบบน (เขียว)
            "donchian_lower": {"color": "#ef5350"},   # กรอบล่าง (แดง)
            "donchian_mid": {"color": "#888888"},     # เส้นกลาง (เทา)
            "trend_ema": {"color": "#2962ff"},        # EMA เทรนด์ (น้ำเงิน)
        },
        "subplots": {
            "RSI": {"rsi": {"color": "#ab47bc"}},
            "ATR": {"atr": {"color": "#ffa726"}},
            "Volume MA": {"volume_ma": {"color": "#78909c"}},
        },
    }

    # ---------------- Hyperopt parameters ----------------
    # ความยาวกรอบ breakout (Donchian)
    breakout_window = IntParameter(15, 60, default=40, space="buy", optimize=True, load=True)
    # ตัวคูณ volume: ต้องมากกว่าค่าเฉลี่ยกี่เท่าถึงถือว่า "แรงจริง"
    volume_factor = DecimalParameter(1.0, 3.0, default=2.0, decimals=1, space="buy", optimize=True, load=True)
    # ความยาว EMA เทรนด์ (เข้า long เฉพาะเหนือ EMA, short เฉพาะใต้ EMA)
    trend_ema = IntParameter(50, 200, default=200, space="buy", optimize=True, load=True)
    # เปิด/ปิดตัวกรองเทรนด์
    use_trend_filter = BooleanParameter(default=True, space="buy", optimize=True, load=True)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Donchian channel — ใช้ค่ากรอบของ "แท่งก่อนหน้า" (shift 1) เพื่อกัน lookahead bias
        win = self.breakout_window.value
        dataframe["donchian_upper"] = dataframe["high"].rolling(win).max().shift(1)
        dataframe["donchian_lower"] = dataframe["low"].rolling(win).min().shift(1)
        dataframe["donchian_mid"] = (
            dataframe["donchian_upper"] + dataframe["donchian_lower"]
        ) / 2

        # Volume เฉลี่ยเพื่อยืนยันแรง
        dataframe["volume_ma"] = dataframe["volume"].rolling(win).mean()

        # EMA เทรนด์
        dataframe["trend_ema"] = ta.EMA(dataframe, timeperiod=int(self.trend_ema.value))

        # ATR ไว้ดูความผันผวน (ใช้ต่อยอด custom_stoploss ได้)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        # RSI ไว้เป็นข้อมูลประกอบ / ใช้ในเงื่อนไขออก
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        volume_ok = dataframe["volume"] > (dataframe["volume_ma"] * self.volume_factor.value)

        if self.use_trend_filter.value:
            long_trend = dataframe["close"] > dataframe["trend_ema"]
            short_trend = dataframe["close"] < dataframe["trend_ema"]
        else:
            long_trend = dataframe["volume"] > 0
            short_trend = dataframe["volume"] > 0

        # LONG: ราคาทะลุกรอบบน + volume ยืนยัน + อยู่ฝั่งขาขึ้นของเทรนด์
        long_mask = (
            qtpylib.crossed_above(dataframe["close"], dataframe["donchian_upper"])
            & volume_ok
            & long_trend
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[long_mask, "enter_long"] = 1
        dataframe.loc[long_mask, "enter_tag"] = "breakout_up"

        # SHORT: ราคาทะลุกรอบล่าง + volume ยืนยัน + อยู่ฝั่งขาลงของเทรนด์
        short_mask = (
            qtpylib.crossed_below(dataframe["close"], dataframe["donchian_lower"])
            & volume_ok
            & short_trend
            & (dataframe["volume"] > 0)
        )
        dataframe.loc[short_mask, "enter_short"] = 1
        dataframe.loc[short_mask, "enter_tag"] = "breakout_down"

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # ออกเมื่อ "เทรนด์พังจริง" เท่านั้น: ราคาข้ามเส้นเทรนด์ EMA กลับฝั่ง
        # (เดิมใช้เส้นกลางกรอบ Donchian ซึ่งไวเกิน → เข้า-ออกวนถี่ โดน fee กิน)
        # กำไรปกติปล่อยให้ ROI / trailing stop จัดการแทน

        # ออก long เมื่อราคาหลุดใต้เส้นเทรนด์
        exit_long_mask = qtpylib.crossed_below(
            dataframe["close"], dataframe["trend_ema"]
        ) & (dataframe["volume"] > 0)
        dataframe.loc[exit_long_mask, "exit_long"] = 1
        dataframe.loc[exit_long_mask, "exit_tag"] = "trend_break"

        # ออก short เมื่อราคากลับขึ้นเหนือเส้นเทรนด์
        exit_short_mask = qtpylib.crossed_above(
            dataframe["close"], dataframe["trend_ema"]
        ) & (dataframe["volume"] > 0)
        dataframe.loc[exit_short_mask, "exit_short"] = 1
        dataframe.loc[exit_short_mask, "exit_tag"] = "trend_break"

        return dataframe
