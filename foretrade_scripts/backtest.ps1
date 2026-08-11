# ForeTrade - backtest the MomentumBreakout strategy
#
# Usage:
#   .\foretrade_scripts\backtest.ps1                 # backtest last 90 days
#   .\foretrade_scripts\backtest.ps1 -Days 30
#   .\foretrade_scripts\backtest.ps1 -Timerange 20250101-20250601
#   .\foretrade_scripts\backtest.ps1 -SkipDownload   # do not re-download data

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
    Write-Host "== Downloading history ($Timerange, $Timeframe) ==" -ForegroundColor Cyan
    freqtrade download-data -c $config --timerange $Timerange --timeframes $Timeframe
    if ($LASTEXITCODE -ne 0) { throw "download-data failed" }
}

Write-Host "== Backtesting $strategy ($Timerange) ==" -ForegroundColor Cyan
freqtrade backtesting -c $config --strategy $strategy --timerange $Timerange --timeframe $Timeframe

Write-Host "`nDone - results in user_data\backtest_results\" -ForegroundColor Green
