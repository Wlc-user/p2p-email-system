@echo off
chcp 65001 >nul
echo ========================================
echo   P2P邮件系统 - 重新启动
echo ========================================
echo.

echo [1/4] 停止所有运行中的进程...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/4] 清理端口占用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8102') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo [3/4] 启动Python P2P Global服务器...
start "P2P Global Server" cmd /k "cd /d "%~dp0ant coding\p2p" && python p2p_global.py api"
timeout /t 3 /nobreak >nul

echo [4/4] 启动Vite开发服务器...
start "Vite Dev Server" cmd /k "cd /d "%~dp0p2p-mail-app" && npm run dev:vite"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   系统启动完成！
echo ========================================
echo.
echo   前端地址: http://localhost:5173
echo   后端API: http://localhost:8102
echo.
echo   按任意键打开浏览器...
pause >nul

start http://localhost:5173

echo.
echo 提示：
echo   - 保持此窗口打开以运行服务
echo   - 关闭此窗口将停止所有服务
echo   - 查看日志信息在各自的CMD窗口中
echo.
pause
