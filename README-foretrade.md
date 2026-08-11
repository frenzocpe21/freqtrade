# ForeTrade — บอทเทรดคริปโตอัตโนมัติ (บนฐาน Freqtrade)

บอทเทรดคริปโต **Perpetual Futures (Binance)** ที่ "เปิดทิ้งไว้แล้วทำงานเอง" มีทั้ง
**โหมดจำลอง (dry-run)** และ **โหมดเงินจริง (live)** พร้อมเว็บแดชบอร์ด (FreqUI),
กลยุทธ์ Momentum Breakout, ตัวคัดคู่เทรดอัตโนมัติ, และ **AI Analyst** วิเคราะห์รายคู่/รายไม้แบบ on-demand

> โปรเจกต์นี้ต่อยอดบน [Freqtrade](https://www.freqtrade.io/) — ไฟล์ส่วนใหญ่เป็นของ Freqtrade
> ส่วนที่เราเพิ่มคือ `user_data/strategies/momentum_breakout.py`, `user_data/config.*`,
> `foretrade_scripts/`, `foretrade_ai/`, `foretrade_line/`

## ⚠️ อ่านก่อน
- **ไม่มีบอทใดการันตีกำไร** — Momentum Breakout เป็นแค่จุดเริ่มต้น ต้อง **backtest → dry-run** พิสูจน์ว่ามี edge ก่อนเสมอ
- ลำดับที่ปลอดภัย: **backtest → dry-run (หลายสัปดาห์) → live เงินก้อนเล็ก**
- โหมด live ใช้ **API key ของคุณเอง**, คุณเป็นผู้ตั้ง `dry_run:false` และยืนยันเอง
- AI Analyst เป็นเครื่องมือ **วิเคราะห์/อธิบาย** เท่านั้น ไม่ใช่คำแนะนำการลงทุน และไม่เชื่อมให้ยิงออเดอร์

---

## 1) ติดตั้ง (ครั้งเดียว) — เลือกทางใดทางหนึ่ง

### ทาง A: Docker (แนะนำ — สะอาดสุด ไม่ต้องติดตั้ง Python/TA-Lib)
ต้องมี **Docker Desktop** (Windows/Mac) หรือ Docker Engine (Linux/WSL)

```bat
foretrade_docker.bat ui        REM ติดตั้ง FreqUI ในคอนเทนเนอร์ (ครั้งแรก)
foretrade_docker.bat data      REM ดาวน์โหลดข้อมูลย้อนหลัง 90 วัน
foretrade_docker.bat backtest  REM ทดสอบกลยุทธ์
foretrade_docker.bat up        REM รัน dry-run + เปิด FreqUI (http://127.0.0.1:8080)
foretrade_docker.bat logs      REM ดู log สด
foretrade_docker.bat down      REM หยุด
```

### ทาง B: Native Windows (ติดตั้งลงเครื่อง)
ต้องมี **Python 3.11/3.12/3.13** และ Git — แล้วดับเบิลคลิก/รัน:

```bat
foretrade_install.bat
```

ไฟล์นี้จะสร้าง `.venv`, ติดตั้ง Freqtrade (มี TA-Lib wheel), SDK ของ LLM, และ FreqUI ให้อัตโนมัติ

> **ก่อนใช้จริง** เปิด `user_data/config.dry.json` แล้วเปลี่ยนค่า `CHANGE_ME_*`
> (`jwt_secret_key`, `ws_token`, `password`) ใน `api_server`
>
> หัวข้อ 2-3, 6 ด้านล่างเป็นคำสั่งสำหรับ **ทาง B (native)**; ถ้าใช้ Docker ให้ใช้คำสั่ง
> `foretrade_docker.bat ...` แทนตามด้านบน

---

## 2) Backtest — พิสูจน์กลยุทธ์กับข้อมูลย้อนหลัง

```powershell
.\foretrade_scripts\backtest.ps1 -Days 90
```

ดูสถิติ win rate / PnL / drawdown ที่ออกมา ผลไฟล์อยู่ใน `user_data/backtest_results/`
(ปรับพารามิเตอร์กลยุทธ์ทีหลังได้ หรือจูนด้วย `freqtrade hyperopt`)

ตรวจว่ากลยุทธ์โหลดได้:

```bash
freqtrade list-strategies
```

ตรวจตัวคัดคู่ (Instrument Profiler):

```bash
freqtrade test-pairlist -c user_data/config.dry.json
```

---

## 3) Dry-run — รันจริง เงินปลอม + เปิดแดชบอร์ด

```powershell
.\foretrade_scripts\run_dry.ps1
```

เปิดเบราว์เซอร์ที่ **http://127.0.0.1:8080** (FreqUI) เพื่อดู PnL/โพสิชันสด และสั่ง stop/forceexit ได้
ปล่อยรันหลายสัปดาห์เพื่อดูว่ากลยุทธ์มี edge จริงไหม

---

## 4) AI Analyst — วิเคราะห์แบบ on-demand (Claude / ChatGPT / Gemini)

เลือก provider และตั้งคีย์ (ตั้งเฉพาะเจ้าที่ใช้):

```powershell
$env:AI_PROVIDER = "claude"          # หรือ openai / gemini
$env:ANTHROPIC_API_KEY = "sk-ant-..." # ถ้าใช้ Claude
# $env:OPENAI_API_KEY = "sk-..."      # ถ้าใช้ ChatGPT
# $env:GEMINI_API_KEY = "..."         # ถ้าใช้ Gemini
```

วิเคราะห์คู่เทรด:

```bash
python -m foretrade_ai.cli analyze-pair BTC/USDT:USDT
python -m foretrade_ai.cli analyze-pair ETH/USDT --provider gemini --timeframe 15m
```

วิเคราะห์กำไร/ขาดทุนของทรานแซกชัน (จาก dry-run/live DB):

```bash
python -m foretrade_ai.cli analyze-trade 42
python -m foretrade_ai.cli analyze-trade 42 --provider openai --db tradesv3.dryrun.sqlite
```

เลือกภาษาผลลัพธ์ (ไทย/อังกฤษ):

```bash
python -m foretrade_ai.cli analyze-pair BTC/USDT --lang en   # อังกฤษ
python -m foretrade_ai.cli analyze-pair BTC/USDT --lang th   # ไทย (ค่าเริ่มต้น)
# หรือตั้งถาวร: $env:AI_LANG = "en"
```

> เปลี่ยนรุ่นโมเดลได้ผ่าน env `ANTHROPIC_MODEL` / `OPENAI_MODEL` / `GEMINI_MODEL`
> ผลลัพธ์มี disclaimer เสมอ และไม่มีการยิงออเดอร์ใดๆ
>
> **หมายเหตุ:** FreqUI (เว็บแดชบอร์ด) รองรับเฉพาะภาษาอังกฤษ — ปุ่มสลับ TH/EN มีเฉพาะใน AI Analyst

---

## 5) แจ้งเตือนเข้า LINE (ฟรี, ไม่บังคับ)

LINE Notify ปิดบริการแล้ว — ใช้ **LINE Messaging API** (Official Account ฟรี) ผ่าน relay ของเรา

1. สร้าง LINE Official Account + Messaging API channel ที่ [LINE Developers](https://developers.line.biz/) → เอา **Channel access token**
2. ตั้งค่าและรัน relay:
   ```powershell
   $env:LINE_CHANNEL_ACCESS_TOKEN = "..."
   # $env:LINE_TO = "Uxxxx"   # ระบุ userId ถ้าจะ push ตรง; ไม่ตั้ง = broadcast หาผู้ติดตามทุกคน
   python -m foretrade_line.relay
   ```
3. เปิดบล็อก `webhook` ใน `user_data/config.dry.json` เป็น `"enabled": true`
   (url ตั้งเป็น `http://127.0.0.1:8090/freqtrade` อยู่แล้ว) แล้วรีสตาร์ทบอท

> **Free tier จำกัด push ~500 ข้อความ/เดือน** — config ตั้งให้แจ้งเฉพาะ entry_fill/exit_fill
> ถ้าเทรดถี่มากอาจเกินโควตา ปรับให้แจ้งเฉพาะเหตุการณ์สำคัญได้

---

## 6) Live — เทรดเงินจริง (ทำเองเมื่อพร้อม)

1. คัดลอก config: `copy user_data\config.live.json.example user_data\config.live.json`
2. ทดสอบกับ **Binance testnet** ก่อน (เปิด `"sandbox": true` ใน `ccxt_config` + ใช้คีย์ testnet)
3. เมื่อมั่นใจ → ใส่คีย์จริง (แนะนำเปิดสิทธิ์เทรดเท่านั้น ปิดสิทธิ์ถอน), ตั้ง `dry_run:false`, เงินก้อนเล็ก
4. รัน:
   ```powershell
   .\foretrade_scripts\run_live.ps1
   ```
   (สคริปต์จะให้พิมพ์ `LIVE` ยืนยันก่อนเริ่ม)

---

## โครงสร้างที่เราเพิ่ม

```
foretrade_install.bat                        ติดตั้ง native Windows อัตโนมัติ
foretrade_docker.bat                         ควบคุมบอทผ่าน Docker
docker-compose.foretrade.yml                 บริการ Docker (dry + MomentumBreakout)
user_data/config.docker-override.json        override api_server ตอนรันใน Docker
user_data/strategies/momentum_breakout.py    กลยุทธ์ Momentum Breakout (pluggable)
user_data/config.dry.json                    config โหมดจำลอง + pairlist คัดคู่ + webhook/api
user_data/config.live.json.example           ตัวอย่าง config โหมดจริง (ใส่คีย์เอง)
foretrade_scripts/*.ps1                       สคริปต์ backtest / run_dry / run_live
foretrade_ai/                                 AI Analyst (provider: claude/openai/gemini)
foretrade_line/                               relay แจ้งเตือนไป LINE
```

## Git (fork ของคุณเอง)

ทำงานบน branch `foretrade`. commit เฉพาะไฟล์ ForeTrade — `.gitignore` กันไฟล์ที่มีความลับ
(`config.live.json`, `*.sqlite`, `.env`) ไว้แล้ว ตรวจก่อน push เสมอ:

```bash
git status
git add -A && git commit -m "ForeTrade: strategy + configs + AI analyst + LINE relay"
git push origin foretrade
```
