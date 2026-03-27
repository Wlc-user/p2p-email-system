@echo off
chcp 65001 >nul
cd /d "%~dp0p2p-mail-app"

echo ========================================
echo   P2P SecureMail - 桌面应用
echo ========================================
echo.

REM 检查Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未安装 Node.js
    echo.
    echo 请先安装 Node.js: https://nodejs.org/
    echo 推荐版本: v18.x 或 v20.x
    pause
    exit /b 1
)

echo [1/3] 安装依赖...
call npm install
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [OK] 依赖安装完成
echo.

echo [2/3] 准备Python后端...
if not exist "..\ant coding\p2p\p2p_global.py" (
    echo [警告] P2P Global核心模块不存在
    echo 请先检查后端配置...
)
echo [OK] 后端准备完成
echo.

echo [3/3] 启动应用...
echo.
echo ========================================
echo   应用启动中...
echo   热重载已启用
echo   修改代码后自动刷新
echo ========================================
echo.

call npm run dev

pause
