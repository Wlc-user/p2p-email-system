@echo off
chcp 65001 >nul
echo ========================================
echo   API验证工具
echo ========================================
echo.

echo [测试] 检查后端服务状态...
curl -s http://localhost:8102/api/health 2>nul
if %errorlevel% equ 0 (
    echo [OK] 后端服务运行正常
) else (
    echo [错误] 后端服务未响应
    echo.
    echo 请先启动后端服务:
    echo   方法1: 运行 "启动系统.bat"
    echo   方法2: 手动运行 python p2p_global.py api
    echo.
    pause
    exit /b 1
)
echo.

echo [测试] 获取完整API信息...
curl -s http://localhost:8102/api/health
echo.
echo.

echo [测试] 检查收件箱...
curl -s http://localhost:8102/api/inbox
echo.
echo.

echo [测试] 检查已发送...
curl -s http://localhost:8102/api/sent
echo.
echo.

echo [测试] 检查联系人...
curl -s http://localhost:8102/api/contacts
echo.
echo.

echo ========================================
echo   验证完成
echo ========================================
echo.
echo 如果所有测试都返回JSON数据，说明API正常
echo.
echo 现在可以打开浏览器访问:
echo   http://localhost:5173
echo.
pause
