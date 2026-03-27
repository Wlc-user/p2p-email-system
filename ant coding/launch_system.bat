@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    智能安全邮箱系统启动器
echo ========================================
echo.

echo [1] 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ Python未安装或不在PATH中
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

echo [2] 安装依赖（如果需要）...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ⚠️  依赖安装失败，尝试继续运行...
) else (
    echo ✅ 依赖安装成功
)

echo.

echo [3] 清理旧的日志文件...
if exist logs rmdir /s /q logs
mkdir logs >nul 2>&1
mkdir logs\example1 >nul 2>&1
mkdir logs\example2 >nul 2>&1

echo.

echo [4] 准备数据目录...
if exist data rmdir /s /q data
mkdir data >nul 2>&1
mkdir data\domain1 >nul 2>&1
mkdir data\domain2 >nul 2>&1

echo ✅ 数据目录准备完成
echo.

echo [5] 启动邮箱服务器...
echo.

echo 🚀 启动 example1.com 服务器 (端口: 8080)...
start "邮箱服务器-1" cmd /k "python server/main.py --domain example1.com --port 8080 --log-level INFO"
timeout /t 3 /nobreak >nul

echo 🚀 启动 example2.com 服务器 (端口: 8081)...
start "邮箱服务器-2" cmd /k "python server/main.py --domain example2.com --port 8081 --log-level INFO"
timeout /t 3 /nobreak >nul

echo.

echo [6] 检查服务器状态...
echo ⏳ 等待服务器启动...
timeout /t 10 /nobreak >nul

echo 📊 服务器状态检查:
echo.

echo 📍 example1.com:
python -c "import socket; s = socket.socket(); s.settimeout(2); result = s.connect_ex(('localhost', 8080)); s.close(); print('✅ 已启动' if result == 0 else '❌ 未响应')"
echo.

echo 📍 example2.com:
python -c "import socket; s = socket.socket(); s.settimeout(2); result = s.connect_ex(('localhost', 8081)); s.close(); print('✅ 已启动' if result == 0 else '❌ 未响应')"
echo.

echo [7] 启动客户端应用...
echo.

echo 🎯 选择要启动的客户端:
echo   1. example1.com 客户端 (用户: alice)
echo   2. example2.com 客户端 (用户: bob)
echo   3. 启动测试客户端
echo   4. 跳过客户端
set /p choice="请选择 (1-4): "

if "%choice%"=="1" (
    echo 🚀 启动 example1.com 客户端...
    start "邮箱客户端-1" cmd /k "python client/main.py --server http://localhost:8080 --user alice"
) else if "%choice%"=="2" (
    echo 🚀 启动 example2.com 客户端...
    start "邮箱客户端-2" cmd /k "python client/main.py --server http://localhost:8081 --user bob"
) else if "%choice%"=="3" (
    echo 🚀 启动测试客户端...
    start "测试客户端" cmd /k "python integration_test.py"
) else (
    echo ⏭️  跳过客户端启动
)

echo.

echo ========================================
echo 🎉 系统启动完成！
echo ========================================
echo.
echo 📍 服务器地址:
echo    example1.com: http://localhost:8080
echo    example2.com: http://localhost:8081
echo.
echo 📍 数据目录:
echo    example1: data\domain1\
echo    example2: data\domain2\
echo.
echo 📍 日志目录:
echo    logs\example1\
echo    logs\example2\
echo.
echo 🚀 后续操作:
echo    1. 打开浏览器访问上述地址查看API文档
echo    2. 查看日志文件监控系统运行
echo    3. 按任意键关闭所有服务器
echo.
pause

echo.
echo [8] 清理进程...
taskkill /F /FI "WINDOWTITLE eq 邮箱服务器-*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq 邮箱客户端-*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq 测试客户端" >nul 2>&1

echo ✅ 系统已关闭
timeout /t 2 /nobreak >nul