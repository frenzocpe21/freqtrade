# ForeTrade - run dry-run (paper trading) + FreqUI
#
# Usage:
#   .\foretrade_scripts\run_dry.ps1
#
# Web dashboard at http://127.0.0.1:8080 (FreqUI). Install it once with:
#   freqtrade install-ui

. (Join-Path $PSScriptRoot "_common.ps1")
Assert-Freqtrade

$config = "user_data\config.dry.json"
$strategy = "MomentumBreakout"

Write-Host "== ForeTrade dry-run (paper money) - Ctrl+C to stop ==" -ForegroundColor Cyan
Write-Host "   FreqUI: http://127.0.0.1:8080  (login per config.dry.json)" -ForegroundColor DarkGray

freqtrade trade -c $config --strategy $strategy
