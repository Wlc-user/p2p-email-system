@echo off
chcp 65001 > nul
echo ========================================
echo 邮箱系统快速启动脚本
echo ========================================
echo.

REM 检查依赖
python --version > nul 2>&1
if errorlevel 1 (
    echo ✗ Python 未安装
    echo 请先安装 Python 3.8+
    pause
    exit /b 1
)

echo ✓ Python 已安装
echo.

REM 安装依赖
echo 正在检查依赖...
pip show flask > nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install flask flask-cors cryptography requests
    echo ✓ 依赖安装完成
    echo.
)

REM 创建数据目录
if not exist "server_a_data" mkdir server_a_data
if not exist "server_b_data" mkdir server_b_data

echo 正在启动服务器...
echo.

REM 启动服务器 A
start "Mail Server A - mail-a.com:5001" cmd /k "python mail_server.py --db-path server_a_data/mail.db --domain mail-a.com --port 5001"

timeout /t 3 /nobreak > nul

REM 启动服务器 B
start "Mail Server B - mail-b.com:5002" cmd /k "python mail_server.py --db-path server_b_data/mail.db --domain mail-b.com --port 5002"

echo.
echo ========================================
echo ✓ 双服务器已启动!
echo ========================================
echo.
echo 服务器 A: http://localhost:5001
echo   - 域名: mail-a.com
echo   - 数据库: server_a_data/mail.db
echo.
echo 服务器 B: http://localhost:5002
echo   - 域名: mail-b.com
echo   - 数据库: server_b_data/mail.db
echo.
echo ========================================
echo 测试命令:
echo ========================================
echo.
echo 1. 运行完整测试:
echo    python test_mail_system.py
echo.
echo 2. 测试健康检查:
echo    curl http://localhost:5001/api/health
echo    curl http://localhost:5002/api/health
echo.
echo 3. 停止所有服务器:
echo    taskkill /F /FI "WINDOWTITLE eq Mail Server*"
echo.
echo ========================================
echo 按任意键关闭此窗口(服务器继续运行)...
pause > nul
