@echo off
REM Docker启动脚本 - 智能安全邮箱系统

echo ============================================================
echo    Smart Secure Email System - Docker Startup
echo ============================================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker is not installed or not running
    echo [!] Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [+] Docker is available
echo.

REM 停止已存在的容器
echo [+] Stopping existing containers...
docker-compose -f docker-compose-simple.yml down 2>nul

REM 构建镜像
echo [+] Building Docker images...
docker-compose -f docker-compose-simple.yml build

if %errorlevel% neq 0 (
    echo [!] Failed to build Docker images
    pause
    exit /b 1
)

echo.
echo [+] Starting services...
docker-compose -f docker-compose-simple.yml up -d

if %errorlevel% neq 0 (
    echo [!] Failed to start services
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [+] Services started successfully!
echo ============================================================
echo.
echo Server Information:
echo   - Domain 1 (example1.com): http://localhost:8080
echo   - Domain 2 (example2.com): http://localhost:8081
echo.
echo Commands:
echo   - View logs: docker-compose -f docker-compose-simple.yml logs -f
echo   - Stop services: docker-compose -f docker-compose-simple.yml down
echo   - Restart: docker-compose -f docker-compose-simple.yml restart
echo.
echo Press any key to view logs...
pause >nul

docker-compose -f docker-compose-simple.yml logs -f
