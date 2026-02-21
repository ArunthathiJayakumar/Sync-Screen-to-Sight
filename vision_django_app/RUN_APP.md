# How to Run the Vision Django Application

## Quick Start (Using Existing Virtual Environment)

### Step 1: Open PowerShell or Command Prompt
Navigate to the `vision_django_app` directory:
```powershell
cd "C:\Users\abhiy\OneDrive\Documents\yazhi\Project\HDA\Sync-Screen(1)\vision_django_app"
```

### Step 2: Activate Virtual Environment
**For PowerShell:**
```powershell
.\venv311\Scripts\Activate.ps1
```

**For Command Prompt (CMD):**
```cmd
venv311\Scripts\activate.bat
```

### Step 3: Run the Server
```powershell
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

---

## Alternative: Using the Setup Script

If you need to install dependencies first:

### For PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\scripts\setup_and_run.ps1
```

### For Full Installation (with all ML libraries):
```powershell
.\scripts\setup_and_run.ps1 -FullInstall
```

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'django'"
**Solution:** Make sure you've activated the virtual environment before running the server.

### Error: "Activate.ps1 cannot be loaded"
**Solution:** Run this command first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### If Virtual Environment Doesn't Have Django:
1. Activate the virtual environment
2. Install requirements:
   ```powershell
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```powershell
   python manage.py migrate
   ```
4. Start server:
   ```powershell
   python manage.py runserver
   ```

### Error: "Mediapipe not installed" in Eye-to-Screen section
**Solution:** Install mediapipe package:
```powershell
# Activate virtual environment first
.\venv311\Scripts\Activate.ps1

# Install mediapipe
pip install mediapipe==0.10.14
```

Or install all requirements:
```powershell
pip install -r requirements.txt
```

---

## Access the Application

Once the server is running:
- Open your browser and go to: `http://127.0.0.1:8000/`
- Sign up for a new account or sign in with existing credentials
- Complete the vision test or upload documents if you have previous test data

---

## Stop the Server

Press `Ctrl+C` in the terminal to stop the development server.

