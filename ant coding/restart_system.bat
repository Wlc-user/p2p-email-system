@echo off
chcp 65001 >nul
cd /d "%~dp0ant coding"

echo ========================================
echo 智能安全邮箱系统 - 重启
echo ========================================
echo.

echo [1/3] 停止现有服务器...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080 :8081 :50051 :50052 :8443 :8444"') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo [+] 已停止现有服务器
echo.

timeout /t 1 /nobreak >nul

echo [2/3] 启动Socket服务器...
start "MailServer-Socket" python server/main.py
echo [+] Socket服务器已启动 (端口 8080/8081)
echo.

timeout /t 2 /nobreak >nul

echo [3/3] 检查服务器状态...
echo.
echo ========================================
echo 服务器已重启!
echo ========================================
echo.
echo Socket服务器:
echo   Domain 1: http://localhost:8080 (example1.com)
echo   Domain 2: http://localhost:8081 (example2.com)
echo.
echo 按任意键打开启动菜单...
pause >nul

python start_system.py
