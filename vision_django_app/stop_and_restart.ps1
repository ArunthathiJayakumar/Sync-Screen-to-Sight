# Stop All Python Processes and Restart Server Correctly
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Stopping All Python Processes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop all Python processes
Write-Host "Stopping all Python processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "All Python processes stopped." -ForegroundColor Green
Write-Host ""

# Change to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if virtual environment exists
if (-not (Test-Path -Path "venv311\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Starting Server with Correct Environment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/5] Activating virtual environment..." -ForegroundColor Green
& .\venv311\Scripts\Activate.ps1

Write-Host "[2/5] Verifying Python path..." -ForegroundColor Green
$pythonPath = python -c "import sys; print(sys.executable)" 2>$null
Write-Host "Using Python: $pythonPath" -ForegroundColor Yellow

if ($pythonPath -notlike "*venv311*") {
    Write-Host "WARNING: Not using virtual environment Python!" -ForegroundColor Red
    Write-Host "Please activate manually: .\venv311\Scripts\Activate.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "[3/5] Checking Django..." -ForegroundColor Green
python -c "import django; print('Django:', django.get_version())" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Django not found!" -ForegroundColor Red
    exit 1
}

Write-Host "[4/5] Checking Mediapipe..." -ForegroundColor Green
python -c "import mediapipe; print('Mediapipe:', mediapipe.__version__)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Mediapipe not found! Installing..." -ForegroundColor Yellow
    pip install mediapipe==0.10.14
} else {
    Write-Host "Mediapipe: OK" -ForegroundColor Green
}

Write-Host "[5/5] Testing DistanceCalculator..." -ForegroundColor Green
python -c "from visionapp.distance_calculator import DistanceCalculator; dc = DistanceCalculator(); result = 'OK' if dc.face_detection is not None else 'FAIL'; print('Face Detection:', result)" 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Starting Django Server" -ForegroundColor Cyan
Write-Host "   URL: http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python manage.py runserver

