"""
foretrade_web — หน้าแดชบอร์ดของเราเอง (ภาษาไทย) ที่คุยกับ Freqtrade REST API

- ดึงสถานะบอท / ออเดอร์ / PnL จาก Freqtrade มาแสดงเป็นภาษาไทย
- มีปุ่ม "วิเคราะห์ด้วย AI" เรียก foretrade_ai วิเคราะห์คู่เทรด/ทรานแซกชัน

รัน:  python -m foretrade_web.server
"""

__all__ = ["server"]
