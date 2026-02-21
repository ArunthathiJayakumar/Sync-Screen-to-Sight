# Vision Django App - Quick Start Script for PowerShell
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Vision Django App - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if virtual environment exists
if (-not (Test-Path -Path "venv311\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv311" -ForegroundColor Yellow
    Write-Host "Then install requirements: pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/3] Activating virtual environment..." -ForegroundColor Green
& .\venv311\Scripts\Activate.ps1

Write-Host "[2/4] Checking for required packages..." -ForegroundColor Green
python -c "import mediapipe; print('Mediapipe: OK')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Mediapipe not found. Installing..." -ForegroundColor Yellow
    pip install mediapipe==0.10.14
}

Write-Host "[3/4] Running database migrations..." -ForegroundColor Green
python manage.py migrate

Write-Host "[4/4] Starting Django development server..." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Server starting at http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop the server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python manage.py runserver

