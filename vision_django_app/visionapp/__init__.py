# Auto-install mediapipe on app startup
import sys

def ensure_mediapipe_installed():
    """Ensure mediapipe is installed when the app starts"""
    try:
        import mediapipe
        version = getattr(mediapipe, '__version__', 'unknown')
        print(f'[VISIONAPP] Mediapipe is already installed (version: {version})')
    except ImportError:
        print('[VISIONAPP] Warning: Mediapipe not found. Please install it manually using: pip install mediapipe==0.10.5')

# Run on app startup
ensure_mediapipe_installed()
