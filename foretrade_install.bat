@echo off
REM ============================================================
REM  ForeTrade — ติดตั้งทุกอย่างที่จำเป็นบน Windows (native)
REM  สร้าง .venv + ติดตั้ง Freqtrade (มี TA-Lib wheel) + SDK ของ LLM + FreqUI
REM
REM  ต้องมี: Python 3.11/3.12/3.13 และ Git ติดตั้งไว้ก่อน
REM  วิธีใช้: ดับเบิลคลิกไฟล์นี้ หรือรันใน cmd:  foretrade_install.bat
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo === ForeTrade installer ===
echo.

REM --- หา Python ที่รองรับ (ไล่จากใหม่ไปเก่า) ---
set "PYEXE="
for %%V in (3.13 3.12 3.11) do (
  if not defined PYEXE (
    py -%%V --version >nul 2>&1 && set "PYEXE=py -%%V"
  )
)
if not defined PYEXE (
  where python >nul 2>&1 && set "PYEXE=python"
)
if not defined PYEXE (
  echo [ERROR] ไม่พบ Python 3.11/3.12/3.13 — ติดตั้งจาก https://www.python.org/downloads/ ก่อน
  echo         ตอนติดตั้งให้ติ๊ก "Add Python to PATH"
  pause
  exit /b 1
)
echo -^> ใช้ Python: %PYEXE%
%PYEXE% --version

REM --- สร้าง venv ---
if not exist ".venv\Scripts\python.exe" (
  echo -^> สร้าง virtual environment (.venv)
  %PYEXE% -m venv .venv
  if errorlevel 1 ( echo [ERROR] สร้าง venv ไม่สำเร็จ & pause & exit /b 1 )
) else (
  echo -^> พบ .venv อยู่แล้ว ข้ามการสร้าง
)

set "VPY=.venv\Scripts\python.exe"

echo -^> อัปเกรด pip/wheel
"%VPY%" -m pip install -U pip wheel
if errorlevel 1 ( echo [ERROR] อัปเกรด pip ไม่สำเร็จ & pause & exit /b 1 )

echo.
echo === ติดตั้ง Freqtrade (จาก source ใน repo นี้ + TA-Lib wheel) ===
echo     ขั้นนี้ใช้เวลาหลายนาที...
"%VPY%" -m pip install -e .
if errorlevel 1 (
  echo [ERROR] ติดตั้ง Freqtrade ไม่สำเร็จ
  echo         ถ้าติดที่ TA-Lib: ตรวจว่าใช้ Python 3.11-3.13 (เวอร์ชันอื่นอาจยังไม่มี wheel)
  pause
  exit /b 1
)

echo.
echo === ติดตั้ง SDK ของ LLM สำหรับ AI Analyst (claude/openai/gemini) ===
"%VPY%" -m pip install -r requirements-foretrade.txt
if errorlevel 1 ( echo [WARN] ติดตั้ง SDK บางตัวไม่สำเร็จ — ข้ามได้ ติดตั้งเฉพาะเจ้าที่จะใช้ทีหลังก็ได้ )

echo.
echo === ติดตั้ง FreqUI (เว็บแดชบอร์ด) ===
".venv\Scripts\freqtrade.exe" install-ui
if errorlevel 1 ( echo [WARN] install-ui ไม่สำเร็จ — รันเองภายหลังได้:  .venv\Scripts\freqtrade install-ui )

echo.
echo ============================================================
echo  ติดตั้งเสร็จ!
echo  ขั้นต่อไป (เปิด PowerShell ในโฟลเดอร์นี้):
echo    .\foretrade_scripts\backtest.ps1 -Days 90
echo    .\foretrade_scripts\run_dry.ps1
echo  หรือดู README-foretrade.md
echo ============================================================
pause
