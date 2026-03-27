@echo off
chcp 65001 >nul
echo ============================================================
echo 重启服务器并测试
echo ============================================================
echo.

cd /d "e:\pyspace\ant-coding-main"

echo [1/3] 停止旧服务器...
taskkill /F /FI "WINDOWTITLE eq Mail Server*" 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE ne 管理员:*" 2>nul
timeout /t 3 /nobreak >nul

echo [2/3] 清理数据库...
del /F "server_a_data\mail.db" 2>nul
del /F "server_b_data\mail.db" 2>nul
del /F "mail_server_a.db" 2>nul
del /F "mail_server_b.db" 2>nul
timeout /t 1 /nobreak >nul

echo [3/3] 启动新服务器(WAL模式)...
start "Mail Server A" cmd /k "python mail_server.py --db-path server_a_data/mail.db --domain mail-a.com --port 5001"
timeout /t 3 /nobreak >nul

start "Mail Server B" cmd /k "python mail_server.py --db-path server_b_data/mail.db --domain mail-b.com --port 5002"
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo 服务器已启动
echo ============================================================
echo.
echo 按任意键运行测试...
pause >nul

echo.
echo 运行简单测试...
python test_simple.py

echo.
echo 按任意键关闭...
pause >nul
