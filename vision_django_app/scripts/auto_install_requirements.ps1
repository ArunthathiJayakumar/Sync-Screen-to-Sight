<#
Auto-install requirements for the Vision Django demo
Usage:
  # Lightweight install (UI + doc processing, no mediapipe/TF)
  .\scripts\auto_install_requirements.ps1

  # Full install (heavy packages including mediapipe, TensorFlow)
  .\scripts\auto_install_requirements.ps1 -FullInstall

  # Try to remove existing venv and create a new one for Python 3.11 (safer)
  .\scripts\auto_install_requirements.ps1 -FullInstall -CleanOldVenv

Notes:
- This script tries to find `python` or `py -3.11`. If Python 3.11 is not installed, it will use the current python but warn that mediapipe may not be available for Python >= 3.12+.
- The script creates a new venv named `venv311` to avoid collisions with an existing `venv` that might be used by the system or processes.
- If you want the venv in another directory, pass -VenvName AnotherVenv.
#>
param(
    [switch]$FullInstall,
    [switch]$CleanOldVenv,
    [string]$VenvName = "venv311",
    [string]$PyVersion = "3.11",   # prefer Python 3.11
    [switch]$UseSystemPython    # Use default 'python' instead of py -3.11
)

# Allow process stoppage: prompt user to proceed with venv removal
function ConfirmAndStopPythonProcesses {
    param([switch]$Force)
    Write-Host "Stopping running python processes (if any) and removing old venv may be required." -ForegroundColor Yellow
    if (-not $Force) {
        $choice = Read-Host "Proceed to stop python processes now? (y/N)"
        if ($choice -ne 'y' -and $choice -ne 'Y') { return }
    }
    Get-Process -Name python -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.Id -Force }
    Get-Process -Name python3 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.Id -Force }
}

function RemoveOldVenv {
    param([string]$PathToVenv)
    if (Test-Path $PathToVenv) {
        Write-Host "Attempting to remove $PathToVenv..." -ForegroundColor Yellow
        try {
            Remove-Item -Path $PathToVenv -Recurse -Force -ErrorAction Stop
            Write-Host "Removed old venv at $PathToVenv" -ForegroundColor Green
        } catch {
            Write-Host "Could not remove $PathToVenv - trying rename fallback..." -ForegroundColor Yellow
            try {
                $bak = "${PathToVenv}_bak_$(Get-Date -Format yyyyMMdd_HHmmss)"
                Rename-Item -Path $PathToVenv -NewName $bak -ErrorAction Stop
                Write-Host "Renamed $PathToVenv to $bak" -ForegroundColor Green
            } catch {
                Write-Host "Failed to remove or rename $PathToVenv. You might need to close running Python processes, pause OneDrive, or run PowerShell as Administrator." -ForegroundColor Red
                throw
            }
        }
    }
}

function FindPythonExecutable {
    # Prefer py -3.11, fallback to py -3.10, then to system 'python'
    if (-not $UseSystemPython) {
        $pyCmd = "py -$PyVersion"
        try {
            $v = & $pyCmd --version 2>&1
            if ($LASTEXITCODE -eq 0) { return $pyCmd }
        } catch { }
    }
    # fallback to default 'python'
    try {
        $v = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) { return 'python' }
    } catch { }
    # fallback to py -3.12, 3.10 if present
    foreach ($v in 3..2) { }
    return $null
}

# Main script
Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
$ProjectRoot = (Join-Path $ScriptDir "..") | Resolve-Path
Set-Location $ProjectRoot
$venvPath = Join-Path $ProjectRoot $VenvName

$pythonExec = FindPythonExecutable
if (-not $pythonExec) {
    Write-Host "No python executable could be found. Please install Python 3.11 or provide -UseSystemPython to use the current python." -ForegroundColor Red
    exit 1
}
Write-Host "Using python: $pythonExec" -ForegroundColor Green

if ($CleanOldVenv) {
    ConfirmAndStopPythonProcesses -Force
    RemoveOldVenv -PathToVenv $venvPath
}

# Create venv if not present
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating venv $VenvName using $pythonExec" -ForegroundColor Cyan
    & $pythonExec -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create venv with $pythonExec" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Venv $VenvName already exists; continuing..." -ForegroundColor Yellow
}

# Activate venv
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Host "Activation script not found: $activateScript" -ForegroundColor Red
    exit 1
}
. $activateScript

# Upgrade pip
Write-Host "Upgrading pip, setuptools, wheel..." -ForegroundColor Cyan
python -m pip install --upgrade pip setuptools wheel

# Install requirements
if ($FullInstall) {
    Write-Host "Installing full requirements (this can take a while)..." -ForegroundColor Cyan
    python -m pip install -r requirements.txt
} else {
    Write-Host "Installing lightweight requirements (requirements-lite.txt)..." -ForegroundColor Cyan
    if (-not (Test-Path (Join-Path $ProjectRoot 'requirements-lite.txt'))) {
        Write-Host "requirements-lite.txt not found; creating a minimal one..." -ForegroundColor Yellow
        @"
Django==5.2.8
pillow==12.0.0
reportlab==4.4.4
python-docx==1.2.0
opencv-python==4.12.0.88
numpy==2.1.3
pandas==2.3.3
screen_brightness_control==0.24.3
"@ | Out-File -FilePath (Join-Path $ProjectRoot 'requirements-lite.txt') -Encoding UTF8
    }
    python -m pip install -r requirements-lite.txt
}

# Verify a few packages
Write-Host "Verifying key modules:" -ForegroundColor Cyan
python -c "import importlib,sys; modules=['pandas','cv2','mediapipe','screen_brightness_control']; [print(f'{m}: OK') if importlib.util.find_spec(m) else print(f'{m}: MISSING') for m in modules]"

Write-Host "Done. You can now run the server with:
    .\$VenvName\Scripts\Activate.ps1
    python manage.py runserver
" -ForegroundColor Green
