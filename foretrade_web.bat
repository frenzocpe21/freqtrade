@echo off
REM ============================================================
REM  ForeTrade - launch the Thai companion dashboard
REM  Runs on the host and talks to the bot's REST API at 127.0.0.1:8080
REM  (works whether the bot runs in Docker or natively).
REM
REM  Needs Python with: fastapi, uvicorn, and your AI provider SDK.
REM  Easiest: run foretrade_install.bat first (creates .venv with everything).
REM
REM  Open the dashboard at: http://127.0.0.1:8099
REM ============================================================
setlocal
cd /d "%~dp0"

REM --- Pick interpreter: prefer .venv, else py/python ---
set "PYCMD="
if exist ".venv\Scripts\python.exe" (
  set "PYCMD=.venv\Scripts\python.exe"
) else (
  for %%V in (3.13 3.12 3.11) do (
    if not defined PYCMD ( py -%%V --version >nul 2>&1 && set "PYCMD=py -%%V" )
  )
  if not defined PYCMD ( where python >nul 2>&1 && set "PYCMD=python" )
)
if not defined PYCMD (
  echo [ERROR] Python not found. Run foretrade_install.bat first, or install Python 3.11-3.13.
  pause
  exit /b 1
)

echo -^> Using: %PYCMD%
echo -^> Dashboard: http://127.0.0.1:8099   (bot API expected at http://127.0.0.1:8080)
echo    Set your AI key first if you want the AI buttons, e.g:
echo      set ANTHROPIC_API_KEY=sk-ant-...
echo.
%PYCMD% -m foretrade_web.server
if errorlevel 1 (
  echo.
  echo [ERROR] Failed to start. If a module is missing, install:
  echo    %PYCMD% -m pip install fastapi uvicorn anthropic
  pause
)
