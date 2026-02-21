@echo off
echo ========================================
echo   Starting Vision Django App
echo ========================================
echo.

REM Navigate to project directory
cd /d "%~dp0"

REM Use Python 3.11 virtual environment
set VENV=C:\Users\arunt\.venvs\vision_django_app311

echo [1/3] Activating Python 3.11 environment...
call "%VENV%\Scripts\activate.bat"

echo [2/3] Verifying Mediapipe...
python -c "import mediapipe; print('Mediapipe OK')" 2>nul
if errorlevel 1 (
    echo ERROR: Mediapipe not found!
    echo Installing mediapipe...
    pip install mediapipe==0.10.14
)

echo [3/3] Starting Django server...
echo.
echo ========================================
echo   Server will start at http://127.0.0.1:8000/
echo   Press Ctrl+C to stop the server
echo ========================================
echo.

python manage.py runserver 127.0.0.1:8000

pause

