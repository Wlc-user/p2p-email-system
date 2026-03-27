# 智能安全邮箱系统 - PowerShell启动脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  智能安全邮箱系统 - 启动器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python
Write-Host "[*] 检查Python环境..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[!] 未找到Python，请先安装Python" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "[+] Python已安装: $($pythonCmd.Source)" -ForegroundColor Green
Write-Host ""

# 切换到正确的目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# 启动服务器
Write-Host "[*] 正在启动邮箱服务器..." -ForegroundColor Yellow
Write-Host ""
Write-Host "服务器信息:" -ForegroundColor Cyan
Write-Host "  - Domain 1: example1.com (端口 8080)" -ForegroundColor White
Write-Host "  - Domain 2: example2.com (端口 8081)" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

# 启动服务器
python "ant coding/server/main.py"

Write-Host ""
Write-Host "服务器已停止" -ForegroundColor Yellow
pause
