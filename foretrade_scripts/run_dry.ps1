# ForeTrade — รันโหมดจำลอง (dry-run) + เปิด FreqUI
#
# ใช้:
#   .\foretrade_scripts\run_dry.ps1
#
# เปิดเว็บแดชบอร์ดที่ http://127.0.0.1:8080 (FreqUI) — ต้องติดตั้ง FreqUI ครั้งแรกด้วย:
#   freqtrade install-ui

. (Join-Path $PSScriptRoot "_common.ps1")
Assert-Freqtrade

$config = "user_data\config.dry.json"
$strategy = "MomentumBreakout"

Write-Host "== ForeTrade dry-run (เงินปลอม) — Ctrl+C เพื่อหยุด ==" -ForegroundColor Cyan
Write-Host "   FreqUI: http://127.0.0.1:8080  (login ตาม config.dry.json)" -ForegroundColor DarkGray

freqtrade trade -c $config --strategy $strategy
