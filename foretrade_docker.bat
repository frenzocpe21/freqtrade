@echo off
REM ============================================================
REM  ForeTrade - control the bot via Docker
REM  Requires Docker Desktop / Docker Engine to be running.
REM
REM  Double-click this file to get a menu, or run from cmd:
REM    foretrade_docker.bat up | logs | down | data | backtest | ui
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "COMPOSE=docker compose -f docker-compose.foretrade.yml"
set "RUN=%COMPOSE% run --rm foretrade"
set "CFG=--config /freqtrade/user_data/config.dry.json"
set "STRAT=--strategy MomentumBreakout"

REM --- Check Docker is installed and running ---
docker version >nul 2>&1
if errorlevel 1 (
  echo.
  echo [ERROR] Docker not found or not running.
  echo         - Install Docker Desktop: https://www.docker.com/products/docker-desktop/
  echo         - Open Docker Desktop, wait until status = Running, then retry.
  echo.
  pause
  exit /b 1
)

set "CMD=%~1"

REM --- No argument (double-click) -> show menu ---
if "%CMD%"=="" (
  echo.
  echo ============= ForeTrade Docker =============
  echo   1^) ui        Install FreqUI in container ^(first time^)
  echo   2^) data      Download 90 days of history
  echo   3^) backtest  Backtest the strategy
  echo   4^) up        Run dry-run + open FreqUI
  echo   5^) logs      Follow live logs
  echo   6^) down      Stop the bot
  echo ===========================================
  set /p "SEL=Type 1-6 and press Enter: "
  if "!SEL!"=="1" set "CMD=ui"
  if "!SEL!"=="2" set "CMD=data"
  if "!SEL!"=="3" set "CMD=backtest"
  if "!SEL!"=="4" set "CMD=up"
  if "!SEL!"=="5" set "CMD=logs"
  if "!SEL!"=="6" set "CMD=down"
)

if /i "%CMD%"=="up"       goto :up
if /i "%CMD%"=="logs"     goto :logs
if /i "%CMD%"=="down"     goto :down
if /i "%CMD%"=="data"     goto :data
if /i "%CMD%"=="backtest" goto :backtest
if /i "%CMD%"=="ui"       goto :ui

echo.
echo Unknown command "%CMD%" - choose: up ^| logs ^| down ^| data ^| backtest ^| ui
echo.
pause
exit /b 1

:up
echo -^> Starting ForeTrade (dry-run) in background...
%COMPOSE% up -d
echo.
echo    FreqUI: http://127.0.0.1:8080  (login per config.dry.json)
echo    Logs:   foretrade_docker.bat logs
echo.
pause
goto :eof

:logs
echo -^> Following logs (Ctrl+C to exit)
%COMPOSE% logs -f
goto :eof

:down
%COMPOSE% down
echo.
pause
goto :eof

:ui
echo -^> Installing FreqUI in container...
%RUN% install-ui
echo.
pause
goto :eof

:data
echo -^> Downloading 90 days of data (5m)...
%RUN% download-data %CFG% --days 90 --timeframes 5m
echo.
pause
goto :eof

:backtest
echo -^> Backtesting MomentumBreakout (90 days)...
%RUN% backtesting %CFG% %STRAT% --timerange=-90 --timeframe 5m
echo.
pause
goto :eof
