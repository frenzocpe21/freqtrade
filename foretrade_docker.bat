@echo off
REM ============================================================
REM  ForeTrade - control the bot via Docker
REM  Requires Docker Desktop / Docker Engine to be running.
REM
REM  Double-click for a looping menu, or run from cmd:
REM    foretrade_docker.bat up | logs | down | data | backtest | ui | test
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

REM --- If an argument was passed, run it once and exit ---
if not "%~1"=="" (
  call :dispatch "%~1"
  goto :eof
)

REM --- No argument (double-click): loop the menu ---
:menu
echo.
echo ============= ForeTrade Docker =============
echo   1^) ui        Install FreqUI in container ^(first time^)
echo   2^) data      Download 90 days of history
echo   3^) backtest  Backtest the strategy
echo   4^) up        Run dry-run in background + FreqUI
echo   5^) logs      Follow live logs ^(Ctrl+C to return^)
echo   6^) down      Stop the bot
echo   7^) test      Run once in foreground to SHOW ERRORS
echo   0^) exit
echo ===========================================
set "SEL="
set /p "SEL=Type 0-7 and press Enter: "
if "%SEL%"=="0" goto :eof
if "%SEL%"=="1" ( call :dispatch ui       & goto :menu )
if "%SEL%"=="2" ( call :dispatch data     & goto :menu )
if "%SEL%"=="3" ( call :dispatch backtest & goto :menu )
if "%SEL%"=="4" ( call :dispatch up       & goto :menu )
if "%SEL%"=="5" ( call :dispatch logs     & goto :menu )
if "%SEL%"=="6" ( call :dispatch down     & goto :menu )
if "%SEL%"=="7" ( call :dispatch test     & goto :menu )
echo Invalid choice: %SEL%
goto :menu

REM ============================================================
:dispatch
set "CMD=%~1"
if /i "%CMD%"=="up"       goto :do_up
if /i "%CMD%"=="logs"     goto :do_logs
if /i "%CMD%"=="down"     goto :do_down
if /i "%CMD%"=="data"     goto :do_data
if /i "%CMD%"=="backtest" goto :do_backtest
if /i "%CMD%"=="ui"       goto :do_ui
if /i "%CMD%"=="test"     goto :do_test
echo Unknown command "%CMD%" - choose: up^|logs^|down^|data^|backtest^|ui^|test
exit /b 1

:do_up
echo -^> Starting ForeTrade (dry-run) in background...
%COMPOSE% up -d
echo.
echo    FreqUI: http://127.0.0.1:8080  (login per config.dry.json)
echo    If it keeps restarting, use option 7 (test) to see the error.
echo.
exit /b 0

:do_logs
echo -^> Following logs (Ctrl+C to return to menu)
%COMPOSE% logs -f
exit /b 0

:do_down
%COMPOSE% down
exit /b 0

:do_ui
echo -^> Installing FreqUI in container...
%RUN% install-ui
exit /b 0

:do_data
echo -^> Downloading 90 days of data (5m)...
%RUN% download-data %CFG% --days 90 --timeframes 5m
exit /b 0

:do_backtest
echo -^> Backtesting MomentumBreakout (90 days)...
%RUN% backtesting %CFG% %STRAT% --timerange=-90 --timeframe 5m
exit /b 0

:do_test
echo -^> Foreground run (no restart) - watch for errors, Ctrl+C to stop
%RUN% trade %CFG% --config /freqtrade/user_data/config.docker-override.json %STRAT%
exit /b 0
