# 🚀 Quick Start Guide - Vision Django App

## ✅ EASIEST METHOD: Double-Click to Run

1. **Go to:** `vision_django_app` folder
2. **Double-click:** `RUN_NOW.bat`
3. **Wait** for server to start (you'll see "Starting development server...")
4. **Open browser:** http://127.0.0.1:8000/

---

## 📝 MANUAL METHOD: PowerShell Commands

### Step 1: Open PowerShell
Press `Win + X` and select "Windows PowerShell" or "Terminal"

### Step 2: Navigate to project folder
```powershell
cd "D:\Sync-Screen(1)\vision_django_app"
```

### Step 3: Run the restart script
```powershell
.\restart_server_fixed.ps1
```

**OR** manually run these commands:

```powershell
# Activate Python 3.11 virtual environment
$venv = "C:\Users\arunt\.venvs\vision_django_app311"
& "$venv\Scripts\Activate.ps1"

# Verify mediapipe
python -c "import mediapipe; print('Mediapipe OK')"

# Start server
python manage.py runserver 127.0.0.1:8000
```

---

## 🌐 Access the Application

Once the server starts, open your browser and go to:

**http://127.0.0.1:8000/**

---

## 🔧 Troubleshooting

### Error: "Mediapipe not installed" in webcam feed
**Solution:**
1. Stop the server (Ctrl+C)
2. Hard refresh browser: `Ctrl + Shift + R`
3. Restart server using `RUN_NOW.bat`

### Error: "Port 8000 already in use"
**Solution:**
```powershell
# Find and stop process using port 8000
netstat -ano | findstr :8000
# Then kill the process ID (replace PID with actual number)
taskkill /PID <PID> /F
```

### Error: "Execution Policy" in PowerShell
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

---

## ✨ Features Available

- ✅ **Fast Chart Loading** - Charts preload for instant switching
- ✅ **Dark/Light Mode** - Toggle in navbar (moon/sun icon)
- ✅ **Voice Recognition** - Speak letters/numbers during test
- ✅ **PDF/Excel Export** - Export test results

---

## 🛑 To Stop the Server

Press `Ctrl + C` in the terminal window

