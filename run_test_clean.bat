@echo off
chcp 65001 >nul
echo ============================================================
echo 邮箱系统 - 清理数据库并运行测试
echo ============================================================
echo.

echo [1/3] 清理数据库...
python clean_databases.py
echo.

echo [2/3] 启动服务器A...
start "Mail Server A" cmd /k "python mail_server.py --db-path server_a_data/mail.db --domain mail-a.com --port 5001"
timeout /t 2 /nobreak >nul

echo [3/3] 启动服务器B...
start "Mail Server B" cmd /k "python mail_server.py --db-path server_b_data/mail.db --domain mail-b.com --port 5002"
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo 等待服务器启动...
timeout /t 5 /nobreak >nul

echo ============================================================
echo 运行测试...
echo ============================================================
python test_mail_system.py

echo.
echo ============================================================
echo 测试完成!
echo ============================================================
echo.
echo 按任意键关闭此窗口...
pause >nul
