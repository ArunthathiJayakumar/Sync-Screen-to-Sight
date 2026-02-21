<#
PowerShell automation to set up and run the Vision Django demo.
Usage:
  - Basic (lite install):
      Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
      .\scripts\setup_and_run.ps1

  - Full install (including heavy ML libs):
      Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
      .\scripts\setup_and_run.ps1 -FullInstall
#>
param(
    [switch]$FullInstall,
    [string]$BindAddress = "127.0.0.1",
    [string]$Port = "8000"
)

function Write-Log {
    param([string]$Message)
    Write-Host "[setup_and_run] $Message"
}

# Work from the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
$projectRoot = (Join-Path $scriptDir "..") | Resolve-Path
Set-Location $projectRoot

# Create virtualenv
if (-not (Test-Path -Path .\venv)) {
    Write-Log "Creating virtual environment 'venv'..."
    python -m venv venv
} else {
    Write-Log "Virtual environment 'venv' already exists." 
}

# Activate environment for the rest of the script
Write-Log "Activating virtual environment..."
. .\venv\Scripts\Activate.ps1

# Upgrade installer utils
Write-Log "Upgrading pip, setuptools and wheel..."
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
if ($FullInstall) {
    Write-Log "Performing full install (heavy packages) from requirements.txt"
    pip install -r requirements.txt
} else {
    Write-Log "Performing lightweight install from requirements-lite.txt"
    if (-not (Test-Path -Path .\requirements-lite.txt)) {
        Write-Log "requirements-lite.txt not found; creating a default minimal file..."
        @"
Django==5.2.8
pillow==12.0.0
reportlab==4.4.4
python-docx==1.2.0
opencv-python==4.12.0.88
numpy==2.1.3
"@ | Out-File -FilePath .\requirements-lite.txt -Encoding UTF8
    }
    pip install -r requirements-lite.txt
}

# Run migrations
Write-Log "Running migrations..."
python manage.py migrate

# Optionally create an admin user
Write-Log "If you don't have a superuser, run 'python manage.py createsuperuser' separately or answer the prompt when requested."

# Quick check to report whether important optional modules are installed
Write-Log "Verifying optional modules: pandas, cv2, mediapipe, screen_brightness_control"
python -c "import importlib, sys; modules=['pandas','cv2','mediapipe','screen_brightness_control']; [print(f'{m}: OK') if importlib.util.find_spec(m) else print(f'{m}: MISSING') for m in modules]"

# Start the Django dev server
Write-Log "Starting Django development server (press Ctrl+C to stop)..."
python manage.py runserver "$BindAddress`:$Port"

# Quick check to report whether important optional modules are installed
Write-Log "Verifying optional modules: pandas, cv2, mediapipe, screen_brightness_control"
python -c "import importlib, sys; modules=['pandas','cv2','mediapipe','screen_brightness_control']; [print(f'{m}: OK') if importlib.util.find_spec(m) else print(f'{m}: MISSING') for m in modules]"
