@echo off
echo ========================================
echo   Vision Django App - Quick Start
echo ========================================
echo.

REM Change to the script's directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv311\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv311
    echo Then install requirements: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
call venv311\Scripts\activate.bat

echo [2/4] Checking for required packages...
python -c "import mediapipe; print('Mediapipe: OK')" 2>nul
if errorlevel 1 (
    echo Mediapipe not found. Installing...
    pip install mediapipe==0.10.32
)

echo [3/4] Running database migrations...
python manage.py migrate

echo [4/4] Starting Django development server...
echo.
echo ========================================
echo   Server starting at http://127.0.0.1:8000/
echo   Press Ctrl+C to stop the server
echo ========================================
echo.

python manage.py runserver

pause

