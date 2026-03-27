# Fix npm installation

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Fix npm dependencies" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to project directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptPath\p2p-mail-app"
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Delete node_modules
Write-Host "[1/3] Cleaning old files..." -ForegroundColor Green
if (Test-Path node_modules) {
    Write-Host "Deleting node_modules..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force node_modules
}
if (Test-Path package-lock.json) {
    Write-Host "Deleting package-lock.json..." -ForegroundColor Yellow
    Remove-Item -Force package-lock.json
}
Write-Host "[OK] Cleanup complete" -ForegroundColor Green
Write-Host ""

# Set environment variables
Write-Host "[2/3] Configuring mirror..." -ForegroundColor Green
$env:ELECTRON_MIRROR = 'https://npmmirror.com/mirrors/electron/'
Write-Host "ELECTRON_MIRROR = $env:ELECTRON_MIRROR" -ForegroundColor Yellow
Write-Host ""

# Install dependencies
Write-Host "[3/3] Installing dependencies..." -ForegroundColor Green
Write-Host "Using npm mirror, this may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

npm install --registry=https://registry.npmmirror.com

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Installation successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Now run: .\一键启动完整版.bat" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  Installation failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check network connection or try again" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"
