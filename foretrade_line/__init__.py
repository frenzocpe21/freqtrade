"""
foretrade_line — สะพานแจ้งเตือนจาก Freqtrade ไปยัง LINE (ฟรีด้วย LINE Messaging API)

Freqtrade (webhook) --POST--> relay ตัวนี้ --push--> LINE Official Account

หมายเหตุ: LINE Notify ปิดบริการแล้ว (มี.ค. 2025) จึงใช้ LINE Messaging API แทน
free tier จำกัด push ~500 ข้อความ/เดือน → ควรตั้ง webhook ให้แจ้งเฉพาะเหตุการณ์สำคัญ
"""

__all__ = ["relay"]
