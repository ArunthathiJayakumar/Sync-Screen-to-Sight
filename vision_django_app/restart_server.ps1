# Restart Server Script - Ensures correct environment
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Restarting Vision Django Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if virtual environment exists
if (-not (Test-Path -Path "venv311\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    exit 1
}

Write-Host "[1/4] Activating virtual environment..." -ForegroundColor Green
& .\venv311\Scripts\Activate.ps1

Write-Host "[2/4] Verifying Python environment..." -ForegroundColor Green
$pythonPath = python -c "import sys; print(sys.executable)" 2>$null
Write-Host "Python: $pythonPath" -ForegroundColor Yellow

Write-Host "[3/4] Checking Mediapipe installation..." -ForegroundColor Green
python -c "import mediapipe; print('Mediapipe version:', mediapipe.__version__)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Mediapipe not found! Installing..." -ForegroundColor Yellow
    pip install mediapipe==0.10.14
} else {
    Write-Host "Mediapipe: OK" -ForegroundColor Green
}

Write-Host "[4/4] Testing DistanceCalculator..." -ForegroundColor Green
python -c "from visionapp.distance_calculator import DistanceCalculator; dc = DistanceCalculator(); print('Face detection available:', dc.face_detection is not None)" 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Starting Django Server" -ForegroundColor Cyan
Write-Host "   Server: http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python manage.py runserver

