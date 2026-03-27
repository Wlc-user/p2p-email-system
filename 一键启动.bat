@echo off
chcp 65001 >nul
echo ========================================
echo 智能安全邮箱系统 - 一键启动
echo ========================================
echo.

cd /d "%~dp0"

echo [方式 1] 使用Python脚本（推荐）
echo.
python 启动服务器.py
if %errorlevel% equ 0 (
    echo.
    echo [+] 服务器已启动
    goto :end
)

echo.
echo [方式 2] 使用批处理脚本
echo.
call 测试启动.bat

:end
pause
