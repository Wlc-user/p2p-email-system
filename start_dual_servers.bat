@echo off
chcp 65001 > nul
echo ========================================
echo 启动双域名邮件系统
echo ========================================
echo.

REM 创建数据目录
if not exist "server_a_data" mkdir server_a_data
if not exist "server_b_data" mkdir server_b_data

echo 正在启动服务器 A (mail-a.com:5001)...
start "Mail Server A" python mail_server.py ^
  --db-path server_a_data/mail.db ^
  --domain mail-a.com ^
  --port 5001

timeout /t 2 /nobreak > nul

echo 正在启动服务器 B (mail-b.com:5002)...
start "Mail Server B" python mail_server.py ^
  --db-path server_b_data/mail.db ^
  --domain mail-b.com ^
  --port 5002

echo.
echo ========================================
echo 双服务器已启动!
echo ========================================
echo 服务器 A: http://localhost:5001 (mail-a.com)
echo 服务器 B: http://localhost:5002 (mail-b.com)
echo ========================================
echo.
echo 按任意键关闭所有服务器...
pause > nul

echo.
echo 正在关闭服务器...
taskkill /FI "WINDOWTITLE eq Mail Server A*" > nul 2>&1
taskkill /FI "WINDOWTITLE eq Mail Server B*" > nul 2>&1
echo 服务器已关闭
timeout /t 2 /nobreak > nul
