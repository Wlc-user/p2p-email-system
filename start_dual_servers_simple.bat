@echo off
chcp 65001 > nul
echo ========================================
echo   Mail System - Dual Server Startup
echo ========================================
echo.

REM Check Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not installed
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

REM Check dependencies
echo Checking dependencies...
pip show flask > nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install flask flask-cors cryptography requests
    echo [OK] Dependencies installed
    echo.
) else (
    echo [OK] All dependencies installed
)

REM Create data directories
if not exist "server_a_data" mkdir server_a_data
if not exist "server_b_data" mkdir server_b_data

echo.
echo Starting dual servers...
echo.

REM Start Server A
echo [1/2] Starting Server A (mail-a.com:5001)...
start "Mail Server A" cmd /k "python mail_server.py --db-path server_a_data/mail.db --domain mail-a.com --port 5001"

timeout /t 2 /nobreak > nul

REM Start Server B
echo [2/2] Starting Server B (mail-b.com:5002)...
start "Mail Server B" cmd /k "python mail_server.py --db-path server_b_data/mail.db --domain mail-b.com --port 5002"

timeout /t 2 /nobreak > nul

echo.
echo ========================================
echo [OK] Dual servers started!
echo ========================================
echo.
echo Server A: http://localhost:5001
echo   Domain: mail-a.com
echo   Database: server_a_data/mail.db
echo.
echo Server B: http://localhost:5002
echo   Domain: mail-b.com
echo   Database: server_b_data/mail.db
echo.
echo ========================================
echo Test Commands:
echo ========================================
echo.
echo 1. Run full test:
echo    python test_mail_system.py
echo.
echo 2. Health check:
echo    curl http://localhost:5001/api/health
echo    curl http://localhost:5002/api/health
echo.
echo 3. Stop all servers:
echo    taskkill /F /FI "WINDOWTITLE eq Mail Server*"
echo.
echo ========================================
echo Press any key to close this window...
pause > nul
