# ForeTrade — backtest กลยุทธ์ MomentumBreakout
#
# ใช้:
#   .\foretrade_scripts\backtest.ps1                 # backtest 90 วันล่าสุด
#   .\foretrade_scripts\backtest.ps1 -Days 30
#   .\foretrade_scripts\backtest.ps1 -Timerange 20250101-20250601
#   .\foretrade_scripts\backtest.ps1 -SkipDownload   # ไม่ดาวน์โหลดข้อมูลใหม่

param(
    [int]$Days = 90,
    [string]$Timerange = "",
    [string]$Timeframe = "5m",
    [switch]$SkipDownload
)

. (Join-Path $PSScriptRoot "_common.ps1")
Assert-Freqtrade

$config = "user_data\config.dry.json"
$strategy = "MomentumBreakout"

if (-not $Timerange) {
    $start = (Get-Date).AddDays(-$Days).ToString("yyyyMMdd")
    $Timerange = "$start-"
}

if (-not $SkipDownload) {
    Write-Host "== ดาวน์โหลดข้อมูลย้อนหลัง ($Timerange, $Timeframe) ==" -ForegroundColor Cyan
    freqtrade download-data -c $config --timerange $Timerange --timeframes $Timeframe
    if ($LASTEXITCODE -ne 0) { throw "download-data ล้มเหลว" }
}

Write-Host "== backtest $strategy ($Timerange) ==" -ForegroundColor Cyan
freqtrade backtesting -c $config --strategy $strategy --timerange $Timerange --timeframe $Timeframe

Write-Host "`nเสร็จ — ผลอยู่ใน user_data\backtest_results\" -ForegroundColor Green
