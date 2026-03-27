@echo off
cd /d "%~dp0"
echo ========================================
echo   P2P Global Email System
echo ========================================
echo.
echo Starting P2P Email System...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found!
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM 运行邮箱演示
python "ant coding/p2p/p2p_global.py" email

if %errorlevel% neq 0 (
    echo.
    echo Error occurred while running P2P system
    pause
    exit /b 1
)

echo.
echo P2P Email System stopped
pause
