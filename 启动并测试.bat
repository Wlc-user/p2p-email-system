@echo off
chcp 65001 >nul
echo ============================================================
echo 启动双服务器邮件系统
echo ============================================================
echo.

cd /d "e:\pyspace\ant-coding-main"

echo [1/4] 停止旧的服务器进程...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/4] 清理数据库...
if exist "mail_server_a.db" del /f "mail_server_a.db"
if exist "mail_server_b.db" del /f "mail_server_b.db"
timeout /t 1 /nobreak >nul

echo [3/4] 启动服务器A (端口 5001)...
start "Mail Server A" cmd /k "python mail_server.py --domain mail-a.com --port 5001"
timeout /t 3 /nobreak >nul

echo [4/4] 启动服务器B (端口 5002)...
start "Mail Server B" cmd /k "python mail_server.py --domain mail-b.com --port 5002"
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo 服务器已启动!
echo - 服务器A: http://localhost:5001
echo - 服务器B: http://localhost:5002
echo ============================================================
echo.
echo 按任意键开始测试...
pause >nul

echo.
echo [测试] 运行完整测试...
python test_mail_system_fixed.py

echo.
echo 按任意键关闭窗口...
pause >nul
