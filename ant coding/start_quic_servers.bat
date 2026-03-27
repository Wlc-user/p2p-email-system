@echo off
chcp 65001 >nul
cd /d "%~dp0ant coding"

echo ========================================
echo 启动 QUIC 邮件服务器
echo ========================================
echo.

echo [警告] QUIC在Windows上可能需要额外配置
echo 推荐在Linux/macOS上运行
echo.

echo [1/2] 启动 Domain 1 服务器 (端口 8443)
start "QUIC-Server-1" python quic/quic_server.py config/domain1_config.json example1.com 8443

timeout /t 2 /nobreak >nul

echo [2/2] 启动 Domain 2 服务器 (端口 8444)
start "QUIC-Server-2" python quic/quic_server.py config/domain2_config.json example2.com 8444

echo.
echo ========================================
echo QUIC 服务器已启动!
echo ========================================
echo Domain 1: localhost:8443 (example1.com)
echo Domain 2: localhost:8444 (example2.com)
echo.
echo 按任意键启动客户端测试...
pause >nul

python quic/quic_client.py

pause
