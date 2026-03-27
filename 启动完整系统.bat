@echo off
chcp 65001 >nul
echo ========================================
echo P2P邮件系统 - 完整启动
echo ========================================
echo.

echo [1/3] 启动中继服务器...
start "Relay Server" cmd /k "cd /d "%~dp0ant coding\p2p" && python relay_server.py"

echo.
timeout /t 3 /nobreak >nul

echo [2/3] 启动P2P节点A (端口8000)...
start "P2P Node A" cmd /k "cd /d "%~dp0ant coding\p2p" && set NODE_ID=user_a@localhost && set PORT=8000 && python p2p_global.py api"

echo.
timeout /t 3 /nobreak >nul

echo [3/3] 启动前端开发服务器...
start "Frontend" cmd /k "cd /d "%~dp0p2p-mail-app" && npm run dev"

echo.
echo ========================================
echo 所有服务已启动！
echo ========================================
echo.
echo 中继服务器: http://localhost:9000
echo P2P节点API: http://localhost:8102
echo 前端界面:    http://localhost:5173
echo.
echo 如需测试多节点通信:
echo   1. 在新终端运行: cd "ant coding\p2p" && set NODE_ID=user_b@localhost && set PORT=8001 && python p2p_global.py api
echo.
echo 按任意键关闭此窗口（服务将继续运行）...
pause >nul
