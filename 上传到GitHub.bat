@echo off
chcp 65001 >nul
echo ========================================
echo   GitHub 上传向导
echo ========================================
echo.

cd /d "%~dp0"

REM 检查是否是 git 仓库
if not exist ".git" (
    echo [1/4] 初始化 Git 仓库...
    git init
    echo [OK] Git 仓库初始化完成
    echo.
) else (
    echo [OK] Git 仓库已存在
    echo.
)

REM 添加所有文件
echo [2/4] 添加文件到暂存区...
git add .
echo [OK] 文件已添加
echo.

REM 提交
echo [3/4] 提交更改...
git commit -m "Initial commit: P2P Email System with X25519 + ChaCha20-Poly1305 encryption"
echo [OK] 提交完成
echo.

REM 检查是否有远程仓库
git remote -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [4/4] 请执行以下步骤完成上传:
    echo.
    echo 步骤 1: 在 GitHub 创建新仓库
    echo   - 访问 https://github.com/new
    echo   - 仓库名: p2p-email-system (或自定义)
    echo   - 设置为 Public 或 Private
    echo   - 不要初始化 README (我们已有)
    echo.
    echo 步骤 2: 复制仓库地址 (https 或 ssh)
    echo.
    echo 步骤 3: 运行以下命令:
    echo.
    echo   git remote add origin ^<你的仓库地址^>
    echo   git branch -M main
    echo   git push -u origin main
    echo.
    echo ========================================
    echo 示例:
    echo   git remote add origin https://github.com/你的用户名/p2p-email-system.git
    echo   git branch -M main
    echo   git push -u origin main
    echo ========================================
    echo.
) else (
    echo [4/4] 推送到远程仓库...
    git branch -M main
    git push -u origin main
    echo [OK] 推送完成
    echo.
)

echo 完成!
pause
