@echo off
chcp 65001 >nul
cd /d "%~dp0ant coding"

echo ========================================
echo 启动 gRPC 邮件服务器
echo ========================================
echo.

echo [1/2] 启动 Domain 1 服务器 (端口 50051)
start "GRPC-Server-1" python grpc/grpc_server.py config/domain1_config.json example1.com 50051

timeout /t 2 /nobreak >nul

echo [2/2] 启动 Domain 2 服务器 (端口 50052)
start "GRPC-Server-2" python grpc/grpc_server.py config/domain2_config.json example2.com 50052

echo.
echo ========================================
echo gRPC 服务器已启动!
echo ========================================
echo Domain 1: localhost:50051 (example1.com)
echo Domain 2: localhost:50052 (example2.com)
echo.
echo 按任意键启动客户端测试...
pause >nul

python grpc/grpc_client.py

pause
