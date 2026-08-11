"""
เซิร์ฟเวอร์แดชบอร์ดของ ForeTrade

ทำ 2 อย่าง:
    1) proxy ไปยัง Freqtrade REST API (จัดการ login/token ให้ฝั่งเซิร์ฟเวอร์
       เบราว์เซอร์จึงไม่ต้องยุ่งกับ auth)
    2) เรียก foretrade_ai วิเคราะห์คู่เทรด/ทรานแซกชัน

รัน:
    python -m foretrade_web.server

ตั้งค่าเป็น env (มีค่าเริ่มต้นตรงกับ config.dry.json):
    FREQTRADE_API_URL   (ค่าเริ่มต้น http://127.0.0.1:8080)
    FREQTRADE_USERNAME  (ค่าเริ่มต้น foretrade)
    FREQTRADE_PASSWORD  (ค่าเริ่มต้น CHANGE_ME_password)
    WEB_HOST / WEB_PORT (ค่าเริ่มต้น 127.0.0.1 / 8099)
    AI_PROVIDER / AI_LANG + คีย์ของ provider (สำหรับปุ่ม AI)
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

FT_URL = os.getenv("FREQTRADE_API_URL", "http://127.0.0.1:8080").rstrip("/")
FT_USER = os.getenv("FREQTRADE_USERNAME", "foretrade")
FT_PASS = os.getenv("FREQTRADE_PASSWORD", "CHANGE_ME_password")

_STATIC = Path(__file__).resolve().parent / "static"

# cache token ระหว่างคำขอ
_token: dict[str, str | None] = {"access": None}


def _login() -> str:
    creds = base64.b64encode(f"{FT_USER}:{FT_PASS}".encode()).decode()
    req = urllib.request.Request(
        f"{FT_URL}/api/v1/token/login",
        method="POST",
        headers={"Authorization": f"Basic {creds}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    _token["access"] = data["access_token"]
    return _token["access"]


def _ft_get(path: str) -> dict:
    """GET ไปยัง Freqtrade API พร้อม token (re-login อัตโนมัติเมื่อ 401)."""
    if not _token["access"]:
        _login()
    url = f"{FT_URL}{path}"
    for attempt in range(2):
        req = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {_token['access']}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 401 and attempt == 0:
                _login()
                continue
            raise


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import FileResponse, JSONResponse
    except ImportError as e:
        raise RuntimeError("ต้องมี fastapi/uvicorn (มากับ Freqtrade)") from e

    app = FastAPI(title="ForeTrade Dashboard")

    @app.get("/")
    def index():
        return FileResponse(str(_STATIC / "index.html"))

    def _proxy(path: str):
        try:
            return JSONResponse(_ft_get(path))
        except urllib.error.URLError as e:
            raise HTTPException(status_code=502, detail=f"ต่อ Freqtrade ไม่ได้: {e}")
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/ping")
    def ping():
        return _proxy("/api/v1/ping")

    @app.get("/api/status")
    def status():
        return _proxy("/api/v1/status")

    @app.get("/api/profit")
    def profit():
        return _proxy("/api/v1/profit")

    @app.get("/api/whitelist")
    def whitelist():
        return _proxy("/api/v1/whitelist")

    @app.get("/api/ai/pair")
    def ai_pair(symbol: str, provider: str | None = None, lang: str | None = None):
        try:
            from foretrade_ai.analyst import analyze_pair
            from foretrade_ai.providers import get_provider
            text = analyze_pair(symbol, provider=get_provider(provider), lang=lang)
            return {"ok": True, "text": text}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "text": f"วิเคราะห์ไม่ได้: {e}"}

    @app.get("/api/ai/trade")
    def ai_trade(trade_id: int, provider: str | None = None, lang: str | None = None,
                 db: str | None = None):
        try:
            from foretrade_ai.analyst import analyze_trade
            from foretrade_ai.providers import get_provider
            text = analyze_trade(trade_id, provider=get_provider(provider),
                                 db_path=db, lang=lang)
            return {"ok": True, "text": text}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "text": f"วิเคราะห์ไม่ได้: {e}"}

    return app


def main() -> None:
    try:
        import uvicorn
    except ImportError as e:
        raise RuntimeError("ต้องมี uvicorn (มากับ Freqtrade)") from e

    host = os.getenv("WEB_HOST", "127.0.0.1")
    port = int(os.getenv("WEB_PORT", "8099"))
    print(f"ForeTrade Dashboard: http://{host}:{port}")
    print(f"  (proxy -> Freqtrade API ที่ {FT_URL})")
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
