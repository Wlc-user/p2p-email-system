@echo off
chcp 65001 >nul
echo ╔════════════════════════════════════════════════════════╗
echo ║     企业级P2P系统 - 99%+成功率                ║
echo ╚════════════════════════════════════════════════════════╝
echo.

cd "ant coding/p2p"

python quick_start.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败
    echo 请检查:
    echo   1. Python是否安装: python --version
    echo   2. 依赖是否安装: pip install cryptography
    echo.
    pause
)
