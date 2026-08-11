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

## 1) ติดตั้ง (ครั้งเดียว)

ต้องมี **Python 3.11+** และ Git บน Windows แล้วรัน setup ของ Freqtrade (สร้าง venv + ติดตั้ง TA-Lib ให้):

```powershell
.\setup.ps1 -Install
```

จากนั้น activate venv และติดตั้ง SDK ของ LLM ที่จะใช้ (เลือกเฉพาะเจ้าที่ต้องการ):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-foretrade.txt
```

ติดตั้ง FreqUI (เว็บแดชบอร์ด) ครั้งแรก:

```bash
freqtrade install-ui
```

> **ก่อนใช้จริง** เปิด `user_data/config.dry.json` แล้วเปลี่ยนค่า `CHANGE_ME_*`
> (`jwt_secret_key`, `ws_token`, `password`) ใน `api_server`

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

> เปลี่ยนรุ่นโมเดลได้ผ่าน env `ANTHROPIC_MODEL` / `OPENAI_MODEL` / `GEMINI_MODEL`
> ผลลัพธ์มี disclaimer เสมอ และไม่มีการยิงออเดอร์ใดๆ

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
user_data/strategies/momentum_breakout.py   กลยุทธ์ Momentum Breakout (pluggable)
user_data/config.dry.json                   config โหมดจำลอง + pairlist คัดคู่ + webhook/api
user_data/config.live.json.example          ตัวอย่าง config โหมดจริง (ใส่คีย์เอง)
foretrade_scripts/*.ps1                      สคริปต์ backtest / run_dry / run_live
foretrade_ai/                                AI Analyst (provider: claude/openai/gemini)
foretrade_line/                              relay แจ้งเตือนไป LINE
```

## Git (fork ของคุณเอง)

ทำงานบน branch `foretrade`. commit เฉพาะไฟล์ ForeTrade — `.gitignore` กันไฟล์ที่มีความลับ
(`config.live.json`, `*.sqlite`, `.env`) ไว้แล้ว ตรวจก่อน push เสมอ:

```bash
git status
git add -A && git commit -m "ForeTrade: strategy + configs + AI analyst + LINE relay"
git push origin foretrade
```
