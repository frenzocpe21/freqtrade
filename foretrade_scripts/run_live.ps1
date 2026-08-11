# ForeTrade — รันโหมดเงินจริง (LIVE)  ⚠️ เทรดด้วยเงินจริง
#
# ก่อนรัน:
#   1) คัดลอก user_data\config.live.json.example -> user_data\config.live.json
#   2) ใส่ API key/secret ของคุณเอง และตรวจ dry_run=false
#   3) ผ่าน dry-run มาแล้ว มั่นใจใน edge + คุมความเสี่ยงได้
#
# ใช้:
#   .\foretrade_scripts\run_live.ps1

. (Join-Path $PSScriptRoot "_common.ps1")
Assert-Freqtrade

$config = "user_data\config.live.json"
$strategy = "MomentumBreakout"

if (-not (Test-Path $config)) {
    throw "ไม่พบ $config — คัดลอกจาก config.live.json.example แล้วใส่คีย์ของคุณก่อน"
}

Write-Host "==========================================================" -ForegroundColor Red
Write-Host "  โหมด LIVE — จะเทรดด้วยเงินจริงบนบัญชีของคุณ" -ForegroundColor Red
Write-Host "==========================================================" -ForegroundColor Red
$confirm = Read-Host "พิมพ์ 'LIVE' เพื่อยืนยันเริ่มเทรดจริง (อื่นๆ = ยกเลิก)"
if ($confirm -ne "LIVE") {
    Write-Host "ยกเลิกแล้ว" -ForegroundColor Yellow
    exit 0
}

freqtrade trade -c $config --strategy $strategy
