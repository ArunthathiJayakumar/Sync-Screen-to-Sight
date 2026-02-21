Vision Django Demo
------------------

This is a minimal Django application demonstrating your uploaded eye-chart generator
integrated into a web UI that estimates visual acuity and adjusts uploaded documents.

How to run (on your machine):

1. Create and activate a virtual environment (recommended):
   python -m venv venv
   source venv/bin/activate    (Linux/macOS)
   venv\Scripts\activate     (Windows)

2. Install requirements:
   pip install -r requirements.txt
   # OR use the provided automation script (recommended):
   # - Lightweight (faster, no ML libs):
   #   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   #   .\scripts\setup_and_run.ps1
   # - Full install (installs heavy ML packages):
   #   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   #   .\scripts\setup_and_run.ps1 -FullInstall
   # - Optional: change bind address or port (defaults: 127.0.0.1:8000)
   #   .\scripts\setup_and_run.ps1 -BindAddress 0.0.0.0 -Port 8000

3. Run initial migrations and start server:
   python manage.py migrate
   python manage.py runserver

4. Open http://127.0.0.1:8000 in your browser.

Notes:
- Place any TTF fonts required by charts.py next to charts.py or edit charts.py to use an existing font path.
- Uploaded files and adjusted files are stored under the app's uploads/ directory.
- This is a demo and not a medical device. Do not use it as a prescription.
 
 Video feed and webcam-related features:
 - Webcam & face-distance streaming depends on `mediapipe` and `opencv` to be installed. `mediapipe` is not part of the lightweight install; to enable it, run the script with `-FullInstall` or manually `pip install mediapipe` inside the venv.
 - When `mediapipe` is not installed, the `video_feed` endpoint will show a static message instead of an active webcam stream.
