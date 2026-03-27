@echo off
chcp 65001 >nul
echo ========================================
echo   P2P邮件系统 - 停止服务
echo ========================================
echo.

echo 停止Python进程...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

timeout /t 2 /nobreak >nul

echo 清理端口...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8102') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ✓ 所有服务已停止
echo.
pause
