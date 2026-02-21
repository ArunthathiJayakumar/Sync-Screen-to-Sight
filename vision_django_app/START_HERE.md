# 🚀 START HERE - How to Run the Vision App

## ⚠️ IMPORTANT: You MUST be in the `vision_django_app` folder!

---

## ✅ EASIEST METHOD: Double-Click

1. **Go to:** `vision_django_app` folder
2. **Double-click:** `run_app.bat`
3. **Wait** for server to start
4. **Open browser:** http://127.0.0.1:8000/

---

## 📝 MANUAL METHOD: Copy & Paste These Commands

### Step 1: Open PowerShell
Press `Win + X` and select "Windows PowerShell" or "Terminal"

### Step 2: Navigate to the project folder
```powershell
cd "C:\Users\abhiy\OneDrive\Documents\yazhi\Project\HDA\Sync-Screen(1)\vision_django_app"
```

### Step 3: Activate Virtual Environment
```powershell
.\venv311\Scripts\Activate.ps1
```

**You should see `(venv311)` appear in your prompt!**

### Step 4: Verify Mediapipe (Optional Check)
```powershell
python -c "import mediapipe; print('Mediapipe: OK')"
```

If you see an error, install it:
```powershell
pip install mediapipe==0.10.14
```

### Step 5: Start the Server
```powershell
python manage.py runserver
```

### Step 6: Open Browser
Go to: **http://127.0.0.1:8000/**

---

## 🔧 If You Get Errors

### Error: "Activate.ps1 is not recognized"
**Problem:** You're in the wrong directory!

**Solution:**
```powershell
# Check where you are
pwd

# Navigate to correct folder
cd "C:\Users\abhiy\OneDrive\Documents\yazhi\Project\HDA\Sync-Screen(1)\vision_django_app"

# Try again
.\venv311\Scripts\Activate.ps1
```

### Error: "Execution Policy"
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### Error: "ModuleNotFoundError: No module named 'mediapipe'"
**Solution:**
```powershell
# Make sure virtual environment is activated (see (venv311) in prompt)
pip install mediapipe==0.10.14
```

### Error: "ModuleNotFoundError: No module named 'django'"
**Problem:** Virtual environment not activated!

**Solution:**
```powershell
# Activate virtual environment first
.\venv311\Scripts\Activate.ps1

# Then run server
python manage.py runserver
```

---

## ✅ Quick Verification

Before running, check these:

```powershell
# 1. Check you're in right directory
pwd
# Should show: ...\vision_django_app

# 2. Activate virtual environment
.\venv311\Scripts\Activate.ps1
# Should see: (venv311) in prompt

# 3. Check Django
python -c "import django; print('Django OK')"

# 4. Check Mediapipe
python -c "import mediapipe; print('Mediapipe OK')"
```

---

## 🎯 Complete Command Sequence (Copy All)

```powershell
# Navigate to project
cd "C:\Users\abhiy\OneDrive\Documents\yazhi\Project\HDA\Sync-Screen(1)\vision_django_app"

# Activate virtual environment
.\venv311\Scripts\Activate.ps1

# Verify mediapipe (optional)
python -c "import mediapipe; print('Mediapipe OK')"

# Start server
python manage.py runserver
```

Then open: **http://127.0.0.1:8000/**

---

## 🛑 To Stop the Server

Press `Ctrl + C` in the terminal

---

## 📞 Need Help?

1. Make sure you're in `vision_django_app` folder
2. Make sure virtual environment is activated (see `(venv311)`)
3. Check all errors above and follow solutions

