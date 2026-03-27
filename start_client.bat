@echo off
chcp 65001 > nul
echo ========================================
echo 启动客户端测试界面
echo ========================================
echo.

cd p2p-mail-app

echo 正在启动前端...
call npm run dev

echo.
echo 客户端已停止
pause
