# Scripts for setting up and running the Vision Django demo

Files included in `scripts/`:

- `setup_and_run.ps1` - PowerShell script that:
  - creates a virtual environment `venv` if not present, and activates it
  - upgrades pip, setuptools, and wheel
  - installs dependencies (lightweight or full via -FullInstall switch)
  - runs database migrations
  - starts the Django development server

Usage examples (PowerShell):

1. Prepare PowerShell to run scripts (temporary session setting):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

2. Run the default (lightweight) install, migrations, and server:

```powershell
cd .\vision_django_app
.\scripts\setup_and_run.ps1
```

3. Run the full install (heavy ML packages like `tensorflow`, `mediapipe`):

```powershell
  cd .\vision_django_app
  .\scripts\setup_and_run.ps1 -FullInstall
```

Notes:
- The default (`-FullInstall` omitted) installs the small `requirements-lite.txt` which supports web UI and document adjustments.
- The full install downloads heavy packages and may require a good network connection, disk space, and appropriate python environment (64-bit Python).
- If you want to customize your Python path, prepend commands with the absolute python command or run `py -3.x` where x is your installed minor version.
- If you see DLL, build or package errors for packages like TensorFlow or MediaPipe on Windows, follow the package-specific installation guidance (GPU dependencies, Visual C++ build tools, etc.).
 - If you previously ran the script and saw an error like "Cannot overwrite variable Host because it is read-only or constant", this was due to the original script using the PowerShell built-in variable `$Host` as a parameter name. The script now uses `-BindAddress` instead to avoid collisions.
 - You can change the bind address and port of the server via these optional parameters:
   - `-BindAddress` - address to bind the server to (default: `127.0.0.1`)
   - `-Port` - port number for the Django server (default: `8000`)

 Example (bind on all interfaces, default port):
 ```powershell
 .\scripts\setup_and_run.ps1 -BindAddress 0.0.0.0
 ```

Optional packages and behavior:
- `screen_brightness_control` is included in the lightweight requirements now; the app will attempt to change screen brightness if available. If you prefer not to install it or the package fails on your platform, the app will skip brightness changes (the module is now tolerant of the missing dependency).
 - `mediapipe` (and other heavy ML packages) are only installed by using `-FullInstall`. If you do not install `mediapipe`, the app will still start but the `video_feed` feature will display a static message indicating mediapipe is not installed.
 - `pandas` is included in `requirements-lite.txt` to support CSV calibration loading with the lightweight install.
