@echo off
chcp 65001 >nul
echo ============================================================
echo 启动前端应用
echo ============================================================
echo.

cd /d "e:\pyspace\ant-coding-main\p2p-mail-app"

echo [1/2] 检查依赖...
if not exist "node_modules" (
    echo 正在安装依赖...
    call npm install
)

echo [2/2] 启动开发服务器...
echo.
echo ============================================================
echo 前端启动中...
echo 访问地址: http://localhost:5173
echo ============================================================
echo.

call npm run dev

pause
