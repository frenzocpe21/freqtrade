@echo off
REM ============================================================
REM  ForeTrade - control the bot via Docker
REM  Requires Docker Desktop / Docker Engine to be running.
REM
REM  Double-click for a looping menu, or run from cmd:
REM    foretrade_docker.bat up | logs | down | data | backtest | ui | test
REM                       | list | import | compare
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
echo   8^) list      List available strategies
echo   9^) import    Download a strategy .py from a URL
echo  10^) compare   Backtest several strategies side by side
echo  11^) web       Start Thai dashboard (http://127.0.0.1:8099)
echo   0^) exit
echo ===========================================
set "SEL="
set /p "SEL=Type 0-11 and press Enter: "
if "%SEL%"=="0" goto :eof
if "%SEL%"=="1"  ( call :dispatch ui       & goto :menu )
if "%SEL%"=="2"  ( call :dispatch data     & goto :menu )
if "%SEL%"=="3"  ( call :dispatch backtest & goto :menu )
if "%SEL%"=="4"  ( call :dispatch up       & goto :menu )
if "%SEL%"=="5"  ( call :dispatch logs     & goto :menu )
if "%SEL%"=="6"  ( call :dispatch down     & goto :menu )
if "%SEL%"=="7"  ( call :dispatch test     & goto :menu )
if "%SEL%"=="8"  ( call :dispatch list     & goto :menu )
if "%SEL%"=="9"  ( call :dispatch import   & goto :menu )
if "%SEL%"=="10" ( call :dispatch compare  & goto :menu )
if "%SEL%"=="11" ( call :dispatch web      & goto :menu )
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
if /i "%CMD%"=="list"     goto :do_list
if /i "%CMD%"=="import"   goto :do_import
if /i "%CMD%"=="compare"  goto :do_compare
if /i "%CMD%"=="web"      goto :do_web
echo Unknown command "%CMD%" - choose: up^|logs^|down^|data^|backtest^|ui^|test^|list^|import^|compare^|web
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

:do_list
echo -^> Available strategies (use these names in 'compare'):
%RUN% list-strategies %CFG%
exit /b 0

:do_import
echo -^> Download a strategy .py into user_data\strategies\
echo    Paste a raw URL, e.g. https://raw.githubusercontent.com/user/repo/main/MyStrat.py
set "URL="
set /p "URL=URL: "
if "%URL%"=="" ( echo Cancelled. & exit /b 1 )
REM GitHub 'blob' URL -> raw URL
echo %URL% | findstr /i "github.com" >nul && echo %URL% | findstr /i "/blob/" >nul && (
  set "URL=%URL:github.com=raw.githubusercontent.com%"
  set "URL=%URL:/blob/=/%"
)
for %%F in ("%URL%") do set "FNAME=%%~nxF"
if "%FNAME%"=="" set "FNAME=imported_strategy.py"
echo -^> Saving as user_data\strategies\%FNAME%
curl -L -o "user_data\strategies\%FNAME%" "%URL%"
if errorlevel 1 ( echo [ERROR] Download failed. & exit /b 1 )
echo Done. Run 'list' to see its class name, then 'compare'.
exit /b 0

:do_compare
echo -^> Backtest several strategies side by side (needs data - run 'data' first)
echo    Enter CLASS names separated by spaces (see 'list'), e.g. MomentumBreakout OtherStrat
set "NAMES="
set /p "NAMES=Strategies: "
if "%NAMES%"=="" ( echo Cancelled. & exit /b 1 )
%RUN% backtesting %CFG% --strategy-list %NAMES% --timerange=-90 --timeframe 5m
exit /b 0

:do_web
echo -^> Starting Thai dashboard container...
echo    (installs AI SDKs on first run - may take ~30s)
%COMPOSE% up -d foretrade-web
echo.
echo    Dashboard: http://127.0.0.1:8099
echo    For AI buttons, put your keys in a .env file next to this script, e.g:
echo      AI_PROVIDER=claude
echo      ANTHROPIC_API_KEY=sk-ant-...
echo    then run 'web' again.
start "" http://127.0.0.1:8099
exit /b 0
