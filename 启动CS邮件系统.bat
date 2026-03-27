@echo off
chcp 65001 >nul
echo ========================================
echo CS架构邮件系统 - 启动脚本
echo ========================================
echo.

echo [1/2] 启动邮件服务器...
start "Email Server" cmd /k "cd /d "%~dp0ant coding\p2p" && python email_server_cs.py"

timeout /t 3 /nobreak >nul

echo [2/2] 启动前端开发服务器...
start "Frontend" cmd /k "cd /d "%~dp0p2p-mail-app" && npm run dev"

echo.
echo ========================================
echo 服务启动完成！
echo ========================================
echo.
echo 邮件服务器: http://localhost:5000
echo 前端界面:    http://localhost:5173
echo.
echo ========================================
echo 使用说明:
echo 1. 首次使用需要在"设置"页面注册账号
echo 2. 获取节点ID（40位十六进制）可使用: python -c "import hashlib; print(hashlib.sha256(input().encode()).hexdigest())[:40]"
echo 3. 注册成功后，会返回私钥，请妥善保存！
echo 4. 登录后可以正常使用邮件功能
echo ========================================
echo.
echo 按任意键关闭此窗口（服务将继续运行）...
pause >nul
