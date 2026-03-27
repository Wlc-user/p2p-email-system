@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 智能安全邮箱系统
echo ========================================
echo.

echo [1] 启动Socket服务器 (端口 8080/8081)
echo [2] 启动gRPC服务器 (端口 50051/50052)
echo [3] 启动流式传输演示
echo [4] 运行Python启动器
echo [0] 退出
echo.
echo ========================================

set /p choice="请选择 (0-4): "

if "%choice%"=="1" (
    cd "ant coding"
    cls
    echo ========================================
    echo 启动Socket服务器
    echo ========================================
    echo.
    python server/main.py
    pause
) else if "%choice%"=="2" (
    cd "ant coding"
    cls
    echo ========================================
    echo 启动gRPC服务器
    echo ========================================
    echo.
    echo 检查gRPC代码...
    if not exist "grpc\mail_service_pb2.py" (
        echo 生成gRPC代码...
        python grpc\generate_grpc.py
    )
    echo.
    echo 启动Domain 1 (端口 50051)...
    start "GRPC-Domain1" python grpc\grpc_server.py config\domain1_config.json example1.com 50051
    timeout /t 2 /nobreak >nul
    echo 启动Domain 2 (端口 50052)...
    start "GRPC-Domain2" python grpc\grpc_server.py config\domain2_config.json example2.com 50052
    echo.
    echo gRPC服务器已启动!
    echo Domain 1: localhost:50051
    echo Domain 2: localhost:50052
    echo.
    pause
) else if "%choice%"=="3" (
    cd "ant coding"
    cls
    echo ========================================
    echo gRPC流式传输演示
    echo ========================================
    echo.
    echo 启动流式服务器...
    start "GRPC-Stream" python grpc\grpc_stream_server.py config\domain1_config.json example1.com 50052
    timeout /t 3 /nobreak >nul
    echo 启动流式客户端...
    echo.
    python grpc\grpc_stream_client.py
    pause
) else if "%choice%"=="4" (
    python launch_system.py
) else if "%choice%"=="0" (
    exit
) else (
    echo 无效选择
    pause
)
