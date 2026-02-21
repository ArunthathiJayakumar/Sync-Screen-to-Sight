from django.apps import AppConfig
import subprocess
import sys

class VisionappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'visionapp'

    def ready(self):
        """Ensure mediapipe is installed when Django app is ready"""
        try:
            import mediapipe
            print('[VISIONAPP] Mediapipe is installed')
        except ImportError:
            print('[VISIONAPP] Mediapipe not found. Auto-installing mediapipe==0.10.14...')
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'mediapipe==0.10.14', '-q'])
                print('[VISIONAPP] Mediapipe installed successfully!')
            except Exception as e:
                print(f'[VISIONAPP] Warning: Failed to auto-install mediapipe: {e}')
