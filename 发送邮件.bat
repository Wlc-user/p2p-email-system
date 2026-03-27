@echo off
cd /d "%~dp0"
echo ========================================
echo   P2P 邮件系统
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found!
    pause
    exit /b 1
)

python send_mail.py

pause
