@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    智能安全邮箱系统 - Docker启动器
echo ========================================
echo.

echo [1] 检查Docker环境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装或未运行
    echo.
    echo 请安装Docker Desktop:
    echo 1. 访问 https://www.docker.com/products/docker-desktop
    echo 2. 下载并安装Docker Desktop
    echo 3. 启动Docker服务
    echo.
    pause
    exit /b 1
)

echo ✅ Docker已安装
echo.

echo [2] 检查Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Docker Compose未安装，使用Docker原生compose
    set USE_NATIVE_COMPOSE=1
) else (
    echo ✅ Docker Compose已安装
    set USE_NATIVE_COMPOSE=0
)

echo.

echo [3] 清理旧的容器和镜像...
echo ⏳ 停止并移除旧容器...
if "!USE_NATIVE_COMPOSE!"=="1" (
    docker compose down >nul 2>&1
) else (
    docker-compose down >nul 2>&1
)

docker rm -f mail-server-1 mail-server-2 >nul 2>&1
docker rmi -f smart-mail-system >nul 2>&1

echo ✅ 清理完成
echo.

echo [4] 创建必要的目录...
mkdir logs >nul 2>&1
mkdir logs\server1 >nul 2>&1
mkdir logs\server2 >nul 2>&1
mkdir data >nul 2>&1
mkdir data\domain1 >nul 2>&1
mkdir data\domain2 >nul 2>&1
mkdir test_reports >nul 2>&1

echo ✅ 目录创建完成
echo.

echo [5] 构建Docker镜像...
echo ⏳ 正在构建镜像，这可能需要几分钟...
if "!USE_NATIVE_COMPOSE!"=="1" (
    docker compose build
) else (
    docker-compose build
)

if errorlevel 1 (
    echo ❌ 镜像构建失败
    echo.
    echo 可能的解决方案:
    echo 1. 检查网络连接
    echo 2. 确保Docker服务正在运行
    echo 3. 检查Dockerfile语法
    pause
    exit /b 1
)

echo ✅ 镜像构建成功
echo.

echo [6] 启动服务...
echo 🚀 启动邮箱服务器...
if "!USE_NATIVE_COMPOSE!"=="1" (
    docker compose up -d
) else (
    docker-compose up -d
)

if errorlevel 1 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)

echo ✅ 服务启动成功
echo.

echo [7] 等待服务就绪...
echo ⏳ 等待服务器启动...
timeout /t 10 /nobreak >nul

echo 📊 服务状态检查:
echo.

echo 📍 邮箱服务器1 (example1.com):
docker exec mail-server-1 python -c "import socket; s = socket.socket(); s.settimeout(2); result = s.connect_ex(('localhost', 8080)); print('✅ 运行正常' if result == 0 else '❌ 未响应')"
echo.

echo 📍 邮箱服务器2 (example2.com):
docker exec mail-server-2 python -c "import socket; s = socket.socket(); s.settimeout(2); result = s.connect_ex(('localhost', 8081)); print('✅ 运行正常' if result == 0 else '❌ 未响应')"
echo.

echo [8] 显示容器状态...
docker ps --filter "name=mail" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

echo ========================================
echo 🎉 系统启动完成！
echo ========================================
echo.
echo 📍 访问地址:
echo    邮箱服务器1: http://localhost:8080
echo    邮箱服务器2: http://localhost:8081
echo.
echo 📍 API端点:
echo    • 健康检查: /api/health
echo    • 用户注册: /api/register
echo    • 发送邮件: /api/mail/send
echo    • 查看收件箱: /api/mail/inbox
echo.
echo 📍 容器管理:
echo    • 查看日志: docker logs mail-server-1
echo    • 进入容器: docker exec -it mail-server-1 bash
echo    • 停止服务: docker-compose down
echo.
echo 🚀 演示功能:
echo    1. 运行动态成本优化演示: 
echo       docker exec mail-server-1 python cost_optimizer/demo_system.py
echo    2. 运行集成测试:
echo       docker exec mail-server-1 python integration_test.py
echo.
echo ⏳ 系统将在30秒后自动打开浏览器...
timeout /t 30 /nobreak >nul

echo.
echo [9] 打开浏览器...
start http://localhost:8080
start http://localhost:8081

echo.
echo [10] 显示使用菜单...
echo.
echo ========================================
echo           🚀 操作菜单
echo ========================================
echo.
echo 请选择操作:
echo   1. 查看服务器日志
echo   2. 运行成本优化演示
echo   3. 运行完整测试
echo   4. 停止服务并退出
echo   5. 继续运行
echo.
set /p menu_choice="选择 (1-5): "

if "!menu_choice!"=="1" (
    echo.
    echo 📋 服务器日志:
    echo [Ctrl+C 退出日志查看]
    timeout /t 2 /nobreak >nul
    docker-compose logs -f
) else if "!menu_choice!"=="2" (
    echo.
    echo 🚀 运行动态成本优化演示...
    docker exec mail-server-1 python cost_optimizer/demo_system.py
    pause
) else if "!menu_choice!"=="3" (
    echo.
    echo 🧪 运行完整测试...
    docker exec mail-server-1 python integration_test.py
    pause
) else if "!menu_choice!"=="4" (
    echo.
    echo 🛑 停止服务...
    if "!USE_NATIVE_COMPOSE!"=="1" (
        docker compose down
    ) else (
        docker-compose down
    )
    echo ✅ 服务已停止
    pause
    exit /b 0
)

echo.
echo ========================================
echo      系统持续运行中...
echo ========================================
echo.
echo 要停止服务，请运行:
echo   docker-compose down
echo.
echo 或按 Ctrl+C 停止批处理文件
echo.

:keep_running
timeout /t 3600 /nobreak >nul
goto keep_running