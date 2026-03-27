@echo off
chcp 65001 >nul
cd /d "%~dp0ant coding"

echo ========================================
echo 智能安全邮箱系统 - 立即启动
echo ========================================
echo.

echo [+] 正在启动双域名邮箱服务器...
echo.

python server/main.py

if %errorlevel% neq 0 (
    echo.
    echo [-] 启动失败
    echo.
    echo 可能的原因:
    echo   1. 端口被占用 (8080/8081)
    echo   2. 依赖未安装
    echo   3. 配置文件缺失
    echo.
    echo 请检查错误信息后重试
)

pause
