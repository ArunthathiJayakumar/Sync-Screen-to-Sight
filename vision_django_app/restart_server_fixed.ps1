# Restart Django Server with Correct Python 3.11 Environment
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Restarting Django Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop any existing Python processes
Write-Host "[1/4] Stopping existing servers..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Navigate to project directory
$projectDir = "D:\Sync-Screen(1)\vision_django_app"
cd $projectDir

# Use Python 3.11 virtual environment
$venv = "C:\Users\arunt\.venvs\vision_django_app311"

Write-Host "[2/4] Verifying Python environment..." -ForegroundColor Green
& "$venv\Scripts\python.exe" --version

Write-Host "[3/4] Testing Mediapipe..." -ForegroundColor Green
& "$venv\Scripts\python.exe" -c "import mediapipe as mp; print('Mediapipe version:', mp.__version__); from visionapp.distance_calculator import DistanceCalculator; dc = DistanceCalculator(); print('FaceDetection available:', dc.face_detection is not None)"

Write-Host "[4/4] Starting Django server..." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Server starting at http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop the server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

& "$venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000

