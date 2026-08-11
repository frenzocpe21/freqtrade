@echo off
REM ============================================================
REM  ForeTrade — ควบคุมบอทผ่าน Docker
REM  ต้องมี Docker Desktop / Docker Engine ทำงานอยู่
REM
REM  วิธีใช้:
REM    foretrade_docker.bat up            รัน dry-run เบื้องหลัง + เปิด FreqUI
REM    foretrade_docker.bat logs          ดู log สด (Ctrl+C ออก)
REM    foretrade_docker.bat down          หยุดบอท
REM    foretrade_docker.bat data          ดาวน์โหลดข้อมูลย้อนหลัง 90 วัน
REM    foretrade_docker.bat backtest      backtest กลยุทธ์
REM    foretrade_docker.bat ui            ติดตั้ง FreqUI ในคอนเทนเนอร์ (ครั้งแรก)
REM ============================================================
setlocal
cd /d "%~dp0"

set "COMPOSE=docker compose -f docker-compose.foretrade.yml"
set "RUN=%COMPOSE% run --rm foretrade"
set "CFG=--config /freqtrade/user_data/config.dry.json"
set "STRAT=--strategy MomentumBreakout"

docker version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] ไม่พบ Docker หรือ Docker ยังไม่ทำงาน — เปิด Docker Desktop ก่อน
  exit /b 1
)

if "%~1"=="" goto :help
if /i "%~1"=="up"       goto :up
if /i "%~1"=="logs"     goto :logs
if /i "%~1"=="down"     goto :down
if /i "%~1"=="data"     goto :data
if /i "%~1"=="backtest" goto :backtest
if /i "%~1"=="ui"       goto :ui
goto :help

:up
echo -^> เริ่ม ForeTrade (dry-run) เบื้องหลัง...
%COMPOSE% up -d
echo    FreqUI: http://127.0.0.1:8080  (login ตาม config.dry.json)
echo    ดู log:  foretrade_docker.bat logs
goto :eof

:logs
%COMPOSE% logs -f
goto :eof

:down
%COMPOSE% down
goto :eof

:ui
echo -^> ติดตั้ง FreqUI ในคอนเทนเนอร์
%RUN% install-ui
goto :eof

:data
echo -^> ดาวน์โหลดข้อมูล 90 วัน (5m)
%RUN% download-data %CFG% --days 90 --timeframes 5m
goto :eof

:backtest
echo -^> backtest MomentumBreakout (90 วัน)
%RUN% backtesting %CFG% %STRAT% --timerange=-90 --timeframe 5m
goto :eof

:help
echo.
echo ForeTrade Docker — คำสั่ง: up ^| logs ^| down ^| data ^| backtest ^| ui
echo   ครั้งแรกแนะนำ:  foretrade_docker.bat ui  แล้ว  data  แล้ว  backtest  แล้ว  up
echo.
goto :eof
