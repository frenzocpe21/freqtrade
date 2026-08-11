# Shared helper: locate repo root and activate venv (.venv) if present.
# Dot-sourced by the other scripts.

$ErrorActionPreference = "Stop"

# repo root = parent of foretrade_scripts
$script:RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $script:RepoRoot

# Activate venv if not already active
if (-not $env:VIRTUAL_ENV) {
    $venvActivate = Join-Path $script:RepoRoot ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvActivate) {
        Write-Host "-> activating venv (.venv)" -ForegroundColor DarkGray
        & $venvActivate
    } else {
        Write-Host "!! .venv not found - run foretrade_install.bat first" -ForegroundColor Yellow
    }
}

function Assert-Freqtrade {
    if (-not (Get-Command freqtrade -ErrorAction SilentlyContinue)) {
        throw "'freqtrade' command not found - venv not installed/activated (see README-foretrade.md)"
    }
}
