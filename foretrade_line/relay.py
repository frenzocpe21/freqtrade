"""
Relay: รับ webhook จาก Freqtrade แล้ว push ไป LINE

รัน:
    python -m foretrade_line.relay
    (ต้องมี uvicorn/fastapi — มากับ Freqtrade อยู่แล้ว)

ตั้งค่าเป็น env:
    LINE_CHANNEL_ACCESS_TOKEN   (จำเป็น) — จาก LINE Developers > Messaging API channel
    LINE_TO                     (ไม่บังคับ) — userId/groupId ปลายทาง; ถ้าไม่ตั้งจะใช้ broadcast
    LINE_RELAY_HOST             (ค่าเริ่มต้น 127.0.0.1)
    LINE_RELAY_PORT             (ค่าเริ่มต้น 8090)

ฝั่ง Freqtrade: เปิดบล็อก "webhook" ใน config.dry.json ให้ enabled=true
และตั้ง url = http://127.0.0.1:8090/freqtrade
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"


def _push_to_line(text: str) -> tuple[bool, str]:
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        return False, "ยังไม่ได้ตั้ง LINE_CHANNEL_ACCESS_TOKEN"

    to = os.getenv("LINE_TO")
    # ตัดความยาวกัน LINE ปฏิเสธ (จำกัด ~5000 ตัวอักษร/ข้อความ)
    text = text[:4900]
    messages = [{"type": "text", "text": text}]

    if to:
        url = LINE_PUSH_URL
        payload = {"to": to, "messages": messages}
    else:
        url = LINE_BROADCAST_URL  # ส่งหาผู้ติดตามทุกคน (ไม่ต้องรู้ userId)
        payload = {"messages": messages}

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300, f"LINE status {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"LINE HTTPError {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}"
    except Exception as e:  # noqa: BLE001
        return False, f"LINE error: {e}"


def _extract_text(body: dict) -> str:
    """ดึงข้อความจาก payload ของ Freqtrade webhook (คีย์ 'text') หรือสรุปจาก type."""
    if isinstance(body, dict):
        if body.get("text"):
            return str(body["text"])
        if body.get("type"):
            # เผื่อ webhook ที่ไม่ได้ตั้ง text — สรุปคร่าวๆ
            return f"[{body['type']}] " + json.dumps(
                {k: v for k, v in body.items() if k != "type"}, ensure_ascii=False
            )
    return json.dumps(body, ensure_ascii=False)[:1000]


def create_app():
    try:
        from fastapi import FastAPI, Request
    except ImportError as e:
        raise RuntimeError("ต้องมี fastapi/uvicorn (มากับ Freqtrade)") from e

    app = FastAPI(title="ForeTrade LINE relay")

    @app.get("/health")
    async def health():  # noqa: D401
        return {"ok": True, "mode": "push" if os.getenv("LINE_TO") else "broadcast"}

    @app.post("/freqtrade")
    async def freqtrade_webhook(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {"text": (await request.body()).decode("utf-8", "ignore")}

        text = _extract_text(body)
        ok, info = _push_to_line(f"[ForeTrade] {text}")
        return {"forwarded": ok, "info": info}

    return app


def main() -> None:
    try:
        import uvicorn
    except ImportError as e:
        raise RuntimeError("ต้องมี uvicorn (มากับ Freqtrade)") from e

    host = os.getenv("LINE_RELAY_HOST", "127.0.0.1")
    port = int(os.getenv("LINE_RELAY_PORT", "8090"))
    if not os.getenv("LINE_CHANNEL_ACCESS_TOKEN"):
        print("!! เตือน: ยังไม่ได้ตั้ง LINE_CHANNEL_ACCESS_TOKEN — relay จะรับได้แต่ push ไม่ได้")
    print(f"ForeTrade LINE relay: http://{host}:{port}/freqtrade")
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
