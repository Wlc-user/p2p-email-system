@echo off
chcp 65001 >nul
cd /d "%~dp0ant coding"

echo ========================================
echo gRPC流式传输演示
echo ========================================
echo.
echo 本演示将展示gRPC的流式传输功能:
echo   1. 实时新邮件推送
echo   2. 实时邮箱状态同步
echo.
echo ========================================
echo.

echo [步骤 1/2] 启动流式服务器...
start "GRPC-Stream-Server" python grpc/grpc_stream_server.py config/domain1_config.json example1.com 50052

timeout /t 3 /nobreak >nul

echo [步骤 2/2] 启动流式客户端...
echo.
python grpc/grpc_stream_client.py

pause
