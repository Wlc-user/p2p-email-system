@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   P2P 邮件系统 - 增强演示版
echo   显示详细连接信息和节点位置
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found!
    pause
    exit /b 1
)

python demo_with_details.py

pause
