@echo off
cd /d "%~dp0"
echo ========================================
echo   P2P Global Email System - Tests
echo ========================================
echo.
echo Running unit tests...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found!
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM 运行测试
python "ant coding/p2p/test_p2p_global.py"

if %errorlevel% neq 0 (
    echo.
    echo Tests failed!
    pause
    exit /b 1
)

echo.
echo All tests passed!
pause
