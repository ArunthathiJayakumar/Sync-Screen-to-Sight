# Auto-install mediapipe on app startup
import subprocess
import sys

def ensure_mediapipe_installed():
    """Ensure mediapipe is installed when the app starts"""
    try:
        import mediapipe
        print('[VISIONAPP] Mediapipe is already installed')
    except ImportError:
        print('[VISIONAPP] Mediapipe not found. Auto-installing mediapipe==0.10.14...')
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'mediapipe==0.10.14', '-q'])
            print('[VISIONAPP] Mediapipe installed successfully!')
        except Exception as e:
            print(f'[VISIONAPP] Warning: Failed to auto-install mediapipe: {e}')

# Run on app startup
ensure_mediapipe_installed()
