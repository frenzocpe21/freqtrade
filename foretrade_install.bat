@echo off
REM ============================================================
REM  ForeTrade - install everything on Windows (native)
REM  Creates .venv + installs Freqtrade (with TA-Lib wheel) + LLM SDKs + FreqUI
REM
REM  Requires: Python 3.11/3.12/3.13 and Git installed first.
REM  Usage: double-click this file, or run in cmd:  foretrade_install.bat
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo === ForeTrade installer ===
echo.

REM --- Find a supported Python (newest first) ---
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
  echo [ERROR] Python 3.11/3.12/3.13 not found.
  echo         Install from https://www.python.org/downloads/ and tick "Add Python to PATH".
  pause
  exit /b 1
)
echo -^> Using Python: %PYEXE%
%PYEXE% --version

REM --- Create venv ---
if not exist ".venv\Scripts\python.exe" (
  echo -^> Creating virtual environment (.venv)
  %PYEXE% -m venv .venv
  if errorlevel 1 ( echo [ERROR] Failed to create venv & pause & exit /b 1 )
) else (
  echo -^> .venv already exists, skipping creation
)

set "VPY=.venv\Scripts\python.exe"

echo -^> Upgrading pip/wheel
"%VPY%" -m pip install -U pip wheel
if errorlevel 1 ( echo [ERROR] Failed to upgrade pip & pause & exit /b 1 )

echo.
echo === Installing Freqtrade (from this repo + TA-Lib wheel) ===
echo     This can take several minutes...
"%VPY%" -m pip install -e .
if errorlevel 1 (
  echo [ERROR] Failed to install Freqtrade.
  echo         If it failed on TA-Lib: make sure you use Python 3.11-3.13 (other versions may lack a wheel).
  pause
  exit /b 1
)

echo.
echo === Installing LLM SDKs for AI Analyst (claude/openai/gemini) ===
"%VPY%" -m pip install -r requirements-foretrade.txt
if errorlevel 1 ( echo [WARN] Some SDKs failed - fine, install only the one you need later. )

echo.
echo === Installing FreqUI (web dashboard) ===
".venv\Scripts\freqtrade.exe" install-ui
if errorlevel 1 ( echo [WARN] install-ui failed - run later:  .venv\Scripts\freqtrade install-ui )

echo.
echo ============================================================
echo  Done!
echo  Next (open PowerShell in this folder):
echo    .\foretrade_scripts\backtest.ps1 -Days 90
echo    .\foretrade_scripts\run_dry.ps1
echo  Or see README-foretrade.md
echo ============================================================
pause
