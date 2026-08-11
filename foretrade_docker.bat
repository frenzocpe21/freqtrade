@echo off
REM ============================================================
REM  ForeTrade — ควบคุมบอทผ่าน Docker
REM  ต้องมี Docker Desktop / Docker Engine ทำงานอยู่
REM
REM  ดับเบิลคลิกไฟล์นี้ = ขึ้นเมนูให้เลือก
REM  หรือรันใน cmd พร้อมคำสั่ง:
REM    foretrade_docker.bat up | logs | down | data | backtest | ui
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "COMPOSE=docker compose -f docker-compose.foretrade.yml"
set "RUN=%COMPOSE% run --rm foretrade"
set "CFG=--config /freqtrade/user_data/config.dry.json"
set "STRAT=--strategy MomentumBreakout"

REM --- ตรวจว่ามี Docker และกำลังทำงานอยู่ ---
docker version >nul 2>&1
if errorlevel 1 (
  echo.
  echo [ERROR] ไม่พบ Docker หรือ Docker ยังไม่ทำงาน
  echo         - ติดตั้ง Docker Desktop: https://www.docker.com/products/docker-desktop/
  echo         - เปิดโปรแกรม Docker Desktop รอจนขึ้นว่า Running แล้วลองใหม่
  echo.
  pause
  exit /b 1
)

set "CMD=%~1"

REM --- ถ้าไม่ได้ส่งคำสั่งมา (เช่นดับเบิลคลิก) ให้ขึ้นเมนู ---
if "%CMD%"=="" (
  echo.
  echo ============= ForeTrade Docker =============
  echo   1^) ui        ติดตั้ง FreqUI ในคอนเทนเนอร์ (ครั้งแรก)
  echo   2^) data      ดาวน์โหลดข้อมูลย้อนหลัง 90 วัน
  echo   3^) backtest  ทดสอบกลยุทธ์
  echo   4^) up        รัน dry-run + เปิด FreqUI
  echo   5^) logs      ดู log สด
  echo   6^) down      หยุดบอท
  echo ===========================================
  set /p "SEL=พิมพ์เลข 1-6 แล้วกด Enter: "
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
echo ไม่รู้จักคำสั่ง "%CMD%" — เลือก up ^| logs ^| down ^| data ^| backtest ^| ui
echo.
pause
exit /b 1

:up
echo -^> เริ่ม ForeTrade (dry-run) เบื้องหลัง...
%COMPOSE% up -d
echo.
echo    FreqUI: http://127.0.0.1:8080  (login ตาม config.dry.json)
echo    ดู log:  foretrade_docker.bat logs
echo.
pause
goto :eof

:logs
echo -^> ดู log สด (Ctrl+C เพื่อออก)
%COMPOSE% logs -f
goto :eof

:down
%COMPOSE% down
echo.
pause
goto :eof

:ui
echo -^> ติดตั้ง FreqUI ในคอนเทนเนอร์...
%RUN% install-ui
echo.
pause
goto :eof

:data
echo -^> ดาวน์โหลดข้อมูล 90 วัน (5m)...
%RUN% download-data %CFG% --days 90 --timeframes 5m
echo.
pause
goto :eof

:backtest
echo -^> backtest MomentumBreakout (90 วัน)...
%RUN% backtesting %CFG% %STRAT% --timerange=-90 --timeframe 5m
echo.
pause
goto :eof
