# ForeTrade - run LIVE mode  (!) trades with real money
#
# Before running:
#   1) copy user_data\config.live.json.example -> user_data\config.live.json
#   2) add your API key/secret and confirm dry_run=false
#   3) you have passed dry-run and are confident in the edge + risk controls
#
# Usage:
#   .\foretrade_scripts\run_live.ps1

. (Join-Path $PSScriptRoot "_common.ps1")
Assert-Freqtrade

$config = "user_data\config.live.json"
$strategy = "MomentumBreakout"

if (-not (Test-Path $config)) {
    throw "$config not found - copy from config.live.json.example and add your keys first"
}

Write-Host "==========================================================" -ForegroundColor Red
Write-Host "  LIVE MODE - this will trade with REAL money" -ForegroundColor Red
Write-Host "==========================================================" -ForegroundColor Red
$confirm = Read-Host "Type 'LIVE' to confirm real trading (anything else = cancel)"
if ($confirm -ne "LIVE") {
    Write-Host "Cancelled" -ForegroundColor Yellow
    exit 0
}

freqtrade trade -c $config --strategy $strategy
