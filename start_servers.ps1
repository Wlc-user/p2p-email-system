# Mail System Startup Script (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Mail System Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found" -ForegroundColor Red
    pause
    exit 1
}

# Check dependencies
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow

$modules = @("flask", "flask_cors", "cryptography", "requests")
$missing = @()

foreach ($module in $modules) {
    $result = pip show $module 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missing += $module
    }
}

if ($missing.Count -gt 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install $missing
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[OK] All dependencies installed" -ForegroundColor Green
}

# Create data directories
Write-Host ""
if (-not (Test-Path "server_a_data")) {
    New-Item -ItemType Directory -Path "server_a_data" | Out-Null
}
if (-not (Test-Path "server_b_data")) {
    New-Item -ItemType Directory -Path "server_b_data" | Out-Null
}

Write-Host ""
Write-Host "Starting dual servers..." -ForegroundColor Yellow
Write-Host ""

# Start Server A
Write-Host "Starting Server A (mail-a.com:5001)..." -ForegroundColor Cyan
$processA = Start-Process -FilePath "python" -ArgumentList "mail_server.py --db-path server_a_data/mail.db --domain mail-a.com --port 5001" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Server B
Write-Host "Starting Server B (mail-b.com:5002)..." -ForegroundColor Cyan
$processB = Start-Process -FilePath "python" -ArgumentList "mail_server.py --db-path server_b_data/mail.db --domain mail-b.com --port 5002" -PassThru -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] Dual servers started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Server A: http://localhost:5001" -ForegroundColor White
Write-Host "  Domain: mail-a.com" -ForegroundColor Gray
Write-Host "  Database: server_a_data/mail.db" -ForegroundColor Gray
Write-Host ""
Write-Host "Server B: http://localhost:5002" -ForegroundColor White
Write-Host "  Domain: mail-b.com" -ForegroundColor Gray
Write-Host "  Database: server_b_data/mail.db" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Test Commands:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Run full test:" -ForegroundColor White
Write-Host "   python test_mail_system.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Health check:" -ForegroundColor White
Write-Host "   curl http://localhost:5001/api/health" -ForegroundColor Gray
Write-Host "   curl http://localhost:5002/api/health" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Stop all servers:" -ForegroundColor White
Write-Host "   taskkill /F /IM python.exe" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Press Enter to close this window (servers will continue running)..." -ForegroundColor Yellow
Read-Host
