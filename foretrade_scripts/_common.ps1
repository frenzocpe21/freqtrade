# ตัวช่วยร่วม: หา repo root และ activate venv (.venv) ถ้ามี
# ไฟล์นี้ถูก dot-source โดยสคริปต์อื่น

$ErrorActionPreference = "Stop"

# repo root = โฟลเดอร์แม่ของ foretrade_scripts
$script:RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $script:RepoRoot

# พยายาม activate venv ถ้ายังไม่อยู่ใน venv
if (-not $env:VIRTUAL_ENV) {
    $venvActivate = Join-Path $script:RepoRoot ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvActivate) {
        Write-Host "-> activating venv (.venv)" -ForegroundColor DarkGray
        & $venvActivate
    } else {
        Write-Host "!! ไม่พบ .venv — ถ้ายังไม่ติดตั้ง ให้รัน setup.ps1 ของ Freqtrade ก่อน" -ForegroundColor Yellow
    }
}

function Assert-Freqtrade {
    if (-not (Get-Command freqtrade -ErrorAction SilentlyContinue)) {
        throw "ไม่พบคำสั่ง 'freqtrade' — ยังไม่ได้ติดตั้ง/activate venv (ดู README-foretrade.md)"
    }
}
