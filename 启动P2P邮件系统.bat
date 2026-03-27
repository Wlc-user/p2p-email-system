@echo off
chcp 65001 >nul
echo ========================================
echo P2P邮件系统 - 启动脚本
echo ========================================
echo.

echo [1/2] 启动后端API服务器...
start "P2P Backend" cmd /k "cd /d "%~dp0ant coding\p2p" && python p2p_global.py api"

echo.
echo [2/2] 启动前端开发服务器...
timeout /t 3 /nobreak >nul
start "P2P Frontend" cmd /k "cd /d "%~dp0p2p-mail-app" && npm run dev"

echo.
echo ========================================
echo 服务启动完成！
echo ========================================
echo.
echo 后端API: http://localhost:8102
echo 前端界面: http://localhost:5173
echo.
echo 按任意键关闭此窗口（服务将继续运行）...
pause >nul
