# ISDP Institutional Local Setup Script (Windows PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "ISDP Campus: Local Institutional Installer" -ForegroundColor Cyan
Write-Host "RC Patel Educational Trust's IMRD Shirpur" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Prerequisites
Write-Host "`n[1/4] Verifying local runtimes..." -ForegroundColor Yellow
$pythonVer = python --version 2>&1
$nodeVer = node --version 2>&1
$npmVer = npm --version 2>&1

Write-Host "  Python : $pythonVer"
Write-Host "  NodeJS : $nodeVer"
Write-Host "  NPM    : $npmVer"

# 2. Setup Local Storage Directories
Write-Host "`n[2/4] Initializing local storage paths..." -ForegroundColor Yellow
$storageRoot = "./local_storage"
$dirs = @("assignments", "submissions", "resources", "backups", "temp", "logs")
foreach ($d in $dirs) {
    $target = Join-Path $storageRoot $d
    if (-not (Test-Path $target)) {
        New-Item -ItemType Directory -Path $target -Force | Out-Null
        Write-Host "  Created: $target" -ForegroundColor Green
    }
}

# 3. Install Python Dependencies
Write-Host "`n[3/4] Installing backend Python packages..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn sqlalchemy aiosqlite pydantic pydantic-settings PyJWT bcrypt email-validator pytest pytest-asyncio httpx

# 4. Install Frontend Dependencies
Write-Host "`n[4/4] Installing frontend packages..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "Installation Complete! Run .\scripts\start.ps1 to launch." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
